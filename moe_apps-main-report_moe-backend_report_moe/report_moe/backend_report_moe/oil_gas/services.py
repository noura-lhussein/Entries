from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Max

from .metric_catalog import (
    DISTRIBUTION_REGIONS,
    EXECUTIVE_KPI_GROUPS,
    EXECUTIVE_METRIC_KEYS,
    EXECUTIVE_TREND_METRICS,
    KPI_METRICS,
    METRIC_BY_KEY,
    METRIC_SPECS,
    MONTHLY_AGGREGATION,
    PRODUCTS,
    resolve_metric_labels,
)
from .models import DailyMetric, DailyReport


def _float(value: Decimal | float | int) -> float:
    return float(value)


def _metric_map(report: DailyReport) -> dict[tuple[str, str], DailyMetric]:
    return {(m.metric_key, m.dimension): m for m in report.metrics.all()}


def _get_value(metrics: dict[tuple[str, str], DailyMetric], key: str, dimension: str = '') -> float | None:
    row = metrics.get((key, dimension))
    return _float(row.value) if row else None


def _kpi_status(spec_key: str, value: float | None) -> str:
    if value is None:
        return 'neutral'
    spec = METRIC_BY_KEY.get(spec_key)
    if not spec or not spec.kpi_status_rule:
        return 'ok'
    if spec.kpi_status_rule == 'zero_is_bad' and value == 0:
        return 'critical'
    if spec.kpi_status_rule == 'higher_is_bad' and value > 50:
        return 'warning' if value < 100 else 'critical'
    if spec.kpi_status_rule == 'lower_is_bad' and value < 30:
        return 'critical' if value < 15 else 'warning'
    return 'ok'


def _delta_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 1)


def get_latest_report_date() -> date | None:
    return DailyReport.objects.filter(status=DailyReport.Status.PUBLISHED).aggregate(
        latest=Max('report_date'),
    )['latest']


def get_report_for_date(report_date: date | None) -> DailyReport | None:
    if report_date:
        return (
            DailyReport.objects.filter(
                report_date=report_date, status=DailyReport.Status.PUBLISHED)
            .prefetch_related('metrics')
            .first()
        )
    latest = get_latest_report_date()
    if not latest:
        return None
    return (
        DailyReport.objects.filter(
            report_date=latest, status=DailyReport.Status.PUBLISHED)
        .prefetch_related('metrics')
        .first()
    )


def get_previous_report(report: DailyReport) -> DailyReport | None:
    return (
        DailyReport.objects.filter(
            report_date__lt=report.report_date,
            status=DailyReport.Status.PUBLISHED,
        )
        .order_by('-report_date')
        .prefetch_related('metrics')
        .first()
    )


def _has_executive_metrics(metrics: dict[tuple[str, str], DailyMetric]) -> bool:
    return any((key, '') in metrics for key in EXECUTIVE_METRIC_KEYS)


def _build_kpi_row(
    spec_key: str,
    metrics: dict[tuple[str, str], DailyMetric],
    prev_metrics: dict[tuple[str, str], DailyMetric],
    report_date: date,
) -> dict[str, Any]:
    spec = METRIC_BY_KEY[spec_key]
    value = _get_value(metrics, spec_key)
    prev_value = _get_value(prev_metrics, spec_key)
    label_en, label_ar = resolve_metric_labels(spec, report_date)
    return {
        'id': spec_key,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'unit': spec.unit,
        'target_value': None,
        'achievement_pct': None,
        'delta_pct': _delta_pct(value, prev_value),
        'status': _kpi_status(spec_key, value),
    }


