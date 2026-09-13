from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Max

from .report_template import national_scalar_metrics
from .governorates import GOVERNORATE_BY_CODE, GOVERNORATES
from .metric_catalog import (
    KPI_GROUP_LABEL_OVERRIDES,
    KPI_GROUPS,
    KPI_METRICS,
    METRIC_BY_KEY,
    MONTHLY_AGGREGATION,
    TREND_METRICS,
)
from .models import (
    DailyMetric,
    DailyReport,
    FuelTankReading,
    GenerationIncident,
    GenerationUnitReading,
    GovernorateLoad,
    GridLineIncident,
    HydroDamReading,
)
from .report_catalog import FUEL_TANK_BY_CODE


def _float(value: Decimal | float | int) -> float:
    return float(value)


def _is_maintenance_unit(item: dict[str, Any]) -> bool:
    return (
        item.get('status') == GenerationUnitReading.UnitStatus.MAINTENANCE
        or item.get('plant_code') == 'maintenance'
    )


def _is_maintenance_reading(row: GenerationUnitReading) -> bool:
    return row.status == GenerationUnitReading.UnitStatus.MAINTENANCE or row.plant_code == 'maintenance'


def _parse_maintenance_groups(text: str) -> list[str]:
    return [line.strip() for line in (text or '').splitlines() if line.strip()]


class _MetricValue:
    __slots__ = ('value',)

    def __init__(self, value: float):
        self.value = Decimal(str(value))


def _metric_map(report: DailyReport) -> dict[tuple[str, str], DailyMetric]:
    return {(m.metric_key, m.dimension): m for m in report.metrics.all()}


def _get_value(metrics: dict[tuple[str, str], DailyMetric | _MetricValue], key: str, dimension: str = '') -> float | None:
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
    if spec.kpi_status_rule == 'higher_is_bad' and value > 15:
        return 'warning' if value < 30 else 'critical'
    if spec.kpi_status_rule == 'count_is_bad' and value > 0:
        return 'warning' if value < 3 else 'critical'
    if spec.kpi_status_rule == 'lower_is_bad' and value < 80000:
        return 'warning' if value > 50000 else 'critical'
    if spec.kpi_status_rule == 'pct_lower_is_bad' and value < 30:
        return 'warning' if value > 20 else 'critical'
    if spec.kpi_status_rule == 'negative_is_bad' and value < 0:
        return 'critical' if value < -500 else 'warning'
    return 'ok'


def _ordered_dashboard_kpi_keys() -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for _, _, _, group_keys in KPI_GROUPS:
        for key in group_keys:
            if key not in seen and key in METRIC_BY_KEY:
                keys.append(key)
                seen.add(key)
    for spec in sorted(KPI_METRICS, key=lambda s: s.kpi_order or 0):
        if spec.key not in seen:
            keys.append(spec.key)
            seen.add(spec.key)
    return keys


