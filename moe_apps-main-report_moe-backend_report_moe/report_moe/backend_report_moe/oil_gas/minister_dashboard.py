from __future__ import annotations

from datetime import date
from typing import Any

from .models import Alert, DailyReport, Field, Pipeline, Refinery
from .services import (
    _delta_pct,
    _get_value,
    _metric_map,
    get_report_for_date,
    list_available_dates,
)
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
        ('total_oil', 'Oil production', 'إنتاج النفط', 'bbl/d', 'total_oil_production_bpd', 'target_total_oil_production_bpd'),
        ('total_gas', 'Gas production', 'إنتاج الغاز', 'MMscf/d', 'total_gas_production_mmscf', 'target_total_gas_production_mmscf'),
        ('exports', 'Exports', 'الصادرات', 'bbl', 'total_export_bbl', 'target_total_export_bbl'),
        ('revenue', 'Export revenue', 'إيرادات التصدير', 'USD', 'export_revenue_usd', 'target_export_revenue_usd'),
        ('gasoline_stock', 'Gasoline stock', 'مخزون البنزين', 'days', 'gasoline_stock_days', 'target_gasoline_stock_days'),
        ('diesel_stock', 'Diesel stock', 'مخزون الديزل', 'days', 'diesel_stock_days', None),
        ('gas_to_power', 'Gas to power', 'غاز للكهرباء', '%', 'gas_supply_to_power_percent', 'target_gas_supply_to_power_percent'),
        ('refinery_util', 'Refinery util.', 'استغلال المصافي', '%', 'refinery_utilization_percent', None),
        ('losses', 'Prod. losses', 'فاقد الإنتاج', 'bbl/d', 'total_losses_bbl', None),
    ]
    kpis = []
    for kpi_id, label_en, label_ar, unit, field, target_field in specs:
        value = _float(getattr(snapshot, field, None))
        prev_value = _float(getattr(previous, field, None)) if previous else None
        target_value = _resolve_kpi_target(snapshot, field, target_field)
        metric_key = SNAPSHOT_TARGET_MAP.get(field, field)
        spec = TARGET_METRIC_BY_KEY.get(metric_key)
        higher = spec.higher_is_better if spec else True
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
                'status': target_status(achieve, higher_is_better=higher),
            }
        )
    return kpis


def _status_cards(snapshot_date: date, snapshot) -> list[dict[str, str]]:
    total_fields = Field.objects.count()
    active_fields = Field.objects.filter(status=Field.Status.ACTIVE).count()
    shutdown_fields = Field.objects.filter(status=Field.Status.SHUTDOWN).count()

    total_refineries = Refinery.objects.count()
    operating_refineries = Refinery.objects.filter(status=Refinery.Status.OPERATING).count()

    normal_pipelines = Pipeline.objects.filter(status=Pipeline.Status.NORMAL).count()
    total_pipelines = Pipeline.objects.count()

    gasoline_days = _float(snapshot.gasoline_stock_days)
    stock_status = 'critical' if gasoline_days is not None and gasoline_days < 5 else 'ok'
    if gasoline_days is not None and gasoline_days < 8:
        stock_status = 'warning' if stock_status == 'ok' else stock_status

    field_status = 'critical' if shutdown_fields else ('warning' if active_fields < total_fields else 'ok')
    refinery_status = 'critical' if operating_refineries < total_refineries else 'ok'
    pipeline_status = 'warning' if normal_pipelines < total_pipelines else 'ok'

    return [
        _status_card(
            'fields',
            'Oil fields status',
            'حالة الحقول',
            f'{active_fields}/{total_fields}',
            field_status,
            f'{shutdown_fields} shutdown' if shutdown_fields else 'All active',
            f'{shutdown_fields} متوقف' if shutdown_fields else 'جميعها عاملة',
        ),
        _status_card(
            'refineries',
            'Refineries status',
            'حالة المصافي',
            f'{operating_refineries}/{total_refineries}',
            refinery_status,
            'Operating units',
            'وحدات عاملة',
        ),
        _status_card(
            'pipelines',
            'Pipelines status',
            'حالة الخطوط',
            f'{normal_pipelines}/{total_pipelines}',
            pipeline_status,
            'Normal operations',
            'تشغيل طبيعي',
        ),
        _status_card(
            'stock',
            'Strategic stock',
            'المخزون الاستراتيجي',
            f'{gasoline_days or "—"} d' if gasoline_days is not None else '—',
            stock_status,
            'Gasoline coverage',
            'كفاية البنزين',
        ),
    ]