def build_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    report = get_report_for_date(report_date)
    if not report:
        return {
            'report_date': None,
            'status': 'empty',
            'view': 'executive',
            'kpis': [],
            'kpi_groups': [],
            'charts': {},
            'trends': {},
            'alerts': [],
            'notes': [],
            'available_dates': list_available_dates(),
            'available_months': list_available_months(),
        }

    metrics = _metric_map(report)
    previous = get_previous_report(report)
    prev_metrics = _metric_map(previous) if previous else {}

    if not _has_executive_metrics(metrics):
        return {
            'report_date': report.report_date.isoformat(),
            'status': 'empty',
            'view': 'executive',
            'kpis': [],
            'kpi_groups': [],
            'charts': {},
            'trends': {},
            'alerts': [],
            'notes': [],
            'available_dates': list_available_dates(),
            'available_months': list_available_months(),
        }

    kpis = [
        _build_kpi_row(spec.key, metrics, prev_metrics, report.report_date)
        for spec in sorted(KPI_METRICS, key=lambda s: s.kpi_order or 0)
    ]
    kpi_by_id = {row['id']: row for row in kpis}

    kpi_groups: list[dict[str, Any]] = []
    for group_id, label_en, label_ar, keys in EXECUTIVE_KPI_GROUPS:
        group_kpis = [kpi_by_id[key] for key in keys if key in kpi_by_id]
        if group_kpis:
            kpi_groups.append(
                {
                    'id': group_id,
                    'label_en': label_en,
                    'label_ar': label_ar,
                    'kpis': group_kpis,
                }
            )

    clean_gas_mix = {
        'labels_en': ['Local production', 'Azerbaijan import', 'Jordan import'],
        'labels_ar': ['الإنتاج المحلي', 'استيراد أذربيجان', 'استيراد الأردن'],
        'values': [
            _get_value(metrics, 'local_clean_gas_mm3') or 0,
            _get_value(metrics, 'clean_gas_import_azerbaijan_mm3') or 0,
            _get_value(metrics, 'clean_gas_import_jordan_mm3') or 0,
        ],
        'unit': 'M m³',
    }

    fuel_sales = {
        'labels_en': ['Mazut', 'Gasoline 90+95', 'Domestic LPG', 'Fuel oil'],
        'labels_ar': ['مازوت', 'بنزين 90+95', 'غاز مسال منزلي', 'فيول'],
        'values': [
            _get_value(metrics, 'mazut_sold_thu_fri_m3') or 0,
            _get_value(metrics, 'gasoline_90_95_sold_thu_fri_m3') or 0,
            _get_value(metrics, 'domestic_lpg_sold_m3') or 0,
            _get_value(metrics, 'fuel_oil_sold_m3') or 0,
        ],
        'unit': 'm³',
    }

    gas_distribution = {
        'labels_en': ['Distributed to consumers', 'Electricity sector'],
        'labels_ar': ['موزّع للمستهلكين', 'قطاع الكهرباء'],
        'values': [
            _get_value(metrics, 'clean_gas_distributed_mm3') or 0,
            _get_value(metrics, 'electricity_clean_gas_consumption_mm3') or 0,
        ],
        'unit': 'M m³',
    }

    trends = {
        metric_key: build_metric_trend(
            metric_key, days=14, end_date=report.report_date)
        for metric_key in EXECUTIVE_TREND_METRICS
    }

    notes: list[dict[str, str]] = []
    if report.notes_ar or report.notes_en:
        notes.append({'ar': report.notes_ar, 'en': report.notes_en})

    return {
        'report_date': report.report_date.isoformat(),
        'status': 'ready',
        'view': 'executive',
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'charts': {
            'clean_gas_mix': clean_gas_mix,
            'fuel_sales': fuel_sales,
            'gas_distribution': gas_distribution,
        },
        'trends': trends,
        'alerts': [],
        'notes': notes,
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
    }


