"""
Oil & gas portal executive dashboard from accepted Info under
TitleCategory «إدارة قطاع البترول». Does not read DailyReport for display.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache
from typing import Any

from django.db import DatabaseError
from projects.alerts_info import list_info_alerts
from projects.display_models import (
    ReportDynamicFormsAttribute,
    ReportDynamicFormsInfo,
    ReportDynamicFormsTitle,
)
from projects.report_forms_read import ACCEPTED

from oil_gas.info_scope import (
    oil_gas_category_id_override,
    oil_gas_category_name,
)
from oil_gas.metric_catalog import (
    EXECUTIVE_KPI_GROUPS,
    EXECUTIVE_METRIC_KEYS,
    EXECUTIVE_TREND_METRICS,
    KPI_METRICS,
    METRIC_BY_KEY,
    MONTHLY_AGGREGATION,
    resolve_metric_labels,
)
from oil_gas.models import Field, Pipeline, Refinery
from oil_gas.target_catalog import TARGET_METRIC_BY_KEY
from oil_gas.target_resolver import achievement_pct, resolve_target_value, target_status

# Stable code assigned by report_moe's seed_oil_gas_daily_info_forms — never
# match a Title by its Arabic `name`, which is free-text and can be renamed at
# any time from the report_moe UI.
TITLE_NATIONAL = 'oil_gas.national'
TITLE_FIELD_ENTITY = 'oil_gas.field_entity'
TITLE_REFINERY_ENTITY = 'oil_gas.refinery_entity'


def _status_card(card_id, label_en, label_ar, value, status, detail_en='', detail_ar=''):
    return {
        'id': card_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'status': status,
        'detail_en': detail_en,
        'detail_ar': detail_ar,
    }


def _status_cards() -> list[dict[str, str]]:
    """Live infrastructure status counts (master-data models — read-only from moeds).

    Ported from the now-unreachable minister_dashboard.py::_status_cards, minus the
    "strategic stock" card (needs KpiDailySnapshot, which no live path feeds anymore).
    """
    total_fields = Field.objects.count()
    active_fields = Field.objects.filter(status=Field.Status.ACTIVE).count()
    shutdown_fields = Field.objects.filter(status=Field.Status.SHUTDOWN).count()

    total_refineries = Refinery.objects.count()
    operating_refineries = Refinery.objects.filter(status=Refinery.Status.OPERATING).count()

    total_pipelines = Pipeline.objects.count()
    normal_pipelines = Pipeline.objects.filter(status=Pipeline.Status.NORMAL).count()

    field_status = 'critical' if shutdown_fields else ('warning' if active_fields < total_fields else 'ok')
    refinery_status = 'critical' if operating_refineries < total_refineries else 'ok'
    pipeline_status = 'warning' if normal_pipelines < total_pipelines else 'ok'

    return [
        _status_card(
            'fields', 'Oil fields status', 'حالة الحقول',
            f'{active_fields}/{total_fields}', field_status,
            f'{shutdown_fields} shutdown' if shutdown_fields else 'All active',
            f'{shutdown_fields} متوقف' if shutdown_fields else 'جميعها عاملة',
        ),
        _status_card(
            'refineries', 'Refineries status', 'حالة المصافي',
            f'{operating_refineries}/{total_refineries}', refinery_status,
            'Operating units', 'وحدات عاملة',
        ),
        _status_card(
            'pipelines', 'Pipelines status', 'حالة الخطوط',
            f'{normal_pipelines}/{total_pipelines}', pipeline_status,
            'Normal operations', 'تشغيل طبيعي',
        ),
    ]


def _parse_number(value: str) -> float | None:
    text = str(value or '').strip().replace(',', '.')
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    text = str(value or '').strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


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


def _empty_payload(*, period: str = 'day', month: str | None = None) -> dict[str, Any]:
    return {
        'period': period,
        'month': month,
        'report_date': None,
        'status': 'empty',
        'view': 'executive',
        'source': 'dynamic_forms',
        'category_name': oil_gas_category_name(),
        'kpis': [],
        'kpi_groups': [],
        'status_cards': [],
        'charts': {},
        'trends': {},
        'alerts': [],
        'notes': [
            {
                'ar': 'لوحة النفط والغاز تعتمد على Info المقبول تحت فئة إدارة قطاع البترول.',
                'en': 'Petroleum dashboard uses accepted Info under the petroleum title category.',
            }
        ],
        'fields': _field_rows(),
        'refineries': _refinery_rows(),
        'available_dates': [],
        'available_months': [],
    }


@lru_cache(maxsize=1)
def _national_date_attr_ids() -> tuple[int, ...]:
    """Attribute ids carrying the "row date" cell for TITLE_NATIONAL.

    Cached: this is Form Builder *schema* (which attribute is the date cell), not
    report data — it only changes when someone reseeds the oil & gas forms.
    """
    try:
        title = ReportDynamicFormsTitle.objects.filter(code=TITLE_NATIONAL).first()
        if title is None:
            return ()
        return tuple(
            ReportDynamicFormsAttribute.objects
            .filter(title_id=title.id, type='date')
            .values_list('id', flat=True)
        )
    except DatabaseError:
        return ()


def _available_national_dates() -> list[str]:
    """Distinct report dates — a small, complete scan (bounded by the number of
    distinct dates ever reported, not by total row volume), so it never silently
    truncates like a "top N most-recent rows" cap would."""
    date_attr_ids = _national_date_attr_ids()
    if not date_attr_ids:
        return []
    try:
        values = (
            ReportDynamicFormsInfo.objects
            .filter(confirmed=ACCEPTED, attribute_id__in=date_attr_ids)
            .values_list('value', flat=True)
            .distinct()
            .iterator(chunk_size=2000)
        )
        dates = {v[:10] for v in values if v and len(v) >= 10 and v[4] == '-'}
    except DatabaseError:
        return []
    return sorted(dates, reverse=True)


def _row_keys_in_window(start_iso: str, end_iso: str) -> set[Any]:
    date_attr_ids = _national_date_attr_ids()
    if not date_attr_ids:
        return set()
    try:
        qs = (
            ReportDynamicFormsInfo.objects
            .filter(
                confirmed=ACCEPTED,
                attribute_id__in=date_attr_ids,
                value__gte=start_iso,
                value__lt=end_iso + '￿',
            )
            .values_list('row_key', flat=True)
        )
        return {rk for rk in qs.iterator(chunk_size=2000) if rk}
    except DatabaseError:
        return set()


def _load_attrs_and_infos(
    *, window_start: str | None = None, window_end: str | None = None
) -> tuple[
    list[ReportDynamicFormsInfo],
    dict[int, ReportDynamicFormsAttribute],
    dict[int, str],
]:
    """Facts bundle scoped to a calendar window when given, else a bounded fallback
    (last 400 days) — never "most recent N rows by insert time", which silently
    hides older data once this category's Info volume passes the row cap."""
    if window_start is None or window_end is None:
        today = date.today()
        window_end = today.isoformat()
        window_start = (today - timedelta(days=400)).isoformat()
    row_keys = _row_keys_in_window(window_start, window_end)
    if not row_keys:
        return [], {}, {}
    try:
        infos = list(
            ReportDynamicFormsInfo.objects.filter(
                row_key__in=row_keys, confirmed=ACCEPTED
            )
        )
    except DatabaseError:
        return [], {}, {}
    attr_ids = {r.attribute_id for r in infos}
    try:
        attrs = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(id__in=attr_ids)
        }
    except DatabaseError:
        attrs = {}
    title_ids = {a.title_id for a in attrs.values() if a.title_id}
    try:
        title_codes = {
            t.id: t.code
            for t in ReportDynamicFormsTitle.objects.filter(id__in=title_ids)
        }
    except DatabaseError:
        title_codes = {}
    return infos, attrs, title_codes


