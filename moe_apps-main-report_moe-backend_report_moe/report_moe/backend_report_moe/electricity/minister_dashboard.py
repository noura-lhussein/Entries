from __future__ import annotations

from datetime import date
from typing import Any

from .models import Alert, DailyReport, PowerPlant, Substation, TransmissionLine
from .services import _delta_pct
from .snapshot_builder import (
    get_previous_snapshot,
    get_snapshot,
    list_snapshot_dates,
    snapshot_trend,
)
from .target_catalog import SNAPSHOT_TARGET_MAP, TARGET_METRIC_BY_KEY
from .target_resolver import achievement_pct, resolve_target_value, target_status


def _float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _status_card(
    card_id: str,
    label_en: str,
    label_ar: str,
    value: str,
    status: str,
    detail_en: str = '',
    detail_ar: str = '',
) -> dict[str, str]:
    return {
        'id': card_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'status': status,
        'detail_en': detail_en,
        'detail_ar': detail_ar,
    }


def _resolve_kpi_target(snapshot, field: str, target_field: str | None) -> float | None:
    if target_field:
        return _float(getattr(snapshot, target_field, None))
    metric_key = SNAPSHOT_TARGET_MAP.get(field, field)
    resolved = resolve_target_value(metric_key, snapshot.snapshot_date)
    return _float(resolved) if resolved is not None else None


def _minister_kpis(snapshot, previous) -> list[dict[str, Any]]:
    specs = [
        ('generation', 'Total generation', 'إجمالي التوليد', 'MWh', 'total_generation_mwh', 'target_total_generation_mwh'),
        ('peak_demand', 'Peak demand', 'ذروة الحمل', 'MW', 'peak_demand_mw', 'target_peak_demand_mw'),
        ('gap', 'Supply–demand gap', 'فجوة العرض والطلب', 'MW', 'supply_demand_gap_mw', None),
        ('availability', 'Plant availability', 'توفر المحطات', '%', 'plant_availability_percent', 'target_plant_availability_percent'),
        ('capacity_factor', 'Capacity factor', 'معامل الحمل', '%', 'capacity_factor_percent', None),
        ('renewable', 'Renewable share', 'حصة المتجددة', '%', 'renewable_share_percent', None),
        ('installed', 'Installed capacity', 'القدرة المركبة', 'MW', 'total_installed_mw', None),
    ]
    kpis = []
    for kpi_id, label_en, label_ar, unit, field, target_field in specs:
        value = _float(getattr(snapshot, field, None))
        prev_value = _float(getattr(previous, field, None)) if previous else None
        target_value = _resolve_kpi_target(snapshot, field, target_field)
        metric_key = SNAPSHOT_TARGET_MAP.get(field, field)
        spec = TARGET_METRIC_BY_KEY.get(metric_key)
        higher = spec.higher_is_better if spec else (field != 'supply_demand_gap_mw')
        if field == 'supply_demand_gap_mw':
            higher = False
        achieve = achievement_pct(value, target_value, higher_is_better=higher)
        kpis.append(
            {
                'id': kpi_id,
                'label_en': label_en,
                'label_ar': label_ar,
                'value': value,
                'unit': unit,
                'target_value': target_value,
                'achievement_pct': achieve,
                'delta_pct': _delta_pct(value, prev_value),
                'status': target_status(achieve, higher_is_better=higher) if target_value is not None else 'neutral',
            }
        )
    return kpis


