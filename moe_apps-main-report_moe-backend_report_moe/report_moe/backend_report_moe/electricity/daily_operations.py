from __future__ import annotations

from datetime import date
from typing import Any

from django.db import transaction

from .alert_engine import evaluate_alerts
from .models import DailyDemand, DailyGeneration, DailyReport, DataSource, GridOutage, PowerPlant
from .snapshot_builder import build_kpi_snapshot


def _get_plant(plant_code: str) -> PowerPlant:
    try:
        return PowerPlant.objects.get(code__iexact=plant_code.strip())
    except PowerPlant.DoesNotExist as exc:
        raise ValueError(f'Unknown plant code: {plant_code}') from exc


@transaction.atomic
def upsert_daily_operations(payload: dict[str, Any], *, user=None) -> dict[str, Any]:
    report_date: date = payload['report_date']
    counts = {'generation': 0, 'demand': 0, 'grid_outages': 0}
    audit = {'source': DataSource.API, 'updated_by': user}

    for row in payload.get('generation', []):
        plant = _get_plant(row['plant_code'])
        DailyGeneration.objects.update_or_create(
            plant=plant,
            report_date=report_date,
            defaults={
                'gross_generation_mwh': row.get('gross_generation_mwh', 0),
                'peak_mw': row.get('peak_mw'),
                'available_capacity_mw': row.get('available_capacity_mw'),
                'forced_outage_mw': row.get('forced_outage_mw'),
                **audit,
            },
        )
        counts['generation'] += 1

    demand = payload.get('demand')
    if demand:
        DailyDemand.objects.update_or_create(
            report_date=report_date,
            defaults={
                'peak_demand_mw': demand.get('peak_demand_mw'),
                'energy_consumed_mwh': demand.get('energy_consumed_mwh'),
                **audit,
            },
        )
        counts['demand'] = 1

    GridOutage.objects.filter(report_date=report_date).delete()
    for row in payload.get('grid_outages', []):
        GridOutage.objects.create(
            report_date=report_date,
            governorate=row.get('governorate', ''),
            outage_type=row.get('outage_type', 'distribution'),
            duration_hours=row.get('duration_hours', 0),
            customers_affected=row.get('customers_affected', 0),
            severity=row.get('severity', ''),
            description=row.get('description', ''),
            **audit,
        )
        counts['grid_outages'] += 1

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
            report_date=report_date,
            defaults={**defaults, 'created_by': user},
        )
        if not created:
            for key, value in defaults.items():
                setattr(report, key, value)
            report.save(update_fields=list(defaults.keys()))

    result: dict[str, Any] = {
        'report_date': report_date.isoformat(),
        'counts': counts,
        'published': False,
        'snapshot': None,
    }

    if payload.get('publish'):
        result.update(publish_day(report_date))

    return result


def publish_day(report_date: date) -> dict[str, Any]:
    snapshot = build_kpi_snapshot(report_date)
    alert_count = evaluate_alerts(report_date, snapshot)
    snapshot.active_alerts_count = alert_count
    snapshot.save(update_fields=['active_alerts_count'])
    DailyReport.objects.filter(report_date=report_date).update(
        status=DailyReport.Status.PUBLISHED,
    )
    return {
        'published': True,
        'report_date': report_date.isoformat(),
        'snapshot': {
            'total_generation_mwh': float(snapshot.total_generation_mwh or 0),
            'peak_demand_mw': float(snapshot.peak_demand_mw or 0),
            'supply_demand_gap_mw': float(snapshot.supply_demand_gap_mw or 0),
            'active_alerts_count': snapshot.active_alerts_count,
        },

    }