def _build_kpi_row(
    spec_key: str,
    metrics: dict[tuple[str, str], DailyMetric | _MetricValue],
    prev_metrics: dict[tuple[str, str], DailyMetric | _MetricValue],
) -> dict[str, Any]:
    spec = METRIC_BY_KEY[spec_key]
    value = _get_value(metrics, spec.key)
    prev_value = _get_value(prev_metrics, spec.key)
    return {
        'id': spec.key,
        'label_en': spec.label_en,
        'label_ar': spec.label_ar,
        'value': value,
        'unit': spec.unit,
        'delta_pct': _delta_pct(value, prev_value),
        'status': _kpi_status(spec.key, value),
    }


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
            .prefetch_related(
                'metrics',
                'governorate_loads',
                'hydro_readings',
                'fuel_tank_readings',
                'generation_unit_readings',
                'generation_incidents',
                'grid_incidents',
            )
            .first()
        )
    latest = get_latest_report_date()
    if not latest:
        return None
    return (
        DailyReport.objects.filter(
            report_date=latest, status=DailyReport.Status.PUBLISHED)
        .prefetch_related(
            'metrics',
            'governorate_loads',
            'hydro_readings',
            'fuel_tank_readings',
            'generation_unit_readings',
            'generation_incidents',
            'grid_incidents',
        )
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
        .prefetch_related(
            'metrics',
            'governorate_loads',
            'hydro_readings',
            'fuel_tank_readings',
            'generation_unit_readings',
            'generation_incidents',
            'grid_incidents',
        )
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


def _build_monthly_metric_map(reports: list[DailyReport]) -> dict[tuple[str, str], _MetricValue]:
    series: dict[tuple[str, str], list[float]] = defaultdict(list)
    for report in reports:
        for metric in report.metrics.all():
            series[(metric.metric_key, metric.dimension)
                   ].append(_float(metric.value))

    aggregated: dict[tuple[str, str], _MetricValue] = {}
    for (metric_key, dimension), values in series.items():
        rule = MONTHLY_AGGREGATION.get(metric_key, 'avg')
        value = _aggregate_metric_values(values, rule)
        if value is not None:
            aggregated[(metric_key, dimension)] = _MetricValue(value)
    return aggregated


def _build_kpi_groups(kpis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kpi_by_id = {row['id']: row for row in kpis}
    kpi_groups: list[dict[str, Any]] = []
    for group_id, label_en, label_ar, keys in KPI_GROUPS:
        group_kpis = [{**kpi_by_id[key]} for key in keys if key in kpi_by_id]
        for kpi in group_kpis:
            override = KPI_GROUP_LABEL_OVERRIDES.get((group_id, kpi['id']))
            if override:
                kpi['label_en'], kpi['label_ar'] = override
        if group_kpis:
            kpi_groups.append(
                {
                    'id': group_id,
                    'label_en': label_en,
                    'label_ar': label_ar,
                    'kpis': group_kpis,
                }
            )
    return kpi_groups


def _build_governorate_chart_from_reports(reports: list[DailyReport]) -> dict[str, Any]:
    consumed_by_code: dict[str, float] = defaultdict(float)
    allocated_by_code: dict[str, float] = defaultdict(float)
    for report in reports:
        for row in report.governorate_loads.all():
            consumed_by_code[row.governorate_code] += _float(row.consumed_mw)
            allocated_by_code[row.governorate_code] += _float(row.allocated_mw)

    return {
        'labels_en': [GOVERNORATE_BY_CODE[code][0] for code, _, _ in GOVERNORATES],
        'labels_ar': [GOVERNORATE_BY_CODE[code][1] for code, _, _ in GOVERNORATES],
        'consumed': [consumed_by_code.get(code, 0) for code, _, _ in GOVERNORATES],
        'allocated': [allocated_by_code.get(code, 0) for code, _, _ in GOVERNORATES],
    }


def _build_generation_mix(metrics: dict[tuple[str, str], DailyMetric | _MetricValue]) -> dict[str, Any]:
    return {
        'labels_en': ['Hydro dams', 'Gas (24h)', 'Steam groups', 'Solar', 'Wind'],
        'labels_ar': [
            'الاستطاعة المتاحة  للسدود المائية (الفرات و تشرين)',
            'التوليد الغازي',
            'البخاري',
            'الاستطاعة المتاحة للعنافات الشمسية',
            'الاستطاعة المتاحة للعنافات الريحية',
        ],
        'values': [
            _get_value(metrics, 'hydro_dams_capacity_mw') or 0,
            _get_value(metrics, 'gas_generation_mwh_24h') or 0,
            _get_value(metrics, 'steam_groups_mw') or 0,
            _get_value(metrics, 'solar_capacity_mw') or 0,
            _get_value(metrics, 'wind_capacity_mw') or 0,
        ],
    }


def _build_fuel_tanks_chart(report: DailyReport) -> dict[str, Any] | None:
    fuel_tank_rows = list(report.fuel_tank_readings.all())
    if not fuel_tank_rows:
        return None
    return {
        'labels_en': [
            FUEL_TANK_BY_CODE[row.station_code].label_en
            for row in fuel_tank_rows
            if row.station_code in FUEL_TANK_BY_CODE
        ],
        'labels_ar': [
            FUEL_TANK_BY_CODE[row.station_code].label_ar
            for row in fuel_tank_rows
            if row.station_code in FUEL_TANK_BY_CODE
        ],
        'current_tons': [
            _float(row.current_tons) if row.current_tons is not None else 0 for row in fuel_tank_rows
        ],
        'max_capacity_tons': [
            _float(row.max_capacity_tons) if row.max_capacity_tons is not None else 0
            for row in fuel_tank_rows
        ],
        'fill_pct': [
            round((_float(row.current_tons) / _float(row.max_capacity_tons)) * 100, 1)
            if row.current_tons is not None and row.max_capacity_tons
            else 0
            for row in fuel_tank_rows
        ],
    }


def _aggregate_hydro_rows(reports: list[DailyReport]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {
            'front_level_m': [],
            'back_level_m': [],
            'generation_mwh': [],
            'outflow_m3s': [],
            'inflow_m3s': [],
            'expected_m3s': [],
        }
    )
    for report in reports:
        for row in report.hydro_readings.all():
            bucket = buckets[row.dam_code]
            if row.front_level_m is not None:
                bucket['front_level_m'].append(_float(row.front_level_m))
            if row.back_level_m is not None:
                bucket['back_level_m'].append(_float(row.back_level_m))
            if row.generation_mwh is not None:
                bucket['generation_mwh'].append(_float(row.generation_mwh))
            if row.outflow_m3s is not None:
                bucket['outflow_m3s'].append(_float(row.outflow_m3s))
            if row.inflow_m3s is not None:
                bucket['inflow_m3s'].append(_float(row.inflow_m3s))
            if row.expected_m3s is not None:
                bucket['expected_m3s'].append(_float(row.expected_m3s))

    hydro_rows: list[dict[str, Any]] = []
    for dam_code, values in buckets.items():
        hydro_rows.append(
            {
                'dam_code': dam_code,
                'front_level_m': _aggregate_metric_values(values['front_level_m'], 'avg'),
                'back_level_m': _aggregate_metric_values(values['back_level_m'], 'avg'),
                'generation_mwh': _aggregate_metric_values(values['generation_mwh'], 'sum'),
                'outflow_m3s': _aggregate_metric_values(values['outflow_m3s'], 'avg'),
                'inflow_m3s': _aggregate_metric_values(values['inflow_m3s'], 'avg'),
                'expected_m3s': _aggregate_metric_values(values['expected_m3s'], 'avg'),
            }
        )
    return hydro_rows


def _collect_monthly_incidents(reports: list[DailyReport]) -> dict[str, Any]:
    generation: list[dict[str, Any]] = []
    grid: list[dict[str, Any]] = []
    by_day_map: dict[str, dict[str, Any]] = {}

    for report in reports:
        day_key = report.report_date.isoformat()
        if day_key not in by_day_map:
            by_day_map[day_key] = {'date': day_key,
                                   'generation': [], 'grid': []}
        day_bucket = by_day_map[day_key]

        for row in report.generation_incidents.all():
            item = {
                'report_date': day_key,
                'event_time': row.event_time,
                'description_ar': row.description_ar,
                'description_en': row.description_en,
            }
            generation.append(item)
            day_bucket['generation'].append(item)

        for row in report.grid_incidents.all():
            item = {
                'report_date': day_key,
                'line_name': row.line_name,
                'voltage_kv': row.voltage_kv,
                'action_ar': row.action_ar,
                'action_en': row.action_en,
            }
            grid.append(item)
            day_bucket['grid'].append(item)

    by_day = [
        by_day_map[day_key]
        for day_key in sorted(by_day_map.keys())
        if by_day_map[day_key]['generation'] or by_day_map[day_key]['grid']
    ]
    return {'generation': generation, 'grid': grid, 'by_day': by_day}


def _collect_monthly_maintenance(reports: list[DailyReport]) -> tuple[str, list[str]]:
    lines: list[str] = []
    seen: set[str] = set()
    for report in reports:
        for line in _parse_maintenance_groups(report.maintenance_groups_ar):
            if line not in seen:
                seen.add(line)
                lines.append(line)
    return '\n'.join(lines), lines


def _build_alerts(metrics: dict[tuple[str, str], DailyMetric | _MetricValue]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    fuel_balance = _get_value(metrics, 'fuel_oil_balance_tpd')
    if fuel_balance is not None and fuel_balance < 0:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'Fuel oil deficit: {fuel_balance:.0f} t/day (received - consumed).',
                'message_ar': f'عجز فيول: {fuel_balance:.0f} طن/يوم.',
            }
        )
    fuel_reserve = _get_value(metrics, 'fuel_reserve_tons')
    if fuel_reserve is not None and fuel_reserve < 80000:
        alerts.append(
            {
                'severity': 'critical',
                'message_en': f'Fuel reserve below 80,000 t ({fuel_reserve:,.0f} t).',
                'message_ar': f'المخزون القابل للاستهلاك أقل من 80,000 طن ({fuel_reserve:,.0f} طن).',
            }
        )
    fuel_reserve_pct = _get_value(metrics, 'fuel_reserve_pct')
    if fuel_reserve_pct is not None and fuel_reserve_pct < 25:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'National fuel reserve at {fuel_reserve_pct:.1f}% of capacity.',
                'message_ar': f'المخزون القابل للاستهلاك عند {fuel_reserve_pct:.1f}% من السعة.',
            }
        )
    gov_excess = _get_value(metrics, 'gov_excess_mw')
    if gov_excess is not None and gov_excess > 15:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'National governorate overrun: +{gov_excess:.0f} MW.',
                'message_ar': f'تجاوز استهلاك المحافظات: +{gov_excess:.0f} م.و.',
            }
        )
    grid_incidents = _get_value(metrics, 'grid_incidents_count') or 0
    if grid_incidents > 0:
        alerts.append(
            {
                'severity': 'critical',
                'message_en': f'{int(grid_incidents)} transmission line incident(s) logged.',
                'message_ar': f'{int(grid_incidents)} حادث خطوط نقل مسجل.',
            }
        )
    generation_incidents = _get_value(
        metrics, 'generation_incidents_count') or 0
    if generation_incidents > 0:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'{int(generation_incidents)} generation incident(s) logged.',
                'message_ar': f'{int(generation_incidents)} حادث توليد مسجل.',
            }
        )
    return alerts


