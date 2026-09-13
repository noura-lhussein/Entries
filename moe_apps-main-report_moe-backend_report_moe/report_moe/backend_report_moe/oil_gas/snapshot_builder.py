from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Sum

from .models import (
    DailyProduction,
    DailyReport,
    Export,
    KpiDailySnapshot,
    PowerGasRequirement,
    PowerGasSupply,
    ProductionLoss,
    RefineryDailyOutput,
)
from .target_resolver import national_targets_for_snapshot


def _sum_production(snapshot_date: date, field: str) -> Decimal:
    agg = DailyProduction.objects.filter(production_date=snapshot_date).aggregate(total=Sum(field))
    return agg['total'] or Decimal('0')


def _legacy_metric_value(snapshot_date: date, metric_key: str) -> Decimal | None:
    report = (
        DailyReport.objects.filter(report_date=snapshot_date, status=DailyReport.Status.PUBLISHED)
        .prefetch_related('metrics')
        .first()
    )
    if not report:
        return None
    row = report.metrics.filter(metric_key=metric_key, dimension='').first()
    return row.value if row else None


def _stock_days(snapshot_date: date, fuel_type: str) -> Decimal | None:
    """Stock coverage days — requires inventory volume; baseline consumption was removed."""
    _ = snapshot_date, fuel_type
    return None


def _gas_supply_percent(snapshot_date: date) -> Decimal | None:
    supplied = PowerGasSupply.objects.filter(supply_date=snapshot_date).aggregate(
        total=Sum('supplied_mmscf'),
    )['total']
    required = PowerGasRequirement.objects.filter(requirement_date=snapshot_date).aggregate(
        total=Sum('required_mmscf'),
    )['total']
    if not supplied or not required or required == 0:
        return None
    return ((supplied / required) * Decimal('100')).quantize(Decimal('0.1'))


def _refinery_utilization(snapshot_date: date) -> Decimal | None:
    outputs = RefineryDailyOutput.objects.filter(production_date=snapshot_date).select_related('refinery')
    total_output_ton = Decimal('0')
    total_capacity_bpd = Decimal('0')
    for row in outputs:
        total_output_ton += (
            row.gasoline_ton + row.diesel_ton + row.fuel_oil_ton + row.lpg_ton
        )
        if row.refinery.design_capacity_bpd:
            total_capacity_bpd += row.refinery.design_capacity_bpd
    if total_capacity_bpd == 0:
        return None
    # Approximate: 1 ton ≈ 7.33 bbl for utilization proxy
    actual_bpd = total_output_ton * Decimal('7.33')
    return ((actual_bpd / total_capacity_bpd) * Decimal('100')).quantize(Decimal('0.1'))


def build_kpi_snapshot(snapshot_date: date, *, persist: bool = True) -> KpiDailySnapshot:
    oil_bbl = _sum_production(snapshot_date, 'crude_oil_bbl')
    gas_mmscf = _sum_production(snapshot_date, 'natural_gas_mmscf')

    if oil_bbl == 0:
        legacy_oil = _legacy_metric_value(snapshot_date, 'crude_transfer_daily_bbl')
        if legacy_oil is not None:
            oil_bbl = legacy_oil * Decimal('100')

    if gas_mmscf == 0:
        legacy_gas = _legacy_metric_value(snapshot_date, 'gas_production_k_m3')
        if legacy_gas is not None:
            gas_mmscf = legacy_gas

    losses = ProductionLoss.objects.filter(loss_date=snapshot_date).aggregate(
        total=Sum('estimated_loss_bbl'),
    )['total'] or Decimal('0')

    export_agg = Export.objects.filter(export_date=snapshot_date).aggregate(
        bbl=Sum('crude_bbl'),
        usd=Sum('revenue_usd'),
    )

    national_targets = national_targets_for_snapshot(snapshot_date)
    target_defaults = {
        'target_total_oil_production_bpd': national_targets.get('total_oil_production_bpd'),
        'target_total_gas_production_mmscf': national_targets.get('total_gas_production_mmscf'),
        'target_total_export_bbl': national_targets.get('total_export_bbl'),
        'target_export_revenue_usd': national_targets.get('export_revenue_usd'),
        'target_gasoline_stock_days': national_targets.get('gasoline_stock_days'),
        'target_gas_supply_to_power_percent': national_targets.get('gas_supply_to_power_percent'),
    }

    snapshot, _ = KpiDailySnapshot.objects.update_or_create(
        snapshot_date=snapshot_date,
        defaults={
            'total_oil_production_bpd': oil_bbl,
            'total_gas_production_mmscf': gas_mmscf,
            'refinery_utilization_percent': _refinery_utilization(snapshot_date),
            'gasoline_stock_days': _stock_days(snapshot_date, 'gasoline'),
            'diesel_stock_days': _stock_days(snapshot_date, 'diesel'),
            'gas_supply_to_power_percent': _gas_supply_percent(snapshot_date),
            'total_export_bbl': export_agg['bbl'] or Decimal('0'),
            'export_revenue_usd': export_agg['usd'] or Decimal('0'),
            'total_losses_bbl': losses,
            'source': 'computed',
            **target_defaults,
        },
    )
    if persist:
        snapshot.save()
    return snapshot


def list_snapshot_dates(limit: int = 90) -> list[str]:
    return [
        d.isoformat()
        for d in KpiDailySnapshot.objects.order_by('-snapshot_date').values_list(
            'snapshot_date',
            flat=True,
        )[:limit]
    ]


def get_snapshot(snapshot_date: date | None) -> KpiDailySnapshot | None:
    if snapshot_date:
        return KpiDailySnapshot.objects.filter(snapshot_date=snapshot_date).first()
    return KpiDailySnapshot.objects.order_by('-snapshot_date').first()


def get_previous_snapshot(snapshot: KpiDailySnapshot) -> KpiDailySnapshot | None:
    return (
        KpiDailySnapshot.objects.filter(snapshot_date__lt=snapshot.snapshot_date)
        .order_by('-snapshot_date')
        .first()
    )


def snapshot_trend(field: str, days: int = 14, end_date: date | None = None) -> list[dict[str, Any]]:
    end = end_date or KpiDailySnapshot.objects.order_by('-snapshot_date').values_list(
        'snapshot_date',
        flat=True,
    ).first()
    if not end:
        return []
    start = end - timedelta(days=days - 1)
    rows = KpiDailySnapshot.objects.filter(
        snapshot_date__gte=start,
        snapshot_date__lte=end,
    ).order_by('snapshot_date')
    return [
        {
            'date': row.snapshot_date.isoformat(),
            'value': float(getattr(row, field) or 0),
        }
        for row in rows
    ]