def build_legacy_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    report = get_report_for_date(report_date)
    if not report:
        return {
            'report_date': None,
            'status': 'empty',
            'kpis': [],
            'charts': {},
            'alerts': [],
            'notes': [],
            'available_dates': list_available_dates(),
            'available_months': list_available_months(),
        }

    metrics = _metric_map(report)
    previous = get_previous_report(report)
    prev_metrics = _metric_map(previous) if previous else {}

    legacy_specs = [
        spec for spec in METRIC_SPECS if spec.key not in EXECUTIVE_METRIC_KEYS and spec.kpi_order]
    kpis: list[dict[str, Any]] = []
    for spec in sorted(legacy_specs, key=lambda s: s.kpi_order or 0):
        value = _get_value(metrics, spec.key)
        prev_value = _get_value(prev_metrics, spec.key)
        kpis.append(
            {
                'id': spec.key,
                'label_en': spec.label_en,
                'label_ar': spec.label_ar,
                'value': value,
                'unit': spec.unit,
                'delta_pct': _delta_pct(value, prev_value),
                'status': _kpi_status(spec.key, value),
            }
        )

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

    crude_trend = build_metric_trend(
        'crude_transfer_daily_bbl', days=14, end_date=report.report_date)
    gas_trend = build_metric_trend(
        'gas_production_k_m3', days=14, end_date=report.report_date)

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

    alerts: list[dict[str, str]] = []
    if (_get_value(metrics, 'units_operating') or 0) == 0:
        alerts.append(
            {
                'severity': 'critical',
                'message_en': 'No refinery units reported as operating.',
                'message_ar': 'لا توجد وحدات مصافٍ عاملة حسب التقرير.',
            }
        )
    if (_get_value(metrics, 'units_under_repair') or 0) > 50:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': 'High number of units under repair.',
                'message_ar': 'عدد مرتفع من الوحدات قيد الإصلاح.',
            }
        )

    notes: list[dict[str, str]] = []
    if report.notes_ar or report.notes_en:
        notes.append({'ar': report.notes_ar, 'en': report.notes_en})

    return {
        'report_date': report.report_date.isoformat(),
        'status': 'ready',
        'kpis': kpis,
        'charts': {
            'refinery_products': refinery_products,
            'product_mix_banias': product_mix,
            'crude_transfer_trend': crude_trend,
            'gas_production_trend': gas_trend,
            'distribution': distribution,
        },
        'alerts': alerts,
        'notes': notes,
        'available_dates': list_available_dates(),
    }


def build_metric_trend(
    metric_key: str,
    days: int = 30,
    dimension: str = '',
    end_date: date | None = None,
) -> dict[str, Any]:
    end = end_date or get_latest_report_date() or date.today()
    start = end - timedelta(days=days - 1)
    spec = METRIC_BY_KEY.get(metric_key)

    rows = (
        DailyMetric.objects.filter(
            metric_key=metric_key,
            dimension=dimension,
            report__report_date__gte=start,
            report__report_date__lte=end,
            report__status=DailyReport.Status.PUBLISHED,
        )
        .select_related('report')
        .order_by('report__report_date')
    )

    points = [
        {
            'date': row.report.report_date.isoformat(),
            'value': _float(row.value),
        }
        for row in rows
    ]

    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': points,
    }


def list_available_dates(limit: int = 90) -> list[str]:
    return [
        d.isoformat()
        for d in DailyReport.objects.filter(status=DailyReport.Status.PUBLISHED)
        .order_by('-report_date')
        .values_list('report_date', flat=True)[:limit]
    ]


def list_available_months(limit: int = 24) -> list[str]:
    months: list[str] = []
    seen: set[str] = set()
    for report_date in (
        DailyReport.objects.filter(status=DailyReport.Status.PUBLISHED)
        .order_by('-report_date')
        .values_list('report_date', flat=True)
    ):
        month_key = f'{report_date.year}-{report_date.month:02d}'
        if month_key in seen:
            continue
        seen.add(month_key)
        months.append(month_key)
        if len(months) >= limit:
            break
    return months


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    return month_start, date(year, month, last_day)


def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _reports_for_month(year: int, month: int) -> list[DailyReport]:
    month_start, month_end = _month_bounds(year, month)
    return list(
        DailyReport.objects.filter(
            report_date__gte=month_start,
            report_date__lte=month_end,
            status=DailyReport.Status.PUBLISHED,
        )
        .prefetch_related('metrics')
        .order_by('report_date')
    )