def _empty_dashboard_payload() -> dict[str, Any]:
    return {
        'period': 'day',
        'month': None,
        'report_date': None,
        'anchor_date': None,
        'reports_count': 0,
        'days_covered': 0,
        'status': 'empty',
        'kpis': [],
        'kpi_groups': [],
        'charts': {},
        'trends': {},
        'alerts': [],
        'notes': [],
        'incidents': {'generation': [], 'grid': []},
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
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
    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': [
            {'date': row.report.report_date.isoformat(), 'value': _float(row.value)}
            for row in rows
        ],
    }


def upsert_metric(
    report: DailyReport,
    metric_key: str,
    value: Decimal | float | int | None,
    dimension: str = '',
    unit: str = '',
) -> None:
    if value is None:
        return
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


def import_extracted_row(row: dict, *, publish: bool = True) -> DailyReport:
    report_date = date.fromisoformat(row['report_date'])
    with transaction.atomic():
        report, _ = DailyReport.objects.update_or_create(
            report_date=report_date,
            defaults={
                'reference_hour': row.get('reference_hour'),
                'peak_generation_time': row.get('peak_generation_time'),
                'status': DailyReport.Status.PUBLISHED if publish else DailyReport.Status.DRAFT,
                'source_file': row.get('source_file', ''),
                'notes_ar': row.get('notes_ar', ''),
                'maintenance_groups_ar': row.get('maintenance_groups_ar', ''),
            },
        )

        scalar_metrics = national_scalar_metrics(row)
        DailyMetric.objects.filter(report=report, dimension='').delete()
        for key, value in scalar_metrics.items():
            upsert_metric(report, key, value)

        report.governorate_loads.all().delete()
        for item in row.get('governorate_loads') or []:
            GovernorateLoad.objects.create(
                report=report,
                governorate_code=item['governorate_code'],
                consumed_mw=item['consumed_mw'],
                allocated_mw=item['allocated_mw'],
            )
            upsert_metric(report, 'gov_consumed_mw',
                          item['consumed_mw'], item['governorate_code'])
            upsert_metric(report, 'gov_allocated_mw',
                          item['allocated_mw'], item['governorate_code'])

        report.hydro_readings.all().delete()
        for item in row.get('hydro_readings') or []:
            HydroDamReading.objects.create(
                report=report,
                dam_code=item['dam_code'],
                front_level_m=item.get('front_level_m'),
                back_level_m=item.get('back_level_m'),
                generation_mwh=item.get('generation_mwh'),
                outflow_m3s=item.get('outflow_m3s'),
                inflow_m3s=item.get('inflow_m3s'),
                expected_m3s=item.get('expected_m3s'),
            )

        report.generation_incidents.all().delete()
        for item in row.get('generation_incidents') or []:
            GenerationIncident.objects.create(
                report=report,
                event_time=item.get('event_time', ''),
                description_ar=item['description_ar'],
                description_en=item.get('description_en', ''),
            )

        report.grid_incidents.all().delete()
        for item in row.get('grid_incidents') or []:
            GridLineIncident.objects.create(
                report=report,
                line_name=item.get('line_name', ''),
                voltage_kv=item.get('voltage_kv'),
                action_ar=item['action_ar'],
                action_en=item.get('action_en', ''),
            )

        report.fuel_tank_readings.all().delete()
        for item in row.get('fuel_tank_readings') or []:
            current = item.get('current_tons')
            max_cap = item.get('max_capacity_tons')
            if current is not None and (current <= 0 or current > 500_000):
                continue
            if max_cap is not None and max_cap > 500_000:
                max_cap = None
            FuelTankReading.objects.create(
                report=report,
                station_code=item['station_code'],
                current_tons=current,
                max_capacity_tons=max_cap,
            )

        report.generation_unit_readings.all().delete()
        for item in row.get('generation_unit_readings') or []:
            if _is_maintenance_unit(item):
                continue
            GenerationUnitReading.objects.create(
                report=report,
                plant_code=item['plant_code'],
                unit_code=item.get('unit_code', ''),
                nominal_mw=item.get('nominal_mw'),
                available_mw=item.get('available_mw'),
                generation_mwh_24h=item.get('generation_mwh_24h'),
                status=item.get(
                    'status', GenerationUnitReading.UnitStatus.ACTIVE),
            )

    return report


