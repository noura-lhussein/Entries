from __future__ import annotations

from datetime import date
from typing import Any

from django.db import transaction

from .alert_engine import evaluate_alerts
from .facility_utils import get_facility
from .models import (
    DailyProduction,
    DailyReport,
    DataSource,
    Export,
    Field,
    FuelInventory,
    PowerGasRequirement,
    PowerGasSupply,
    ProductionLoss,
    Refinery,
    RefineryDailyOutput,
)
from .snapshot_builder import build_kpi_snapshot


def _get_field(field_code: str) -> Field:
    try:
        return Field.objects.get(code__iexact=field_code.strip())
    except Field.DoesNotExist as exc:
        raise ValueError(f'Unknown field code: {field_code}') from exc


def _get_refinery(refinery_name: str) -> Refinery:
    try:
        return Refinery.objects.get(refinery_name__iexact=refinery_name.strip())
    except Refinery.DoesNotExist as exc:
        raise ValueError(f'Unknown refinery: {refinery_name}') from exc


@transaction.atomic
def upsert_daily_operations(payload: dict[str, Any], *, user=None) -> dict[str, Any]:
    production_date: date = payload['production_date']
    counts = {
        'production': 0,
        'refinery_outputs': 0,
        'inventory': 0,
        'exports': 0,
        'losses': 0,
        'power_gas_supply': 0,
        'power_gas_requirement': 0,
    }

    audit = {'source': DataSource.API, 'updated_by': user}

    for row in payload.get('production', []):
        field = _get_field(row['field_code'])
        DailyProduction.objects.update_or_create(
            field=field,
            production_date=production_date,
            defaults={
                'crude_oil_bbl': row.get('crude_oil_bbl', 0),
                'natural_gas_mmscf': row.get('natural_gas_mmscf', 0),
                'condensate_bbl': row.get('condensate_bbl', 0),
                'water_cut_percent': row.get('water_cut_percent'),
                'operating_hours': row.get('operating_hours'),
                **audit,
            },
        )
        counts['production'] += 1

    for row in payload.get('refinery_outputs', []):
        refinery = _get_refinery(row['refinery_name'])
        RefineryDailyOutput.objects.update_or_create(
            refinery=refinery,
            production_date=production_date,
            defaults={
                'gasoline_ton': row.get('gasoline_ton', 0),
                'diesel_ton': row.get('diesel_ton', 0),
                'fuel_oil_ton': row.get('fuel_oil_ton', 0),
                'lpg_ton': row.get('lpg_ton', 0),
                **audit,
            },
        )
        counts['refinery_outputs'] += 1

    for row in payload.get('inventory', []):
        facility = get_facility(
            code=row.get('facility_code'),
            name=row.get('facility_name'),
        )
        FuelInventory.objects.update_or_create(
            facility=facility,
            inventory_date=production_date,
            fuel_type=row['fuel_type'],
            defaults={
                'current_volume': row.get('current_volume', 0),
                'max_capacity': row.get('max_capacity'),
                **audit,
            },
        )
        counts['inventory'] += 1

    for row in payload.get('exports', []):
        destination = row.get('destination_country', '').strip() or '—'
        export, created = Export.objects.get_or_create(
            export_date=production_date,
            destination_country=destination,
            defaults={
                'crude_bbl': row.get('crude_bbl', 0),
                'revenue_usd': row.get('revenue_usd', 0),
                **audit,
            },
        )
        if not created:
            export.crude_bbl = row.get('crude_bbl', 0)
            export.revenue_usd = row.get('revenue_usd', 0)
            export.source = DataSource.API
            export.updated_by = user
            export.save()
        counts['exports'] += 1

    for row in payload.get('losses', []):
        field = _get_field(row['field_code'])
        ProductionLoss.objects.update_or_create(
            field=field,
            loss_date=production_date,
            loss_type=row['loss_type'],
            defaults={
                'estimated_loss_bbl': row.get('estimated_loss_bbl', 0),
                'reason': row.get('reason', ''),
                'severity': row.get('severity', ''),
            },
        )
        counts['losses'] += 1

    for row in payload.get('power_gas_supply', []):
        facility = get_facility(
            code=row.get('facility_code'),
            name=row.get('facility_name') or row.get('power_station'),
        )
        PowerGasSupply.objects.update_or_create(
            supply_date=production_date,
            facility=facility,
            defaults={'supplied_mmscf': row.get('supplied_mmscf', 0)},
        )
        counts['power_gas_supply'] += 1

    for row in payload.get('power_gas_requirement', []):
        facility = get_facility(
            code=row.get('facility_code'),
            name=row.get('facility_name') or row.get('power_station'),
        )
        PowerGasRequirement.objects.update_or_create(
            requirement_date=production_date,
            facility=facility,
            defaults={'required_mmscf': row.get('required_mmscf', 0)},
        )
        counts['power_gas_requirement'] += 1

    notes_ar = payload.get('notes_ar', '')
    notes_en = payload.get('notes_en', '')
    if notes_ar or notes_en or payload.get('publish'):
        defaults: dict[str, Any] = {}
        if notes_ar:
            defaults['notes_ar'] = notes_ar
        if notes_en:
            defaults['notes_en'] = notes_en
        if payload.get('publish'):
            defaults['status'] = DailyReport.Status.PUBLISHED
        report, created = DailyReport.objects.get_or_create(
            report_date=production_date,
            defaults={**defaults, 'created_by': user},
        )
        if not created:
            for key, value in defaults.items():
                setattr(report, key, value)
            report.save(update_fields=list(defaults.keys()))

    result: dict[str, Any] = {
        'production_date': production_date.isoformat(),
        'counts': counts,
        'published': False,
        'snapshot': None,
    }

    if payload.get('publish'):
        result.update(publish_day(production_date))

    return result


def publish_day(production_date: date) -> dict[str, Any]:
    snapshot = build_kpi_snapshot(production_date)
    evaluate_alerts(production_date, snapshot)
    DailyReport.objects.filter(report_date=production_date).update(
        status=DailyReport.Status.PUBLISHED,
    )
    return {
        'published': True,
        'production_date': production_date.isoformat(),
        'snapshot': {
            'total_oil_production_bpd': float(snapshot.total_oil_production_bpd or 0),
            'total_gas_production_mmscf': float(snapshot.total_gas_production_mmscf or 0),
            'total_export_bbl': float(snapshot.total_export_bbl or 0),
            'export_revenue_usd': float(snapshot.export_revenue_usd or 0),
            'active_alerts_count': snapshot.active_alerts_count,
        },
    }