def _aggregate_metric_values(values: list[float], rule: str) -> float | None:
    if not values:
        return None
    if rule == 'sum':
        return sum(values)
    if rule == 'max':
        return max(values)
    if rule == 'last':
        return values[-1]
    return sum(values) / len(values)


def _build_monthly_metric_map(reports: list[DailyReport]) -> dict[tuple[str, str], float]:
    series: dict[tuple[str, str], list[float]] = defaultdict(list)
    for report in reports:
        for metric in report.metrics.all():
            if metric.dimension:
                continue
            if metric.metric_key not in EXECUTIVE_METRIC_KEYS:
                continue
            series[(metric.metric_key, metric.dimension)
                   ].append(_float(metric.value))

    aggregated: dict[tuple[str, str], float] = {}
    for key, values in series.items():
        rule = MONTHLY_AGGREGATION.get(key[0], 'avg')
        value = _aggregate_metric_values(values, rule)
        if value is not None:
            aggregated[key] = value
    return aggregated


def _get_monthly_value(metrics: dict[tuple[str, str], float], key: str, dimension: str = '') -> float | None:
    return metrics.get((key, dimension))


def _build_monthly_kpi_row(
    spec_key: str,
    metrics: dict[tuple[str, str], float],
    prev_metrics: dict[tuple[str, str], float],
    anchor_date: date,
) -> dict[str, Any]:
    spec = METRIC_BY_KEY[spec_key]
    value = _get_monthly_value(metrics, spec_key)
    prev_value = _get_monthly_value(prev_metrics, spec_key)
    label_en, label_ar = resolve_metric_labels(spec, anchor_date)
    return {
        'id': spec_key,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'unit': spec.unit,
        'target_value': None,
        'achievement_pct': None,
        'delta_pct': _delta_pct(value, prev_value),
        'status': _kpi_status(spec_key, value),
    }


def build_metric_trend_for_range(
    metric_key: str,
    *,
    start_date: date,
    end_date: date,
    dimension: str = '',
) -> dict[str, Any]:
    spec = METRIC_BY_KEY.get(metric_key)
    rows = (
        DailyMetric.objects.filter(
            metric_key=metric_key,
            dimension=dimension,
            report__report_date__gte=start_date,
            report__report_date__lte=end_date,
            report__status=DailyReport.Status.PUBLISHED,
        )
        .select_related('report')
        .order_by('report__report_date')
    )
    points = [
        {
            'date': row.report.report_date.isoformat(),
            'value': _float(row.value),
        }
        for row in rows
    ]
    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': points,
    }