def build_report_detail_payload(report_date: date) -> dict[str, Any] | None:
    report = (
        DailyReport.objects.filter(report_date=report_date)
        .prefetch_related(
            'metrics',
            'governorate_loads',
            'hydro_readings',
            'fuel_tank_readings',
            'generation_unit_readings',
            'generation_incidents',
            'grid_incidents',
        )
        .first()
    )
    if not report:
        return None

    return {
        'report_date': report.report_date.isoformat(),
        'status': report.status,
        'reference_hour': report.reference_hour.isoformat() if report.reference_hour else None,
        'peak_generation_time': report.peak_generation_time.isoformat()
        if report.peak_generation_time
        else None,
        'notes_ar': report.notes_ar,
        'notes_en': report.notes_en,
        'maintenance_groups_ar': report.maintenance_groups_ar,
        'metrics': [
            {
                'metric_key': row.metric_key,
                'dimension': row.dimension,
                'value': _float(row.value),
                'unit': row.unit,
            }
            for row in report.metrics.filter(dimension='')
        ],
        'governorate_loads': [
            {
                'governorate_code': row.governorate_code,
                'consumed_mw': _float(row.consumed_mw),
                'allocated_mw': _float(row.allocated_mw),
            }
            for row in report.governorate_loads.all()
        ],
        'hydro_readings': [
            {
                'dam_code': row.dam_code,
                'front_level_m': _float(row.front_level_m) if row.front_level_m is not None else None,
                'back_level_m': _float(row.back_level_m) if row.back_level_m is not None else None,
                'generation_mwh': _float(row.generation_mwh) if row.generation_mwh is not None else None,
                'outflow_m3s': _float(row.outflow_m3s) if row.outflow_m3s is not None else None,
                'inflow_m3s': _float(row.inflow_m3s) if row.inflow_m3s is not None else None,
                'expected_m3s': _float(row.expected_m3s) if row.expected_m3s is not None else None,
            }
            for row in report.hydro_readings.all()
        ],
        'fuel_tank_readings': [
            {
                'station_code': row.station_code,
                'current_tons': _float(row.current_tons) if row.current_tons is not None else None,
                'max_capacity_tons': _float(row.max_capacity_tons)
                if row.max_capacity_tons is not None
                else None,
            }
            for row in report.fuel_tank_readings.all()
        ],
        'generation_unit_readings': [
            {
                'plant_code': row.plant_code,
                'unit_code': row.unit_code,
                'nominal_mw': _float(row.nominal_mw) if row.nominal_mw is not None else None,
                'available_mw': _float(row.available_mw) if row.available_mw is not None else None,
                'generation_mwh_24h': _float(row.generation_mwh_24h)
                if row.generation_mwh_24h is not None
                else None,
                'status': row.status,
            }
            for row in report.generation_unit_readings.all()
            if not _is_maintenance_reading(row)
        ],
        'generation_incidents': [
            {
                'event_time': row.event_time,
                'description_ar': row.description_ar,
                'description_en': row.description_en,
            }
            for row in report.generation_incidents.all()
        ],
        'grid_incidents': [
            {
                'line_name': row.line_name,
                'voltage_kv': row.voltage_kv,
                'action_ar': row.action_ar,
                'action_en': row.action_en,
            }
            for row in report.grid_incidents.all()
        ],
    }