def _row_facts(
    infos: list[ReportDynamicFormsInfo],
    attrs: dict[int, ReportDynamicFormsAttribute],
) -> dict[str, dict[str, str]]:
    """row_key → { attr.key → value } for national title rows.

    Never keyed by `.label` — label is free-text Arabic display text editable
    from the report_moe UI at any time; `key` is the stable contract.
    """
    buckets: dict[str, dict[str, str]] = defaultdict(dict)
    for info in infos:
        attr = attrs.get(info.attribute_id)
        if attr is None or not info.row_key:
            continue
        rk = str(info.row_key)
        if attr.key:
            buckets[rk][attr.key] = str(info.value or '')
        if attr.type == 'date':
            buckets[rk]['_date'] = str(info.value or '')
    return buckets


def _facts_report_date(facts: dict[str, str]) -> date | None:
    return _parse_date(facts.get('_date', ''))


def _facts_metric_map(facts: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key in EXECUTIVE_METRIC_KEYS:
        num = _parse_number(facts.get(key, ''))
        if num is not None:
            out[key] = num
    return out


def _index_national_by_date(
    infos: list[ReportDynamicFormsInfo],
    attrs: dict[int, ReportDynamicFormsAttribute],
    title_names: dict[int, str],
) -> dict[date, dict[str, float]]:
    # Restrict to national title attributes. Not "or not title_names" / "or
    # infos" fallbacks — those silently treated "zero attributes matched the
    # national title" as "match everything", which is exactly backwards: a
    # title with genuinely no data in this batch must produce zero rows, not
    # every other title's data mislabeled as national (confirmed live on the
    # same bug pattern in water/geology's info_dashboard.py).
    national_attr_ids = {
        aid
        for aid, a in attrs.items()
        if title_names.get(a.title_id) == TITLE_NATIONAL
    }
    filtered = [i for i in infos if i.attribute_id in national_attr_ids]
    by_row = _row_facts(filtered, attrs)
    by_date: dict[date, dict[str, float]] = {}
    for facts in by_row.values():
        d = _facts_report_date(facts)
        if d is None:
            continue
        metrics = _facts_metric_map(facts)
        if metrics:
            by_date[d] = metrics
    return by_date


def list_info_available_dates(limit: int = 90) -> list[str]:
    return _available_national_dates()[:limit]


def list_info_available_months(limit: int = 24) -> list[str]:
    months: list[str] = []
    seen: set[str] = set()
    for d in list_info_available_dates(limit=500):
        month_key = d[:7]
        if month_key in seen:
            continue
        seen.add(month_key)
        months.append(month_key)
        if len(months) >= limit:
            break
    return months


def _build_kpi_rows(
    metrics: dict[str, float],
    prev_metrics: dict[str, float],
    report_date: date,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in sorted(KPI_METRICS, key=lambda s: s.kpi_order or 0):
        value = metrics.get(spec.key)
        prev_value = prev_metrics.get(spec.key)
        label_en, label_ar = resolve_metric_labels(spec, report_date)

        target_spec = TARGET_METRIC_BY_KEY.get(spec.key)
        higher = target_spec.higher_is_better if target_spec else True
        target_value = resolve_target_value(spec.key, report_date)
        achieve = achievement_pct(value, target_value, higher_is_better=higher) if target_value is not None else None
        # Only override the value-based status once an actual target is configured
        # for this metric/date — otherwise keep the existing kpi_status_rule reading.
        status = target_status(achieve, higher_is_better=higher) if achieve is not None else _kpi_status(spec.key, value)

        rows.append(
            {
                'id': spec.key,
                'label_en': label_en,
                'label_ar': label_ar,
                'value': value,
                'unit': spec.unit,
                'target_value': float(target_value) if target_value is not None else None,
                'achievement_pct': achieve,
                'delta_pct': _delta_pct(value, prev_value),
                'status': status,
            }
        )
    return rows


def _charts(metrics: dict[str, float]) -> dict[str, Any]:
    return {
        'clean_gas_mix': {
            'labels_en': ['Local production', 'Azerbaijan import', 'Jordan import'],
            'labels_ar': ['الإنتاج المحلي', 'استيراد أذربيجان', 'استيراد الأردن'],
            'values': [
                metrics.get('local_clean_gas_mm3') or 0,
                metrics.get('clean_gas_import_azerbaijan_mm3') or 0,
                metrics.get('clean_gas_import_jordan_mm3') or 0,
            ],
            'unit': 'M m³',
        },
        'fuel_sales': {
            'labels_en': ['Mazut', 'Gasoline 90+95', 'Domestic LPG', 'Fuel oil'],
            'labels_ar': ['مازوت', 'بنزين 90+95', 'غاز مسال منزلي', 'فيول'],
            'values': [
                metrics.get('mazut_sold_thu_fri_m3') or 0,
                metrics.get('gasoline_90_95_sold_thu_fri_m3') or 0,
                metrics.get('domestic_lpg_sold_m3') or 0,
                metrics.get('fuel_oil_sold_m3') or 0,
            ],
            'unit': 'm³',
        },
        'gas_distribution': {
            'labels_en': ['Distributed to consumers', 'Electricity sector'],
            'labels_ar': ['موزّع للمستهلكين', 'قطاع الكهرباء'],
            'values': [
                metrics.get('clean_gas_distributed_mm3') or 0,
                metrics.get('electricity_clean_gas_consumption_mm3') or 0,
            ],
            'unit': 'M m³',
        },
    }


def build_info_metric_trend(
    metric_key: str,
    *,
    days: int = 30,
    end_date: date | None = None,
) -> dict[str, Any]:
    spec = METRIC_BY_KEY.get(metric_key)
    if end_date is None:
        latest = _available_national_dates()
        if not latest:
            return {
                'metric_key': metric_key,
                'label_en': spec.label_en if spec else metric_key,
                'label_ar': spec.label_ar if spec else metric_key,
                'unit': spec.unit if spec else '',
                'points': [],
            }
        end_date = date.fromisoformat(latest[0])
    end = end_date
    start = end - timedelta(days=max(days - 1, 0))
    infos, attrs, titles = _load_attrs_and_infos(
        window_start=start.isoformat(), window_end=end.isoformat()
    )
    by_date = _index_national_by_date(infos, attrs, titles)
    if not by_date:
        return {
            'metric_key': metric_key,
            'label_en': spec.label_en if spec else metric_key,
            'label_ar': spec.label_ar if spec else metric_key,
            'unit': spec.unit if spec else '',
            'points': [],
        }
    points = []
    cursor = start
    while cursor <= end:
        if cursor in by_date and metric_key in by_date[cursor]:
            points.append(
                {'date': cursor.isoformat(), 'value': by_date[cursor][metric_key]}
            )
        cursor += timedelta(days=1)
    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': points,
    }


def build_info_dashboard_payload(report_date: date | None = None) -> dict[str, Any]:
    available_dates_all = _available_national_dates()
    available_months = list_info_available_months()
    if not available_dates_all:
        empty = _empty_payload(period='day')
        empty['available_dates'] = []
        empty['available_months'] = available_months
        return empty

    target_iso = (
        report_date.isoformat()
        if report_date and report_date.isoformat() in available_dates_all
        else available_dates_all[0]
    )
    target = date.fromisoformat(target_iso)
    available_dates = available_dates_all[:90]

    # 60-day buffer so "previous reporting date" resolves even across gaps.
    infos, attrs, titles = _load_attrs_and_infos(
        window_start=(target - timedelta(days=60)).isoformat(), window_end=target_iso
    )
    by_date = _index_national_by_date(infos, attrs, titles)
    if not by_date or target not in by_date:
        empty = _empty_payload(period='day')
        empty['available_dates'] = available_dates
        empty['available_months'] = available_months
        return empty

    metrics = by_date[target]
    prev_dates = [d for d in sorted(by_date.keys()) if d < target]
    prev_metrics = by_date[prev_dates[-1]] if prev_dates else {}

    kpis = _build_kpi_rows(metrics, prev_metrics, target)
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

    trends = {
        key: build_info_metric_trend(key, days=14, end_date=target)
        for key in EXECUTIVE_TREND_METRICS
    }
    alerts = list_info_alerts(
        oil_gas_category_name(),
        settings_id=oil_gas_category_id_override(),
        env_id_name='OIL_GAS_TITLE_CATEGORY_ID',
        on_date=target,
    )

    return {
        'report_date': target.isoformat(),
        'status': 'ready',
        'view': 'executive',
        'source': 'dynamic_forms',
        'category_name': oil_gas_category_name(),
        'period': 'day',
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'status_cards': _status_cards(),
        'charts': _charts(metrics),
        'trends': trends,
        'alerts': alerts,
        'notes': [],
        'fields': _field_rows(),
        'refineries': _refinery_rows(),
        'available_dates': available_dates,
        'available_months': available_months,
    }


@lru_cache(maxsize=8)
def _entity_title_attrs(title_code: str) -> dict[str, ReportDynamicFormsAttribute]:
    """Attributes of an entity-level title, keyed by `Attribute.key` only.

    Cached: schema changes only via report_moe seed commands, not per-request.
    Call `.cache_clear()` after re-running a seed_*_info_forms command in a
    long-lived process.
    """
    title = ReportDynamicFormsTitle.objects.filter(code=title_code).first()
    if title is None:
        return {}
    return {
        a.key: a
        for a in ReportDynamicFormsAttribute.objects.filter(title_id=title.id)
        if a.key
    }


def _latest_entity_readings(title_code: str) -> dict[int, dict[str, str]]:
    """entity_id -> facts of that entity's most recent row_key (by production_date).

    One query for the whole title (small: field/refinery entity data is a few
    hundred rows total), grouped in Python by (entity_id, row_key), then
    reduced to each entity's latest dated row.
    """
    by_key = _entity_title_attrs(title_code)
    key_by_attr = {a.id: k for k, a in by_key.items()}
    if not key_by_attr:
        return {}
    try:
        qs = ReportDynamicFormsInfo.objects.filter(
            confirmed=ACCEPTED, attribute_id__in=key_by_attr.keys(),
        )
        rows = qs.values_list('entity_id', 'row_key', 'attribute_id', 'value')
    except DatabaseError:
        return {}
    by_entity_rowkey: dict[int, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    for entity_id, row_key, attribute_id, value in rows:
        if entity_id is None:
            continue
        key = key_by_attr.get(attribute_id)
        if not key:
            continue
        by_entity_rowkey[int(entity_id)][str(row_key)][key] = value or ''
    latest: dict[int, dict[str, str]] = {}
    for entity_id, rowkeys in by_entity_rowkey.items():
        best_date = None
        best_facts = None
        for facts in rowkeys.values():
            d = _parse_date(facts.get('production_date', ''))
            if d is not None and (best_date is None or d > best_date):
                best_date = d
                best_facts = facts
        if best_facts:
            latest[entity_id] = best_facts
    return latest


def _field_rows() -> list[dict[str, Any]]:
    readings = _latest_entity_readings(TITLE_FIELD_ENTITY)
    rows: list[dict[str, Any]] = []
    for field in Field.objects.all():
        facts = readings.get(field.id)
        rows.append({
            'id': field.id,
            'code': field.code,
            'name_ar': field.name_ar,
            'name_en': field.name_en,
            'production_date': facts.get('production_date') if facts else None,
            'crude_oil_bbl': _parse_number(facts.get('crude_oil_bbl', '')) if facts else None,
            'natural_gas_mmscf': _parse_number(facts.get('natural_gas_mmscf', '')) if facts else None,
            'condensate_bbl': _parse_number(facts.get('condensate_bbl', '')) if facts else None,
            'water_cut_percent': _parse_number(facts.get('water_cut_percent', '')) if facts else None,
            'operating_hours': _parse_number(facts.get('operating_hours', '')) if facts else None,
        })
    rows.sort(key=lambda r: (r['crude_oil_bbl'] is None, -(r['crude_oil_bbl'] or 0)))
    return rows


def _refinery_rows() -> list[dict[str, Any]]:
    readings = _latest_entity_readings(TITLE_REFINERY_ENTITY)
    rows: list[dict[str, Any]] = []
    for refinery in Refinery.objects.all():
        facts = readings.get(refinery.id)
        rows.append({
            'id': refinery.id,
            'name_ar': refinery.name_ar or refinery.refinery_name,
            'name_en': refinery.refinery_name,
            'production_date': facts.get('production_date') if facts else None,
            'gasoline_ton': _parse_number(facts.get('gasoline_ton', '')) if facts else None,
            'diesel_ton': _parse_number(facts.get('diesel_ton', '')) if facts else None,
            'fuel_oil_ton': _parse_number(facts.get('fuel_oil_ton', '')) if facts else None,
            'lpg_ton': _parse_number(facts.get('lpg_ton', '')) if facts else None,
        })
    rows.sort(key=lambda r: (r['diesel_ton'] is None, -(r['diesel_ton'] or 0)))
    return rows


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


def build_info_monthly_dashboard_payload(year: int, month: int) -> dict[str, Any]:
    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_start = date(prev_year, prev_month, 1)

    # Window covers the previous month too — needed for the month-over-month delta.
    infos, attrs, titles = _load_attrs_and_infos(
        window_start=prev_start.isoformat(), window_end=month_end.isoformat()
    )
    by_date = _index_national_by_date(infos, attrs, titles)

    series: dict[str, list[float]] = defaultdict(list)
    for d, metrics in sorted(by_date.items()):
        if month_start <= d <= month_end:
            for key, value in metrics.items():
                series[key].append(value)

    if not series:
        empty = _empty_payload(period='month', month=f'{year}-{month:02d}')
        empty['available_dates'] = list_info_available_dates()
        empty['available_months'] = list_info_available_months()
        return empty

    metrics = {
        key: val
        for key, values in series.items()
        if (val := _aggregate_metric_values(values, MONTHLY_AGGREGATION.get(key, 'avg')))
        is not None
    }

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_start = date(prev_year, prev_month, 1)
    prev_end = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
    prev_series: dict[str, list[float]] = defaultdict(list)
    for d, m in by_date.items():
        if prev_start <= d <= prev_end:
            for key, value in m.items():
                prev_series[key].append(value)
    prev_metrics = {
        key: val
        for key, values in prev_series.items()
        if (val := _aggregate_metric_values(values, MONTHLY_AGGREGATION.get(key, 'avg')))
        is not None
    }

    anchor = month_end
    kpis = _build_kpi_rows(metrics, prev_metrics, anchor)
    kpi_by_id = {row['id']: row for row in kpis}
    kpi_groups = []
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

    alerts = list_info_alerts(
        oil_gas_category_name(),
        settings_id=oil_gas_category_id_override(),
        env_id_name='OIL_GAS_TITLE_CATEGORY_ID',
        on_date=anchor,
    )

    return {
        'period': 'month',
        'month': f'{year}-{month:02d}',
        'report_date': anchor.isoformat(),
        'status': 'ready',
        'view': 'executive',
        'source': 'dynamic_forms',
        'category_name': oil_gas_category_name(),
        'kpis': kpis,
        'kpi_groups': kpi_groups,
        'status_cards': _status_cards(),
        'charts': _charts(metrics),
        'trends': {},
        'alerts': alerts,
        'notes': [],
        'available_dates': list_info_available_dates(),
        'available_months': list_info_available_months(),
    }