def _status_cards(snapshot) -> list[dict[str, str]]:
    total_plants = PowerPlant.objects.count()
    active = PowerPlant.objects.filter(status=PowerPlant.Status.ACTIVE).count()
    shutdown = PowerPlant.objects.filter(status=PowerPlant.Status.SHUTDOWN).count()
    maintenance = PowerPlant.objects.filter(status=PowerPlant.Status.MAINTENANCE).count()

    total_lines = TransmissionLine.objects.count()
    normal_lines = TransmissionLine.objects.filter(status=TransmissionLine.Status.NORMAL).count()

    total_subs = Substation.objects.count()
    active_subs = Substation.objects.filter(status=Substation.Status.ACTIVE).count()

    plant_status = 'critical' if shutdown else ('warning' if active < total_plants else 'ok')
    line_status = 'warning' if normal_lines < total_lines else 'ok'
    sub_status = 'warning' if active_subs < total_subs else 'ok'

    gap = _float(snapshot.supply_demand_gap_mw)
    gap_status = 'critical' if gap and gap > 0 else 'ok'
    if gap and gap > 0 and gap < 200:
        gap_status = 'warning'

    return [
        _status_card(
            'plants',
            'Active plants',
            'محطات عاملة',
            f'{active}/{total_plants}',
            plant_status,
            f'{shutdown} shutdown, {maintenance} maintenance' if shutdown or maintenance else 'All operational',
            f'{shutdown} متوقف، {maintenance} صيانة' if shutdown or maintenance else 'جميعها جاهزة',
        ),
        _status_card(
            'transmission',
            'Transmission lines',
            'خطوط النقل',
            f'{normal_lines}/{total_lines}',
            line_status,
            'Normal operations',
            'تشغيل طبيعي',
        ),
        _status_card(
            'substations',
            'Substations',
            'محطات التحويل',
            f'{active_subs}/{total_subs}',
            sub_status,
            'Grid nodes',
            'عقد الشبكة',
        ),
        _status_card(
            'balance',
            'Grid balance',
            'توازن الشبكة',
            f'{gap or "—"} MW' if gap is not None else '—',
            gap_status,
            'Supply vs peak demand',
            'العرض مقابل ذروة الحمل',
        ),
    ]


def _generation_by_plant(snapshot_date: date) -> dict[str, Any]:
    from .models import DailyGeneration

    rows = DailyGeneration.objects.filter(report_date=snapshot_date).select_related('plant')
    return {
        'labels_en': [r.plant.name_en for r in rows],
        'labels_ar': [r.plant.name_ar for r in rows],
        'values_mwh': [float(r.gross_generation_mwh or 0) for r in rows],
    }


def build_minister_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    snapshot = get_snapshot(report_date)
    if not snapshot:
        return {
            'report_date': None,
            'status': 'empty',
            'view': 'minister',
            'kpis': [],
            'status_cards': [],
            'charts': {},
            'trends': {},
            'alerts': [],
            'notes': [],
            'available_dates': [],
        }

    previous = get_previous_snapshot(snapshot)
    snapshot_date = snapshot.snapshot_date

    alerts_qs = Alert.objects.filter(snapshot_date=snapshot_date, is_resolved=False).order_by('-alert_time')[:20]
    alerts = [
        {
            'severity': row.severity,
            'message_en': row.title_en,
            'message_ar': row.title_ar,
            'alert_type': row.alert_type,
        }
        for row in alerts_qs
    ]

    notes: list[dict[str, str]] = []
    report = DailyReport.objects.filter(report_date=snapshot_date).first()
    if report and (report.notes_ar or report.notes_en):
        notes.append({'ar': report.notes_ar, 'en': report.notes_en})

    return {
        'report_date': snapshot_date.isoformat(),
        'status': 'ready',
        'view': 'minister',
        'kpis': _minister_kpis(snapshot, previous),
        'status_cards': _status_cards(snapshot),
        'charts': {
            'generation_by_plant': _generation_by_plant(snapshot_date),
        },
        'trends': {
            'generation': {
                'label_en': 'Generation trend',
                'label_ar': 'اتجاه التوليد',
                'unit': 'MWh',
                'points': snapshot_trend('total_generation_mwh', days=14, end_date=snapshot_date),
            },
            'peak_demand': {
                'label_en': 'Peak demand trend',
                'label_ar': 'اتجاه ذروة الحمل',
                'unit': 'MW',
                'points': snapshot_trend('peak_demand_mw', days=14, end_date=snapshot_date),
            },
            'availability': {
                'label_en': 'Plant availability',
                'label_ar': 'توفر المحطات',
                'unit': '%',
                'points': snapshot_trend('plant_availability_percent', days=14, end_date=snapshot_date),
            },
        },
        'alerts': alerts,
        'notes': notes,
        'available_dates': list_snapshot_dates(),

    }