def _apply_derived_metrics(report: DailyReport) -> None:
    metrics = _metric_map(report)
    received = _get_value(metrics, 'fuel_oil_received_tpd')
    consumed = _get_value(metrics, 'fuel_oil_consumed_tpd')
    if received is not None and consumed is not None:
        upsert_metric(report, 'fuel_oil_balance_tpd', received - consumed)

    reserve = _get_value(metrics, 'fuel_reserve_tons')
    if reserve is not None:
        from .report_catalog import NATIONAL_FUEL_RESERVE_CAPACITY_TONS

        upsert_metric(
            report,
            'fuel_reserve_pct',
            round(reserve / NATIONAL_FUEL_RESERVE_CAPACITY_TONS * 100, 1),
        )


def upsert_full_daily_report(data: dict[str, Any], *, user=None) -> DailyReport:
    report_date = data['report_date']
    with transaction.atomic():
        defaults: dict[str, Any] = {
            'status': data.get('status', DailyReport.Status.DRAFT),
            'reference_hour': data.get('reference_hour') or data.get('peak_generation_time'),
            'peak_generation_time': data.get('peak_generation_time'),
            'notes_ar': data.get('notes_ar', ''),
            'notes_en': data.get('notes_en', ''),
            'maintenance_groups_ar': data.get('maintenance_groups_ar', ''),
        }
        if user is not None:
            defaults['created_by'] = user

        report, _ = DailyReport.objects.update_or_create(
            report_date=report_date,
            defaults=defaults,
        )

        report.metrics.all().delete()
        for item in data.get('metrics') or []:
            if item.get('value') is None:
                continue
            upsert_metric(
                report,
                item['metric_key'],
                item['value'],
                item.get('dimension', ''),
                item.get('unit', ''),
            )

        report.governorate_loads.all().delete()
        for item in data.get('governorate_loads') or []:
            GovernorateLoad.objects.create(
                report=report,
                governorate_code=item['governorate_code'],
                consumed_mw=item.get('consumed_mw') or 0,
                allocated_mw=item.get('allocated_mw') or 0,
            )
            if item.get('consumed_mw') is not None:
                upsert_metric(report, 'gov_consumed_mw',
                              item['consumed_mw'], item['governorate_code'])
            if item.get('allocated_mw') is not None:
                upsert_metric(report, 'gov_allocated_mw',
                              item['allocated_mw'], item['governorate_code'])

        report.hydro_readings.all().delete()
        for item in data.get('hydro_readings') or []:
            HydroDamReading.objects.create(
                report=report,
                dam_code=item['dam_code'],
                front_level_m=item.get('front_level_m'),
                back_level_m=item.get('back_level_m'),
                generation_mwh=item.get('generation_mwh'),
                outflow_m3s=item.get('outflow_m3s'),
                inflow_m3s=item.get('inflow_m3s'),
                expected_m3s=item.get('expected_m3s'),
            )

        report.fuel_tank_readings.all().delete()
        for item in data.get('fuel_tank_readings') or []:
            FuelTankReading.objects.create(
                report=report,
                station_code=item['station_code'],
                current_tons=item.get('current_tons'),
                max_capacity_tons=item.get('max_capacity_tons'),
            )

        if 'generation_unit_readings' in data:
            report.generation_unit_readings.all().delete()
            for item in data.get('generation_unit_readings') or []:
                if _is_maintenance_unit(item):
                    continue
                GenerationUnitReading.objects.create(
                    report=report,
                    plant_code=item['plant_code'],
                    unit_code=item.get('unit_code', ''),
                    nominal_mw=item.get('nominal_mw'),
                    available_mw=item.get('available_mw'),
                    generation_mwh_24h=item.get('generation_mwh_24h'),
                    status=item.get(
                        'status', GenerationUnitReading.UnitStatus.ACTIVE),
                )

        report.generation_incidents.all().delete()
        for item in data.get('generation_incidents') or []:
            GenerationIncident.objects.create(
                report=report,
                event_time=item.get('event_time', ''),
                description_ar=item['description_ar'],
                description_en=item.get('description_en', ''),
            )

        report.grid_incidents.all().delete()
        for item in data.get('grid_incidents') or []:
            GridLineIncident.objects.create(
                report=report,
                line_name=item.get('line_name', ''),
                voltage_kv=item.get('voltage_kv'),
                action_ar=item['action_ar'],
                action_en=item.get('action_en', ''),
            )

        _apply_derived_metrics(report)

    return report


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

    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': [
            {'date': row.report.report_date.isoformat(), 'value': _float(row.value)}
            for row in rows
        ],
    }


