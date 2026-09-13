from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Sum

from .models import DailyDemand, DailyGeneration, KpiDailySnapshot, PowerPlant
from .target_resolver import national_targets_for_snapshot


def _sum_generation(snapshot_date: date, field: str) -> Decimal:
    agg = DailyGeneration.objects.filter(report_date=snapshot_date).aggregate(total=Sum(field))
    return agg['total'] or Decimal('0')


def _renewable_share(snapshot_date: date, total_mwh: Decimal) -> Decimal | None:
    if total_mwh == 0:
        return None
    renewable = (
        DailyGeneration.objects.filter(
            report_date=snapshot_date,
            plant__plant_type__in=[PowerPlant.PlantType.HYDRO, PowerPlant.PlantType.SOLAR, PowerPlant.PlantType.WIND],
        ).aggregate(total=Sum('gross_generation_mwh'))['total']
        or Decimal('0')
    )
    return ((renewable / total_mwh) * Decimal('100')).quantize(Decimal('0.1'))


def _plant_availability(snapshot_date: date) -> Decimal | None:
    rows = DailyGeneration.objects.filter(report_date=snapshot_date).select_related('plant')
    total_installed = Decimal('0')
    total_available = Decimal('0')
    for row in rows:
        cap = row.plant.installed_capacity_mw or Decimal('0')
        total_installed += cap
        if row.available_capacity_mw is not None:
            total_available += row.available_capacity_mw
        elif row.plant.status == PowerPlant.Status.ACTIVE:
            total_available += cap
    if total_installed == 0:
        return None
    return ((total_available / total_installed) * Decimal('100')).quantize(Decimal('0.1'))


def _capacity_factor(snapshot_date: date, total_mwh: Decimal) -> Decimal | None:
    installed = PowerPlant.objects.filter(status=PowerPlant.Status.ACTIVE).aggregate(
        total=Sum('installed_capacity_mw'),
    )['total']
    if not installed or installed == 0:
        return None
    # CF = energy / (capacity MW * 24 h)
    max_mwh = Decimal(installed) * Decimal('24')
    if max_mwh == 0:
        return None
    return ((total_mwh / max_mwh) * Decimal('100')).quantize(Decimal('0.1'))


def build_kpi_snapshot(snapshot_date: date, *, persist: bool = True) -> KpiDailySnapshot:
    total_mwh = _sum_generation(snapshot_date, 'gross_generation_mwh')
    peak_gen = DailyGeneration.objects.filter(report_date=snapshot_date).aggregate(
        peak=Sum('peak_mw'),
    )['peak']

    demand = DailyDemand.objects.filter(report_date=snapshot_date).first()
    peak_demand = demand.peak_demand_mw if demand else None

    gap = None
    if peak_demand is not None and peak_gen is not None:
        gap = (peak_demand - peak_gen).quantize(Decimal('0.1'))

    installed = PowerPlant.objects.aggregate(total=Sum('installed_capacity_mw'))['total']
    active_plants = PowerPlant.objects.filter(status=PowerPlant.Status.ACTIVE).count()

    national_targets = national_targets_for_snapshot(snapshot_date)

    snapshot, _ = KpiDailySnapshot.objects.update_or_create(
        snapshot_date=snapshot_date,
        defaults={
            'total_generation_mwh': total_mwh,
            'peak_demand_mw': peak_demand,
            'supply_demand_gap_mw': gap,
            'plant_availability_percent': _plant_availability(snapshot_date),
            'capacity_factor_percent': _capacity_factor(snapshot_date, total_mwh),
            'renewable_share_percent': _renewable_share(snapshot_date, total_mwh),
            'total_installed_mw': installed,
            'active_plants_count': active_plants,
            'target_total_generation_mwh': national_targets.get('total_generation_mwh'),
            'target_peak_demand_mw': national_targets.get('peak_demand_mw'),
            'target_plant_availability_percent': national_targets.get('plant_availability_percent'),
            'source': 'computed',
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