def build_monthly_dashboard_payload(year: int, month: int) -> dict[str, Any]:
    reports = _reports_for_month(year, month)
    empty_base = {
        'period': 'month',
        'month': f'{year}-{month:02d}',
        'report_date': None,
        'anchor_date': None,
        'reports_count': 0,
        'days_covered': 0,
        'status': 'empty',
        'view': 'executive',
        'kpis': [],
        'kpi_groups': [],
        'charts': {},
        'trends': {},
        'alerts': [],
        'notes': [],
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
    }
    if not reports:
        return empty_base

    anchor_report = reports[-1]
    month_start, month_end = _month_bounds(year, month)
    metrics = _build_monthly_metric_map(reports)

    prev_year, prev_month = _previous_month(year, month)
    prev_reports = _reports_for_month(prev_year, prev_month)
    prev_metrics = _build_monthly_metric_map(
        prev_reports) if prev_reports else {}

    if not metrics:
        empty_base.update({
            'report_date': anchor_report.report_date.isoformat(),
            'anchor_date': anchor_report.report_date.isoformat(),
        })
        return empty_base

    kpis = [
        _build_monthly_kpi_row(
            spec.key, metrics, prev_metrics, anchor_report.report_date)
        for spec in sorted(KPI_METRICS, key=lambda s: s.kpi_order or 0)
    ]
    kpi_by_id = {row['id']: row for row in kpis}
    kpi_groups: list[dict[str, Any]] = []
    for group_id, label_en, label_ar, keys in EXECUTIVE_KPI_GROUPS:
        group_kpis = [kpi_by_id[key] for key in keys if key in kpi_by_id]
        if group_kpis:
            kpi_groups.append({
                'id': group_id,
                'label_en': label_en,
                'label_ar': label_ar,
                'kpis': group_kpis,
            })

    clean_gas_mix = {
        'labels_en': ['Local production', 'Azerbaijan import', 'Jordan import'],
        'labels_ar': ['الإنتاج المحلي', 'استيراد أذربيجان', 'استيراد الأردن'],
        'values': [
            _get_monthly_value(metrics, 'local_clean_gas_mm3') or 0,
            _get_monthly_value(
                metrics, 'clean_gas_import_azerbaijan_mm3') or 0,
            _get_monthly_value(metrics, 'clean_gas_import_jordan_mm3') or 0,
        ],
        'unit': 'M m³',
    }
    fuel_sales = {
        'labels_en': ['Mazut', 'Gasoline 90+95', 'Domestic LPG', 'Fuel oil'],
        'labels_ar': ['مازوت', 'بنزين 90+95', 'غاز مسال منزلي', 'فيول'],
        'values': [
            _get_monthly_value(metrics, 'mazut_sold_thu_fri_m3') or 0,
            _get_monthly_value(metrics, 'gasoline_90_95_sold_thu_fri_m3') or 0,
            _get_monthly_value(metrics, 'domestic_lpg_sold_m3') or 0,
            _get_monthly_value(metrics, 'fuel_oil_sold_m3') or 0,
        ],
        'unit': 'm³',
    }
    gas_distribution = {
        'labels_en': ['Distributed to consumers', 'Electricity sector'],
        'labels_ar': ['موزّع للمستهلكين', 'قطاع الكهرباء'],
        'values': [
            _get_monthly_value(metrics, 'clean_gas_distributed_mm3') or 0,
            _get_monthly_value(
                metrics, 'electricity_clean_gas_consumption_mm3') or 0,
        ],
        'unit': 'M m³',
    }
    trends = {
        metric_key: build_metric_trend_for_range(
            metric_key,
            start_date=month_start,
            end_date=month_end,
        )
        for metric_key in EXECUTIVE_TREND_METRICS
    }
    notes: list[dict[str, str]] = []
    if anchor_report.notes_ar or anchor_report.notes_en:
        notes.append({'ar': anchor_report.notes_ar,
                     'en': anchor_report.notes_en})

    return {
        'period': 'month',
        'month': f'{year}-{month:02d}',
        'report_date': anchor_report.report_date.isoformat(),
        'anchor_date': anchor_report.report_date.isoformat(),
        'reports_count': len(reports),
        'days_covered': len(reports),
        'status': 'ready',
        'view': 'executive',
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'charts': {
            'clean_gas_mix': clean_gas_mix,
            'fuel_sales': fuel_sales,
            'gas_distribution': gas_distribution,
        },
        'trends': trends,
        'alerts': [],
        'notes': notes,
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
    }


def build_report_detail_payload(report_date: date) -> dict[str, Any] | None:
    report = DailyReport.objects.filter(
        report_date=report_date).prefetch_related('metrics').first()
    if not report:
        return None
    return {
        'report_date': report.report_date.isoformat(),
        'status': report.status,
        'notes_ar': report.notes_ar,
        'notes_en': report.notes_en,
        'metrics': [
            {
                'metric_key': row.metric_key,
                'dimension': row.dimension,
                'value': _float(row.value),
                'unit': row.unit,
            }
            for row in report.metrics.all()
            if not row.dimension
        ],
    }


def upsert_metric(
    report: DailyReport,
    metric_key: str,
    value: Decimal | float | int,
    dimension: str = '',
    unit: str = '',
) -> None:
    spec = METRIC_BY_KEY.get(metric_key)
    DailyMetric.objects.update_or_create(
        report=report,
        metric_key=metric_key,
        dimension=dimension,
        defaults={
            'value': Decimal(str(value)),
            'unit': unit or (spec.unit if spec else ''),
        },
    )