def build_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    report = get_report_for_date(report_date)
    if not report:
        return _empty_dashboard_payload()

    metrics = _metric_map(report)
    previous = get_previous_report(report)
    prev_metrics = _metric_map(previous) if previous else {}

    kpis = [
        _build_kpi_row(spec_key, metrics, prev_metrics)
        for spec_key in _ordered_dashboard_kpi_keys()
    ]

    kpi_by_id = {row['id']: row for row in kpis}
    peak_time = report.peak_generation_time or report.reference_hour
    if peak_time and 'peak_generation_mw' in kpi_by_id:
        kpi_by_id['peak_generation_mw']['time'] = peak_time.strftime('%H:%M')

    kpi_groups = _build_kpi_groups(kpis)
    generation_incident_rows = [
        {
            'report_date': report.report_date.isoformat(),
            'event_time': row.event_time,
            'description_ar': row.description_ar,
            'description_en': row.description_en,
        }
        for row in report.generation_incidents.all()
    ]
    grid_incident_rows = [
        {
            'report_date': report.report_date.isoformat(),
            'line_name': row.line_name,
            'voltage_kv': row.voltage_kv,
            'action_ar': row.action_ar,
            'action_en': row.action_en,
        }
        for row in report.grid_incidents.all()
    ]
    maintenance_groups_ar = (report.maintenance_groups_ar or '').strip()
    maintenance_groups = _parse_maintenance_groups(maintenance_groups_ar)
    notes: list[dict[str, str]] = []
    if report.notes_ar or report.notes_en:
        notes.append({'ar': report.notes_ar, 'en': report.notes_en})

    return {
        'period': 'day',
        'month': None,
        'report_date': report.report_date.isoformat(),
        'anchor_date': report.report_date.isoformat(),
        'reports_count': 1,
        'days_covered': 1,
        'status': 'ready',
        'peak_generation_time': peak_time.strftime('%H:%M') if peak_time else None,
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'charts': {
            'governorate_load': _build_governorate_chart_from_reports([report]),
            'generation_mix': _build_generation_mix(metrics),
            'fuel_tanks': _build_fuel_tanks_chart(report),
            'hydro': [
                {
                    'dam_code': r.dam_code,
                    'front_level_m': _float(r.front_level_m) if r.front_level_m is not None else None,
                    'back_level_m': _float(r.back_level_m) if r.back_level_m is not None else None,
                    'generation_mwh': _float(r.generation_mwh) if r.generation_mwh is not None else None,
                    'outflow_m3s': _float(r.outflow_m3s) if r.outflow_m3s is not None else None,
                    'inflow_m3s': _float(r.inflow_m3s) if r.inflow_m3s is not None else None,
                    'expected_m3s': _float(r.expected_m3s) if r.expected_m3s is not None else None,
                }
                for r in report.hydro_readings.all()
            ],
            'maintenance_groups_ar': maintenance_groups_ar,
            'maintenance_groups': maintenance_groups,
        },
        'trends': {
            key: build_metric_trend(key, days=11, end_date=report.report_date)
            for key in TREND_METRICS
        },
        'alerts': _build_alerts(metrics),
        'notes': notes,
        'incidents': {
            'generation': generation_incident_rows,
            'grid': grid_incident_rows,
        },
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
    }