def _legacy_charts(report_date: date) -> dict[str, Any]:
    report = get_report_for_date(report_date)
    if not report:
        return {}
    from .metric_catalog import DISTRIBUTION_REGIONS, METRIC_BY_KEY, PRODUCTS

    metrics = _metric_map(report)
    refinery_products = {
        'labels_en': ['Homs', 'Banias'],
        'labels_ar': ['حمص', 'بانياس'],
        'products': [
            {
                'key': product,
                'label_en': METRIC_BY_KEY[product].label_en,
                'label_ar': METRIC_BY_KEY[product].label_ar,
                'values': [
                    _get_value(metrics, product, 'homs') or 0,
                    _get_value(metrics, product, 'banias') or 0,
                ],
            }
            for product in PRODUCTS
        ],
    }
    banias_gasoline = _get_value(metrics, 'product_gasoline_t', 'banias') or 0
    banias_mazut = _get_value(metrics, 'product_mazut_t', 'banias') or 0
    banias_fuel = _get_value(metrics, 'product_fuel_oil_t', 'banias') or 0
    mix_total = banias_gasoline + banias_mazut + banias_fuel
    product_mix = {
        'refinery': 'banias',
        'labels_en': ['Gasoline', 'Mazut', 'Fuel oil'],
        'labels_ar': ['بنزين', 'مازوت', 'فيول'],
        'values': [banias_gasoline, banias_mazut, banias_fuel],
        'percentages': [
            round((banias_gasoline / mix_total) * 100, 1) if mix_total else 0,
            round((banias_mazut / mix_total) * 100, 1) if mix_total else 0,
            round((banias_fuel / mix_total) * 100, 1) if mix_total else 0,
        ],
    }
    distribution = {
        'regions': [
            {
                'key': key,
                'label_en': label_en,
                'label_ar': label_ar,
                'tonnes': _get_value(metrics, 'dist_tonnes', key) or 0,
                'reserve_days': _get_value(metrics, 'dist_reserve_days', key) or 0,
            }
            for key, label_en, label_ar in DISTRIBUTION_REGIONS
        ],
    }
    return {
        'refinery_products': refinery_products,
        'product_mix_banias': product_mix,
        'distribution': distribution,
    }


def build_minister_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    snapshot = get_snapshot(report_date)
    if not snapshot:
        legacy_dates = list_available_dates()
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
            'available_dates': legacy_dates,
        }

    previous = get_previous_snapshot(snapshot)
    snapshot_date = snapshot.snapshot_date

    alerts_qs = Alert.objects.filter(snapshot_date=snapshot_date, is_resolved=False).order_by(
        '-alert_time',
    )[:20]
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

    dates = list_snapshot_dates()
    if not dates:
        dates = list_available_dates()

    return {
        'report_date': snapshot_date.isoformat(),
        'status': 'ready',
        'view': 'minister',
        'kpis': _minister_kpis(snapshot, previous),
        'status_cards': _status_cards(snapshot_date, snapshot),
        'charts': _legacy_charts(snapshot_date),
        'trends': {
            'production': {
                'label_en': 'Oil production trend',
                'label_ar': 'اتجاه إنتاج النفط',
                'unit': 'bbl/d',
                'points': snapshot_trend('total_oil_production_bpd', days=14, end_date=snapshot_date),
            },
            'exports': {
                'label_en': 'Export trend',
                'label_ar': 'اتجاه الصادرات',
                'unit': 'bbl',
                'points': snapshot_trend('total_export_bbl', days=14, end_date=snapshot_date),
            },
            'fuel_inventory': {
                'label_en': 'Gasoline stock days',
                'label_ar': 'كفاية مخزون البنزين',
                'unit': 'days',
                'points': snapshot_trend('gasoline_stock_days', days=14, end_date=snapshot_date),
            },
        },
        'alerts': alerts,
        'notes': notes,
        'available_dates': dates,
    }