def build_monthly_dashboard_payload(year: int, month: int) -> dict[str, Any]:
    reports = _reports_for_month(year, month)
    if not reports:
        payload = _empty_dashboard_payload()
        payload.update({'period': 'month', 'month': f'{year}-{month:02d}'})
        return payload

    anchor_report = reports[-1]
    month_start, month_end = _month_bounds(year, month)
    metrics = _build_monthly_metric_map(reports)

    prev_year, prev_month = _previous_month(year, month)
    prev_reports = _reports_for_month(prev_year, prev_month)
    prev_metrics = _build_monthly_metric_map(
        prev_reports) if prev_reports else {}

    kpis = [
        _build_kpi_row(spec_key, metrics, prev_metrics)
        for spec_key in _ordered_dashboard_kpi_keys()
    ]
    kpi_groups = _build_kpi_groups(kpis)
    maintenance_groups_ar, maintenance_groups = _collect_monthly_maintenance(
        reports)
    incidents = _collect_monthly_incidents(reports)
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
        'peak_generation_time': None,
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'charts': {
            'governorate_load': _build_governorate_chart_from_reports(reports),
            'generation_mix': _build_generation_mix(metrics),
            'fuel_tanks': _build_fuel_tanks_chart(anchor_report),
            'hydro': _aggregate_hydro_rows(reports),
            'maintenance_groups_ar': maintenance_groups_ar,
            'maintenance_groups': maintenance_groups,
        },
        'trends': {
            key: build_metric_trend_for_range(
                key,
                start_date=month_start,
                end_date=month_end,
            )
            for key in TREND_METRICS
        },
        'alerts': _build_alerts(metrics),
        'notes': notes,
        'incidents': incidents,
        'available_dates': list_available_dates(),
        'available_months': list_available_months(),
    }
