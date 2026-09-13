"""
Electricity portal dashboard built from accepted Info under TitleCategory
«إدارة قطاع الكهرباء». Does not read DailyReport.
"""

from __future__ import annotations

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

from electricity.info_catalog import ENTITY_ATTR_TYPES
from electricity.info_scope import (
    electricity_category_id_override,
    electricity_category_name,
)
from electricity.metric_catalog import KPI_GROUP_LABEL_OVERRIDES, KPI_GROUPS, METRIC_BY_KEY
from electricity.operational_models import (
    FuelTankStation,
    HydroDam,
    LoadGovernorate,
    OperationalTarget,
    PowerPlant,
    Substation,
    TransmissionLine,
)
from electricity.target_resolver import achievement_pct, resolve_target_value, target_status

# Stable codes assigned by report_moe's seed_electricity_daily_info_forms —
# never match a Title by its Arabic `name`, which is free-text and can be
# renamed at any time from the report_moe UI.
TITLE_NATIONAL = 'electricity.national'
TITLE_UNITS = 'electricity.unit_entity'
TITLE_PLANT = 'electricity.plant_entity'
TITLE_FUEL = 'electricity.fuel_tank_entity'
TITLE_GOV = 'electricity.governorate_load_entity'
TITLE_HYDRO = 'electricity.hydro_dam_entity'
TITLE_INC_GEN = 'electricity.generation_incident'
TITLE_INC_GRID = 'electricity.grid_incident'
TITLE_NOTES = 'electricity.daily_notes'

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
    grid-balance card (that one needs KpiDailySnapshot, which no live path feeds
    anymore).
    """
    total_plants = PowerPlant.objects.count()
    active_plants = PowerPlant.objects.filter(status=PowerPlant.Status.ACTIVE).count()
    shutdown_plants = PowerPlant.objects.filter(status=PowerPlant.Status.SHUTDOWN).count()
    maintenance_plants = PowerPlant.objects.filter(status=PowerPlant.Status.MAINTENANCE).count()

    total_lines = TransmissionLine.objects.count()
    normal_lines = TransmissionLine.objects.filter(status=TransmissionLine.Status.NORMAL).count()

    total_subs = Substation.objects.count()
    active_subs = Substation.objects.filter(status=Substation.Status.ACTIVE).count()

    plant_status = 'critical' if shutdown_plants else ('warning' if active_plants < total_plants else 'ok')
    line_status = 'warning' if normal_lines < total_lines else 'ok'
    sub_status = 'warning' if active_subs < total_subs else 'ok'

    return [
        _status_card(
            'plants', 'Active plants', 'محطات عاملة',
            f'{active_plants}/{total_plants}', plant_status,
            f'{shutdown_plants} shutdown, {maintenance_plants} maintenance' if shutdown_plants or maintenance_plants else 'All operational',
            f'{shutdown_plants} متوقف، {maintenance_plants} صيانة' if shutdown_plants or maintenance_plants else 'جميعها جاهزة',
        ),
        _status_card(
            'transmission', 'Transmission lines', 'خطوط النقل',
            f'{normal_lines}/{total_lines}', line_status,
            'Normal operations', 'تشغيل طبيعي',
        ),
        _status_card(
            'substations', 'Substations', 'محطات التحويل',
            f'{active_subs}/{total_subs}', sub_status,
            'Grid nodes', 'عقد الشبكة',
        ),
    ]


def _kpi_status(spec_key: str, value: float | None) -> str:
    """Value-based status rule (ported from services.py — used as fallback when no
    numeric target is configured for this metric/date)."""
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


# Flat (id, label_en, label_ar, unit) tuples, ordered/grouped per metric_catalog's
# KPI_GROUPS (the same grouping production's dashboard renders as separate sections),
# de-duplicated so a metric appearing in >1 group is only requested/computed once.
KPI_SPECS: list[tuple[str, str, str, str]] = []
_seen_kpi_keys: set[str] = set()
for _group_id, _group_en, _group_ar, _group_keys in KPI_GROUPS:
    for _key in _group_keys:
        if _key in _seen_kpi_keys:
            continue
        _spec = METRIC_BY_KEY.get(_key)
        if not _spec:
            continue
        _seen_kpi_keys.add(_key)
        label_en, label_ar = KPI_GROUP_LABEL_OVERRIDES.get(
            (_group_id, _key), (_spec.label_en, _spec.label_ar)
        )
        KPI_SPECS.append((_key, label_en, label_ar, _spec.unit))

TREND_KEYS = (
    'peak_generation_mw',
    'net_generation_mwh',
    'total_generation_mwh_24h',
    'steam_generation_mwh',
    'fuel_reserve_tons',
    'fuel_reserve_pct',
    'gas_import_mm3d',
    'available_generated_power',
    'gov_excess_mw',
)


def _parse_number(value: str) -> float | None:
    text = str(value or '').strip().replace(',', '.')
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fact_get(facts: dict[str, str], *candidates: str) -> str:
    """Resolve a fact by key/label aliases (seed labels vary with/without units)."""
    for name in candidates:
        if not name:
            continue
        if name in facts and str(facts[name] or '').strip() != '':
            return facts[name]
    for name in candidates:
        if name in facts:
            return facts.get(name) or ''
    return ''


def _fact_number(facts: dict[str, str], *candidates: str) -> float | None:
    return _parse_number(_fact_get(facts, *candidates))


def _empty_info_dashboard(*, period: str = 'day', month: str | None = None) -> dict[str, Any]:
    return {
        'period': period,
        'month': month,
        'report_date': None,
        'anchor_date': None,
        'reports_count': 0,
        'days_covered': 0,
        'status': 'empty',
        'source': 'dynamic_forms',
        'category_name': electricity_category_name(),
        'peak_generation_time': None,
        'kpis': [],
        'kpi_groups': [],
        'status_cards': [],
        'charts': {
            'generation_mix': {'labels_en': [], 'labels_ar': [], 'values': []},
            'generation_units': [],
            'governorate_load': {
                'labels_en': [],
                'labels_ar': [],
                'consumed': [],
                'allocated': [],
            },
            'fuel_tanks': None,
            'hydro': [],
            'maintenance_groups_ar': '',
            'maintenance_groups': [],
        },
        'trends': {},
        'alerts': [],
        'notes': [
            {
                'ar': 'لوحة الكهرباء تعتمد على Info المقبول تحت فئة إدارة قطاع الكهرباء.',
                'en': 'Electricity dashboard uses accepted Info under the electricity title category.',
            }
        ],
        'incidents': {'generation': [], 'grid': [], 'by_day': []},
        'available_dates': [],
        'available_months': [],
    }


_CALENDAR_TITLES = (
    TITLE_NATIONAL, TITLE_NOTES, TITLE_FUEL, TITLE_GOV,
    TITLE_HYDRO, TITLE_INC_GEN, TITLE_INC_GRID, TITLE_UNITS,
)


@lru_cache(maxsize=8)
def _date_attr_ids_for_titles(title_codes: tuple[str, ...]) -> tuple[int, ...]:
    """Attribute ids that carry the "row date" cell for the given titles.

    Matched by `type='date'`, not by key/label text — every seeded title has
    exactly one date attribute regardless of what its key is named
    (`report_date` vs `reading_date` vs `update_date`).

    Cached: this maps to Form Builder *schema* (which attribute is the date cell),
    not report data — it only changes when someone reseeds the electricity forms.
    """
    try:
        title_ids = list(
            ReportDynamicFormsTitle.objects
            .filter(code__in=title_codes)
            .values_list('id', flat=True)
        )
        if not title_ids:
            return ()
        return tuple(
            ReportDynamicFormsAttribute.objects
            .filter(title_id__in=title_ids, type='date')
            .values_list('id', flat=True)
        )
    except DatabaseError:
        return ()


def _available_calendar(title_names: tuple[str, ...]) -> list[str]:
    """Distinct report dates for the given titles — a small, complete scan (bounded
    by the number of distinct dates ever reported, not by total row volume), so it
    never silently truncates like a "top N most-recent rows" cap would."""
    date_attr_ids = _date_attr_ids_for_titles(title_names)
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


def _row_keys_in_window(title_names: tuple[str, ...], start_iso: str, end_iso: str) -> set[Any]:
    """row_keys whose date cell (for any of `title_names`) falls in [start_iso, end_iso]."""
    date_attr_ids = _date_attr_ids_for_titles(title_names)
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


def _load_bundle_for_row_keys(row_keys: set[Any]) -> tuple[
    list[ReportDynamicFormsInfo],
    dict[int, ReportDynamicFormsAttribute],
    dict[int, str],
    dict[str, tuple[str, int]],
]:
    if not row_keys:
        return [], {}, {}, {}
    try:
        all_rows = list(
            ReportDynamicFormsInfo.objects.filter(
                row_key__in=row_keys, confirmed=ACCEPTED
            )
        )
    except DatabaseError:
        return [], {}, {}, {}

    entity_by_row_key: dict[str, tuple[str, int]] = {
        str(r.row_key): (r.entity_type, int(r.entity_id))
        for r in all_rows
        if r.row_key and r.entity_type and r.entity_id is not None
    }
    attr_ids = {r.attribute_id for r in all_rows}
    try:
        attrs = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(id__in=attr_ids)
        }
    except DatabaseError:
        attrs = {}
    title_ids = {a.title_id for a in attrs.values() if a.title_id}
    try:
        titles = {
            t.id: t.code
            for t in ReportDynamicFormsTitle.objects.filter(id__in=title_ids)
        }
    except DatabaseError:
        titles = {}
    return all_rows, attrs, titles, entity_by_row_key


def _load_bundle(
    *, window_start: str | None = None, window_end: str | None = None
) -> tuple[
    list[ReportDynamicFormsInfo],
    dict[int, ReportDynamicFormsAttribute],
    dict[int, str],
    dict[str, tuple[str, int]],
]:
    """Facts bundle scoped to a calendar window when given, else a bounded fallback
    (last 400 days) — never "most recent N rows by insert time", which silently
    hides older data once a category's Info volume passes the row cap (exactly
    what happened to the water dashboards before they were rewritten this way)."""
    if window_start is None or window_end is None:
        today = date.today()
        window_end = today.isoformat()
        window_start = (today - timedelta(days=400)).isoformat()
    row_keys = _row_keys_in_window(_CALENDAR_TITLES, window_start, window_end)
    return _load_bundle_for_row_keys(row_keys)


def _row_facts(
    rows: list[ReportDynamicFormsInfo],
    attrs: dict[int, ReportDynamicFormsAttribute],
) -> dict[str, str]:
    """Latest value per attribute, keyed by `Attribute.key` only.

    Never keyed by `.label` — label is free-text Arabic display text editable
    from the report_moe UI at any time; `key` is the stable contract. Also
    stamps a synthetic `_date` slot for whichever attribute is `type='date'`,
    regardless of that attribute's own key name (`report_date` vs
    `reading_date` vs `update_date` across titles).
    """
    latest: dict[int, ReportDynamicFormsInfo] = {}
    for r in sorted(rows, key=lambda x: (-(x.created_at.timestamp() if x.created_at else 0), -x.id)):
        if r.attribute_id not in latest:
            latest[r.attribute_id] = r
    out: dict[str, str] = {}
    for attr_id, info in latest.items():
        attr = attrs.get(attr_id)
        if not attr:
            continue
        if (attr.type or '') in ENTITY_ATTR_TYPES:
            continue
        value = info.value
        key = (attr.key or '').strip()
        if key:
            out[key] = value
        if attr.type == 'date':
            out['_date'] = value
    return out


def _group_by_title_rowkey(
    all_rows: list[ReportDynamicFormsInfo],
    attrs: dict[int, ReportDynamicFormsAttribute],
    titles: dict[int, str],
    entity_by_row_key: dict[str, tuple[str, int]],
) -> dict[str, list[dict[str, Any]]]:
    """title_code -> list of {facts, entity_type, entity_id, row_key, report_date}"""
    buckets: dict[tuple[str, str], list[ReportDynamicFormsInfo]] = defaultdict(list)
    for row in all_rows:
        attr = attrs.get(row.attribute_id)
        if not attr or not attr.title_id:
            continue
        title_code = titles.get(attr.title_id, '')
        rk = str(row.row_key) if row.row_key else f'id-{row.id}'
        buckets[(title_code, rk)].append(row)

    by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (title_code, rk), rows in buckets.items():
        facts = _row_facts(rows, attrs)
        report_date = str(facts.get('_date') or '').strip()[:10]
        if rows[0].entity_type and rows[0].entity_id is not None:
            et, eid = rows[0].entity_type, int(rows[0].entity_id)
        elif rk in entity_by_row_key:
            et, eid = entity_by_row_key[rk]
        else:
            et, eid = '', None
        by_title[title_code].append(
            {
                'facts': facts,
                'entity_type': et,
                'entity_id': eid,
                'row_key': rk if not rk.startswith('id-') else None,
                'report_date': report_date,
            }
        )
    return by_title


def _filter_day_month(
    items: list[dict[str, Any]],
    *,
    period: str,
    report_date: date | None,
    month: str | None,
) -> list[dict[str, Any]]:
    if period == 'month':
        if not month:
            return []
        return [i for i in items if (i.get('report_date') or '').startswith(month)]
    if period == 'day' and report_date:
        target = report_date.isoformat()
        return [i for i in items if i.get('report_date') == target]
    return items


def _items_on_date(items: list[dict[str, Any]], day: str | None) -> list[dict[str, Any]]:
    if not day:
        return []
    return [i for i in items if i.get('report_date') == day]


def _pick_anchor_date(
    by_title: dict[str, list[dict[str, Any]]],
    *,
    period: str,
    report_date: date | None,
    month: str | None,
) -> str | None:
    if period == 'day' and report_date:
        return report_date.isoformat()
    dates: set[str] = set()
    for items in by_title.values():
        for item in items:
            d = item.get('report_date') or ''
            if len(d) >= 10 and d[4] == '-':
                if period == 'month' and month and not d.startswith(month):
                    continue
                dates.add(d[:10])
    if not dates:
        return None
    return sorted(dates, reverse=True)[0]


def _aggregate_values(values: list[float], rule: str) -> float | None:
    if not values:
        return None
    if rule == 'sum':
        return sum(values)
    if rule == 'max':
        return max(values)
    if rule == 'last':
        return values[-1]
    return sum(values) / len(values)


def _aggregate_national_facts(items: list[dict[str, Any]]) -> dict[str, str]:
    """Monthly national metrics using the same rules as DailyReport aggregation."""
    from electricity.metric_catalog import MONTHLY_AGGREGATION

    series: dict[str, list[float]] = defaultdict(list)
    for item in sorted(items, key=lambda x: x.get('report_date') or ''):
        for key, raw in item.get('facts', {}).items():
            if key.startswith('_'):
                continue
            num = _parse_number(raw)
            if num is not None:
                series[key].append(num)
    out: dict[str, str] = {}
    for key, values in series.items():
        rule = MONTHLY_AGGREGATION.get(key, 'avg')
        agg = _aggregate_values(values, rule)
        if agg is not None:
            out[key] = str(agg)
    return out


def _sum_gov_chart(
    items: list[dict[str, Any]],
    gov_cache: dict[int, Any],
) -> tuple[list[str], list[str], list[float], list[float]]:
    consumed_by: dict[int, float] = defaultdict(float)
    allocated_by: dict[int, float] = defaultdict(float)
    for item in items:
        eid = item.get('entity_id')
        if eid is None or eid not in gov_cache:
            continue
        facts = item['facts']
        consumed_by[eid] += _fact_number(facts, 'المستهلك (ميجاواط)', 'المستهلك', 'consumed_mw') or 0
        allocated_by[eid] += _fact_number(facts, 'المخصّص (ميجاواط)', 'المخصّص', 'allocated_mw') or 0
    g_en, g_ar, consumed, allocated = [], [], [], []
    for eid in sorted(consumed_by.keys() | allocated_by.keys(), key=lambda i: gov_cache[i].code):
        gov = gov_cache[eid]
        g_en.append(gov.name_en or gov.code)
        g_ar.append(gov.name_ar or gov.code)
        consumed.append(consumed_by.get(eid, 0))
        allocated.append(allocated_by.get(eid, 0))
    return g_en, g_ar, consumed, allocated


def _aggregate_hydro_chart(
    items: list[dict[str, Any]],
    dam_cache: dict[int, Any],
) -> list[dict[str, Any]]:
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
    for item in items:
        dam = dam_cache.get(item.get('entity_id'))
        code = dam.code if dam else str(item.get('entity_id') or '')
        facts = item['facts']
        bucket = buckets[code]
        for field, labels, _rule in (
            ('front_level_m', ('المنسوب الأمامي (م)', 'المنسوب الأمامي', 'front_level_m'), 'avg'),
            ('back_level_m', ('المنسوب الخلفي (م)', 'المنسوب الخلفي', 'back_level_m'), 'avg'),
            ('generation_mwh', ('التوليد (ميجاواط ساعة)', 'التوليد', 'generation_mwh'), 'sum'),
            ('outflow_m3s', ('التصريف (م3/ث)', 'التصريف', 'outflow_m3s'), 'avg'),
            ('inflow_m3s', ('الوارد (م3/ث)', 'الوارد', 'inflow_m3s'), 'avg'),
            ('expected_m3s', ('المتوقع (م3/ث)', 'المتوقع', 'expected_m3s'), 'avg'),
        ):
            num = _fact_number(facts, *labels)
            if num is not None:
                bucket[field].append(num)
    rows = []
    for dam_code, values in buckets.items():
        rows.append(
            {
                'dam_code': dam_code,
                'front_level_m': _aggregate_values(values['front_level_m'], 'avg'),
                'back_level_m': _aggregate_values(values['back_level_m'], 'avg'),
                'generation_mwh': _aggregate_values(values['generation_mwh'], 'sum'),
                'outflow_m3s': _aggregate_values(values['outflow_m3s'], 'avg'),
                'inflow_m3s': _aggregate_values(values['inflow_m3s'], 'avg'),
                'expected_m3s': _aggregate_values(values['expected_m3s'], 'avg'),
            }
        )
    return rows


def _collect_month_notes_maintenance(
    notes_items: list[dict[str, Any]],
    *,
    anchor: str | None,
) -> tuple[list[dict[str, str]], str, str | None]:
    notes: list[dict[str, str]] = []
    seen_notes: set[tuple[str, str]] = set()
    maint_lines: list[str] = []
    seen_maint: set[str] = set()
    peak_time = None
    for item in sorted(notes_items, key=lambda x: x.get('report_date') or ''):
        nf = item['facts']
        if item.get('report_date') == anchor and nf.get('peak_generation_time'):
            peak_time = nf.get('peak_generation_time')
        for line in (nf.get('maintenance_groups') or '').replace('\r', '\n').split('\n'):
            text = line.strip()
            if text and text not in seen_maint:
                seen_maint.add(text)
                maint_lines.append(text)
        ar = nf.get('notes_ar') or ''
        en = nf.get('notes_en') or ''
        if (ar or en) and (ar, en) not in seen_notes:
            seen_notes.add((ar, en))
            notes.append({'ar': ar, 'en': en})
    if peak_time is None and notes_items:
        peak_time = notes_items[-1]['facts'].get('peak_generation_time') or None
    return notes, '\n'.join(maint_lines), peak_time


def build_info_metric_trend(
    metric_key: str,
    *,
    days: int = 30,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Trend points from accepted national Info only (no DailyMetric)."""
    try:
        from electricity.metric_catalog import METRIC_BY_KEY
    except ImportError:  # pragma: no cover
        METRIC_BY_KEY = {}
    spec = METRIC_BY_KEY.get(metric_key)
    empty = {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': [],
    }
    all_rows, attrs, titles, entity_by_row_key = _load_bundle()
    if not all_rows:
        return empty
    by_title = _group_by_title_rowkey(all_rows, attrs, titles, entity_by_row_key)
    national_by_date: dict[date, dict[str, str]] = {}
    for item in by_title.get(TITLE_NATIONAL, []):
        raw = (item.get('report_date') or '')[:10]
        if len(raw) < 10:
            continue
        try:
            d = date.fromisoformat(raw)
        except ValueError:
            continue
        national_by_date[d] = item.get('facts') or {}
    if not national_by_date:
        return empty
    end = end_date if end_date and end_date in national_by_date else max(national_by_date.keys())
    start = end - timedelta(days=max(days - 1, 0))
    points: list[dict[str, Any]] = []
    cursor = start
    while cursor <= end:
        facts = national_by_date.get(cursor)
        if facts:
            value = _parse_number(facts.get(metric_key, ''))
            if value is None:
                # also try Arabic label from KPI_SPECS
                for key, _en, label_ar, _unit in KPI_SPECS:
                    if key == metric_key:
                        value = _parse_number(facts.get(label_ar, ''))
                        break
            if value is not None:
                points.append({'date': cursor.isoformat(), 'value': value})
        cursor += timedelta(days=1)
    return {
        'metric_key': metric_key,
        'label_en': spec.label_en if spec else metric_key,
        'label_ar': spec.label_ar if spec else metric_key,
        'unit': spec.unit if spec else '',
        'points': points,
    }


def _fmt_hm_to_iso_time(value: str | None) -> str | None:
    """'HH:MM' (as stamped by migrate_electricity_daily_to_info._migrate_notes,
    which writes `time.strftime('%H:%M')`) -> 'HH:MM:SS' matching the legacy
    contract's `TimeField.isoformat()` output."""
    text = str(value or '').strip()
    if not text:
        return None
    parts = text.split(':')
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return None
    return f'{hour:02d}:{minute:02d}:{second:02d}'


def build_info_report_detail_payload(report_date: date) -> dict[str, Any] | None:
    """Same exact shape as electricity.services.build_report_detail_payload,
    sourced from accepted Info instead of the legacy DailyReport/DailyMetric
    tables. Used by report_export.py / report_pdf.py (the formal Excel export
    and ministerial-letter PDF) — do not change field names/shape without
    updating both consumers.
    """
    date_s = report_date.isoformat()
    row_keys = _row_keys_in_window(_CALENDAR_TITLES, date_s, date_s)
    if not row_keys:
        return None
    all_rows, attrs, titles, entity_by_row_key = _load_bundle_for_row_keys(row_keys)
    if not all_rows:
        return None
    by_title = _group_by_title_rowkey(all_rows, attrs, titles, entity_by_row_key)

    national_items = _items_on_date(by_title.get(TITLE_NATIONAL, []), date_s)
    if not national_items:
        return None
    national_facts = national_items[0]['facts']

    from electricity.metric_catalog import METRIC_BY_KEY

    metrics = []
    for key, raw in national_facts.items():
        # '_date' is the synthetic date-cell slot _row_facts stamps; 'report_date'
        # is the same date attribute's own `key` (its Attribute.key in Info's
        # national title) — neither is a metric row in the legacy contract.
        if key.startswith('_') or key == 'report_date':
            continue
        val = _parse_number(raw)
        if val is None:
            continue
        spec = METRIC_BY_KEY.get(key)
        metrics.append(
            {
                'metric_key': key,
                'dimension': '',
                'value': val,
                'unit': spec.unit if spec else '',
            }
        )

    notes_items = _items_on_date(by_title.get(TITLE_NOTES, []), date_s)
    notes_facts = notes_items[0]['facts'] if notes_items else {}

    governorate_loads = []
    gov_cache = {g.id: g for g in LoadGovernorate.objects.all()}
    for item in _items_on_date(by_title.get(TITLE_GOV, []), date_s):
        gov = gov_cache.get(item.get('entity_id'))
        f = item['facts']
        governorate_loads.append(
            {
                'governorate_code': gov.code if gov else str(item.get('entity_id') or ''),
                'consumed_mw': _fact_number(f, 'المستهلك (ميجاواط)', 'المستهلك', 'consumed_mw'),
                'allocated_mw': _fact_number(f, 'المخصّص (ميجاواط)', 'المخصّص', 'allocated_mw'),
            }
        )

    hydro_readings = []
    dam_cache = {d.id: d for d in HydroDam.objects.all()}
    for item in _items_on_date(by_title.get(TITLE_HYDRO, []), date_s):
        dam = dam_cache.get(item.get('entity_id'))
        f = item['facts']
        hydro_readings.append(
            {
                'dam_code': dam.code if dam else str(item.get('entity_id') or ''),
                'front_level_m': _fact_number(
                    f, 'المنسوب الأمامي (م)', 'المنسوب الأمامي', 'front_level_m'
                ),
                'back_level_m': _fact_number(
                    f, 'المنسوب الخلفي (م)', 'المنسوب الخلفي', 'back_level_m'
                ),
                'generation_mwh': _fact_number(
                    f, 'التوليد (ميجاواط ساعة)', 'التوليد', 'generation_mwh'
                ),
                'outflow_m3s': _fact_number(f, 'التصريف (م3/ث)', 'التصريف', 'outflow_m3s'),
                'inflow_m3s': _fact_number(f, 'الوارد (م3/ث)', 'الوارد', 'inflow_m3s'),
                'expected_m3s': _fact_number(f, 'المتوقع (م3/ث)', 'المتوقع', 'expected_m3s'),
            }
        )

    fuel_tank_readings = []
    tank_cache = {t.id: t for t in FuelTankStation.objects.all()}
    for item in _items_on_date(by_title.get(TITLE_FUEL, []), date_s):
        tank = tank_cache.get(item.get('entity_id'))
        f = item['facts']
        cur = _fact_number(f, 'المخزون الحالي (طن)', 'المخزون الحالي', 'current_stock_tons')
        # max_capacity_tons was a per-report snapshot in legacy FuelTankReading
        # (it drifts date-to-date and does NOT track FuelTankStation's master
        # max_capacity_tons — verified against real data). The migration never
        # copied it (fuel_tank_entity's TITLE_SPEC has no such attribute), so
        # it's a genuine gap here: None rather than a wrong number pulled from
        # master data. Nothing downstream (report_export.py/report_pdf.py)
        # reads fuel_tank_readings[].max_capacity_tons — only the
        # 'fuel_tank_max_capacity_tons' national metric is used for that sheet
        # cell, and that one comes from `metrics` (verified to match exactly).
        fuel_tank_readings.append(
            {
                'station_code': tank.code if tank else str(item.get('entity_id') or ''),
                'current_tons': cur,
                'max_capacity_tons': None,
            }
        )

    generation_unit_readings = []
    plant_cache = {p.id: p for p in PowerPlant.objects.all()}
    unit_source = list(by_title.get(TITLE_UNITS, [])) + list(by_title.get(TITLE_PLANT, []))
    for item in _items_on_date(unit_source, date_s):
        plant = plant_cache.get(item.get('entity_id'))
        f = item['facts']
        plant_code = plant.code if plant else str(item.get('entity_id') or '')
        status = _fact_get(f, 'الحالة', 'status') or ''
        if status == 'maintenance' or plant_code == 'maintenance':
            continue
        generation_unit_readings.append(
            {
                'plant_code': plant_code,
                'unit_code': _fact_get(f, 'رمز الوحدة', 'unit_code') or '',
                'nominal_mw': _fact_number(
                    f, 'القدرة الاسمية (ميجاواط)', 'القدرة الاسمية', 'nominal_mw'
                ),
                'available_mw': _fact_number(f, 'المتاح (ميجاواط)', 'المتاح', 'available_mw'),
                'generation_mwh_24h': _fact_number(
                    f,
                    'التوليد 24س (ميجاواط ساعة)',
                    'التوليد (ميجاواط ساعة)',
                    'التوليد',
                    'generation_mwh',
                ),
                'status': status,
            }
        )

    generation_incidents = []
    for item in _items_on_date(by_title.get(TITLE_INC_GEN, []), date_s):
        f = item['facts']
        generation_incidents.append(
            {
                'event_time': f.get('event_time') or '',
                'description_ar': f.get('description_ar') or '',
                'description_en': f.get('description_en') or '',
            }
        )

    grid_incidents = []
    for item in _items_on_date(by_title.get(TITLE_INC_GRID, []), date_s):
        f = item['facts']
        grid_incidents.append(
            {
                'line_name': f.get('line_name') or '',
                'voltage_kv': _parse_number(f.get('voltage_kv', '')),
                'action_ar': f.get('action_ar') or '',
                'action_en': f.get('action_en') or '',
            }
        )

    return {
        'report_date': date_s,
        'status': 'published',
        'reference_hour': _fmt_hm_to_iso_time(notes_facts.get('reference_hour')),
        'peak_generation_time': _fmt_hm_to_iso_time(notes_facts.get('peak_generation_time')),
        'notes_ar': notes_facts.get('notes_ar') or '',
        'notes_en': notes_facts.get('notes_en') or '',
        'maintenance_groups_ar': notes_facts.get('maintenance_groups') or '',
        'metrics': metrics,
        'governorate_loads': governorate_loads,
        'hydro_readings': hydro_readings,
        'fuel_tank_readings': fuel_tank_readings,
        'generation_unit_readings': generation_unit_readings,
        'generation_incidents': generation_incidents,
        'grid_incidents': grid_incidents,
    }


def build_info_dashboard_payload(
    *,
    period: str = 'day',
    report_date: date | None = None,
    month: str | None = None,
) -> dict[str, Any]:
    # Cheap calendar scan first (bounded by distinct report dates, not row volume —
    # never silently drops old dates the way a "top N rows" cap would). This decides
    # which calendar window we then need to fully load.
    national_dates = _available_calendar((TITLE_NATIONAL,))
    sorted_dates = national_dates or _available_calendar(_CALENDAR_TITLES)
    if not sorted_dates:
        return _empty_info_dashboard(period=period, month=month)
    calendar_dates = set(sorted_dates)
    sorted_months = sorted({d[:7] for d in calendar_dates}, reverse=True)

    # Monthly view must always resolve a concrete YYYY-MM (latest if omitted).
    if period == 'month' and not month:
        month = sorted_months[0] if sorted_months else None

    if period == 'day' and report_date is not None:
        # If the requested day has no daily-report Info, fall back to latest calendar day.
        if report_date.isoformat() not in calendar_dates and sorted_dates:
            report_date = date.fromisoformat(sorted_dates[0])

    if period == 'day':
        anchor = report_date.isoformat() if report_date is not None else sorted_dates[0]
    else:
        anchor = next((d for d in sorted_dates if not month or d.startswith(month)), None)
    if anchor is None:
        return _empty_info_dashboard(period=period, month=month)
    if period == 'day' and report_date is None:
        report_date = date.fromisoformat(anchor)

    anchor_date = date.fromisoformat(anchor)
    if period == 'month' and month:
        import calendar as _cal

        last_day = _cal.monthrange(int(month[:4]), int(month[5:7]))[1]
        window_start, window_end = f'{month}-01', f'{month}-{last_day:02d}'
    else:
        # 35-day buffer so the 30-day trend series (below) has enough history
        # ending at `anchor`, even with a few missing report days.
        window_start = (anchor_date - timedelta(days=35)).isoformat()
        window_end = anchor_date.isoformat()

    all_rows, attrs, titles, entity_by_row_key = _load_bundle(
        window_start=window_start, window_end=window_end
    )
    if not all_rows:
        return _empty_info_dashboard(period=period, month=month)

    by_title = _group_by_title_rowkey(all_rows, attrs, titles, entity_by_row_key)

    national_items = _filter_day_month(
        by_title.get(TITLE_NATIONAL, []),
        period=period,
        report_date=report_date,
        month=month,
    )
    national_facts: dict[str, str] = {}
    if period == 'month':
        national_facts = _aggregate_national_facts(national_items)
    elif national_items:
        exact = [i for i in national_items if i.get('report_date') == anchor]
        national_facts = (exact[0] if exact else national_items[0])['facts']

    kpis = []
    kpi_by_key: dict[str, dict[str, Any]] = {}
    for key, label_en, label_ar, unit in KPI_SPECS:
        val = _parse_number(national_facts.get(key, ''))
        status = _kpi_status(key, val)
        # Only day view has a concrete on_date to resolve a target against; when a
        # numeric target is configured for this metric/date, it takes priority over
        # the qualitative value-based rule above.
        if period == 'day' and report_date is not None and val is not None:
            target = resolve_target_value(key, report_date, scope_type=OperationalTarget.ScopeType.NATIONAL)
            if target is not None:
                achievement = achievement_pct(val, target)
                status = target_status(achievement)
        row = {
            'id': key,
            'label_en': label_en,
            'label_ar': label_ar,
            'value': val,
            'unit': unit,
            'delta_pct': None,
            'status': status,
        }
        kpis.append(row)
        kpi_by_key[key] = row

    kpi_groups_out = []
    for group_id, group_en, group_ar, group_keys in KPI_GROUPS:
        group_kpis = []
        for key in group_keys:
            row = kpi_by_key.get(key)
            if row is None:
                continue
            label_en, label_ar = KPI_GROUP_LABEL_OVERRIDES.get(
                (group_id, key), (row['label_en'], row['label_ar'])
            )
            group_kpis.append({**row, 'label_en': label_en, 'label_ar': label_ar})
        if group_kpis:
            kpi_groups_out.append({
                'id': group_id,
                'label_en': group_en,
                'label_ar': group_ar,
                'kpis': group_kpis,
            })

    notes_items = _filter_day_month(
        by_title.get(TITLE_NOTES, []),
        period=period,
        report_date=report_date,
        month=month,
    )
    if period == 'month':
        notes, maintenance_ar, peak_time = _collect_month_notes_maintenance(
            notes_items, anchor=anchor
        )
    else:
        peak_time = None
        notes = []
        maintenance_ar = ''
        if notes_items:
            nf = notes_items[0]['facts']
            peak_time = nf.get('peak_generation_time') or None
            maintenance_ar = nf.get('maintenance_groups') or ''
            if nf.get('notes_ar') or nf.get('notes_en'):
                notes.append(
                    {
                        'ar': nf.get('notes_ar') or '',
                        'en': nf.get('notes_en') or '',
                    }
                )

    # Generation units: day view all matching rows; month view = anchor day only
    unit_source = list(by_title.get(TITLE_UNITS, [])) + list(by_title.get(TITLE_PLANT, []))
    if period == 'month':
        unit_items = _items_on_date(
            _filter_day_month(
                unit_source, period=period, report_date=report_date, month=month
            ),
            anchor,
        )
    else:
        unit_items = _filter_day_month(
            unit_source, period=period, report_date=report_date, month=month
        )
    generation_units = []
    plant_cache = {p.id: p for p in PowerPlant.objects.all()}
    for item in unit_items:
        eid = item.get('entity_id')
        plant = plant_cache.get(eid) if eid else None
        facts = item['facts']
        generation_units.append(
            {
                'plant_code': plant.code if plant else str(eid or ''),
                'plant_label_en': (plant.name_en if plant else '') or str(eid or ''),
                'plant_label_ar': (plant.name_ar if plant else '') or str(eid or ''),
                'unit_code': _fact_get(facts, 'رمز الوحدة', 'unit_code') or '—',
                'nominal_mw': _fact_number(
                    facts, 'القدرة الاسمية (ميجاواط)', 'القدرة الاسمية', 'nominal_mw'
                ),
                'available_mw': _fact_number(facts, 'المتاح (ميجاواط)', 'المتاح', 'available_mw'),
                'generation_mwh_24h': _fact_number(
                    facts,
                    'التوليد 24س (ميجاواط ساعة)',
                    'التوليد (ميجاواط ساعة)',
                    'التوليد',
                    'generation_mwh',
                ),
                'status': _fact_get(facts, 'الحالة', 'status') or 'info',
            }
        )

    # Fuel tanks: month uses anchor day snapshot (same as legacy dashboard)
    fuel_month_items = _filter_day_month(
        by_title.get(TITLE_FUEL, []),
        period=period,
        report_date=report_date,
        month=month,
    )
    fuel_items = (
        _items_on_date(fuel_month_items, anchor) if period == 'month' else fuel_month_items
    )
    tank_cache = {t.id: t for t in FuelTankStation.objects.all()}
    fuel_labels_en, fuel_labels_ar, current_tons, max_tons, fill_pct = [], [], [], [], []
    for item in fuel_items:
        tank = tank_cache.get(item.get('entity_id'))
        if tank is None:
            continue
        cur = _fact_number(
            item['facts'], 'المخزون الحالي (طن)', 'المخزون الحالي', 'current_stock_tons'
        )
        cap = float(tank.max_capacity_tons) if tank.max_capacity_tons is not None else None
        fuel_labels_en.append(tank.name_en or tank.code)
        fuel_labels_ar.append(tank.name_ar or tank.code)
        current_tons.append(cur or 0)
        max_tons.append(cap or 0)
        fill_pct.append(
            round((cur / cap) * 100, 1) if cur is not None and cap and cap > 0 else 0
        )
    fuel_chart = None
    if fuel_labels_ar:
        fuel_chart = {
            'labels_en': fuel_labels_en,
            'labels_ar': fuel_labels_ar,
            'current_tons': current_tons,
            'max_capacity_tons': max_tons,
            'fill_pct': fill_pct,
        }

    # Governorates: month sums per governorate; day is single-day rows
    gov_items = _filter_day_month(
        by_title.get(TITLE_GOV, []),
        period=period,
        report_date=report_date,
        month=month,
    )
    gov_cache = {g.id: g for g in LoadGovernorate.objects.all()}
    if period == 'month':
        g_en, g_ar, consumed, allocated = _sum_gov_chart(gov_items, gov_cache)
    else:
        g_en, g_ar, consumed, allocated = [], [], [], []
        for item in gov_items:
            gov = gov_cache.get(item.get('entity_id'))
            if gov is None:
                continue
            g_en.append(gov.name_en or gov.code)
            g_ar.append(gov.name_ar or gov.code)
            facts = item['facts']
            consumed.append(
                _fact_number(facts, 'المستهلك (ميجاواط)', 'المستهلك', 'consumed_mw') or 0
            )
            allocated.append(
                _fact_number(facts, 'المخصّص (ميجاواط)', 'المخصّص', 'allocated_mw') or 0
            )

    # Hydro: month aggregates per dam; day is raw rows
    hydro_items = _filter_day_month(
        by_title.get(TITLE_HYDRO, []),
        period=period,
        report_date=report_date,
        month=month,
    )
    dam_cache = {d.id: d for d in HydroDam.objects.all()}
    if period == 'month':
        hydro_rows = _aggregate_hydro_chart(hydro_items, dam_cache)
    else:
        hydro_rows = []
        for item in hydro_items:
            dam = dam_cache.get(item.get('entity_id'))
            facts = item['facts']
            hydro_rows.append(
                {
                    'dam_code': dam.code if dam else str(item.get('entity_id') or ''),
                    'front_level_m': _fact_number(
                        facts, 'المنسوب الأمامي (م)', 'المنسوب الأمامي', 'front_level_m'
                    ),
                    'back_level_m': _fact_number(
                        facts, 'المنسوب الخلفي (م)', 'المنسوب الخلفي', 'back_level_m'
                    ),
                    'generation_mwh': _fact_number(
                        facts, 'التوليد (ميجاواط ساعة)', 'التوليد', 'generation_mwh'
                    ),
                    'outflow_m3s': _fact_number(
                        facts, 'التصريف (م3/ث)', 'التصريف', 'outflow_m3s'
                    ),
                    'inflow_m3s': _fact_number(facts, 'الوارد (م3/ث)', 'الوارد', 'inflow_m3s'),
                    'expected_m3s': _fact_number(
                        facts, 'المتوقع (م3/ث)', 'المتوقع', 'expected_m3s'
                    ),
                }
            )

    # Incidents
    gen_inc = []
    for item in _filter_day_month(
        by_title.get(TITLE_INC_GEN, []),
        period=period,
        report_date=report_date,
        month=month,
    ):
        f = item['facts']
        gen_inc.append(
            {
                'report_date': item.get('report_date'),
                'event_time': f.get('event_time') or '',
                'description_ar': f.get('description_ar') or '',
                'description_en': f.get('description_en') or '',
            }
        )
    grid_inc = []
    for item in _filter_day_month(
        by_title.get(TITLE_INC_GRID, []),
        period=period,
        report_date=report_date,
        month=month,
    ):
        f = item['facts']
        grid_inc.append(
            {
                'report_date': item.get('report_date'),
                'line_name': f.get('line_name') or '',
                'voltage_kv': _parse_number(f.get('voltage_kv', '')),
                'action_ar': f.get('action_ar') or '',
                'action_en': f.get('action_en') or '',
            }
        )

    # Gas/steam are actual 24h-generated energy (MWh); hydro/solar/wind only have
    # instantaneous installed-capacity readings (MW), not a matching MWh figure —
    # mixing the two in one series would sum incompatible units. Capacity numbers
    # stay visible via their own KPI tiles instead.
    mix_labels_en = ['Gas', 'Steam']
    mix_labels_ar = ['غاز', 'بخار']
    mix_values = [
        _parse_number(national_facts.get('gas_generation_mwh_24h', '')) or 0,
        _parse_number(national_facts.get('steam_generation_mwh', '')) or 0,
    ]

    # Trends from national rows across dates
    try:
        from electricity.metric_catalog import METRIC_BY_KEY
    except ImportError:  # pragma: no cover
        METRIC_BY_KEY = {}
    trends: dict[str, Any] = {}
    national_by_date: dict[str, dict[str, str]] = {}
    for item in by_title.get(TITLE_NATIONAL, []):
        d = item.get('report_date') or ''
        if len(d) >= 10:
            national_by_date[d[:10]] = item['facts']
    trend_dates = sorted(national_by_date.keys())
    if period == 'month' and month:
        trend_dates = [d for d in trend_dates if d.startswith(month)]
    else:
        trend_dates = trend_dates[-30:]
    for key in TREND_KEYS:
        points = []
        for d in trend_dates:
            v = _parse_number(national_by_date[d].get(key, ''))
            if v is not None:
                points.append({'date': d, 'value': v})
        spec = METRIC_BY_KEY.get(key)
        trends[key] = {
            'metric_key': key,
            'label_en': spec.label_en if spec else key,
            'label_ar': spec.label_ar if spec else key,
            'unit': spec.unit if spec else '',
            'points': points,
        }

    # Group incidents by day (month view UX)
    by_day_map: dict[str, dict[str, list]] = {}
    for inc in gen_inc:
        d = (inc.get('report_date') or anchor or '')[:10]
        if not d:
            continue
        by_day_map.setdefault(d, {'date': d, 'generation': [], 'grid': []})
        by_day_map[d]['generation'].append(inc)
    for inc in grid_inc:
        d = (inc.get('report_date') or anchor or '')[:10]
        if not d:
            continue
        by_day_map.setdefault(d, {'date': d, 'generation': [], 'grid': []})
        by_day_map[d]['grid'].append(inc)
    incidents_by_day = [by_day_map[k] for k in sorted(by_day_map.keys(), reverse=True)]

    on_date = None
    if anchor:
        try:
            on_date = date.fromisoformat(str(anchor)[:10])
        except ValueError:
            on_date = None
    alerts = list_info_alerts(
        electricity_category_name(),
        settings_id=electricity_category_id_override(),
        env_id_name='ELECTRICITY_TITLE_CATEGORY_ID',
        on_date=on_date,
    )
    gcount = _parse_number(national_facts.get('grid_incidents_count', '')) or 0
    if gcount > 0:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'{int(gcount)} transmission line incident(s) logged.',
                'message_ar': f'{int(gcount)} حادث خطوط نقل مسجل.',
            }
        )
    gencount = _parse_number(national_facts.get('generation_incidents_count', '')) or 0
    if gencount > 0:
        alerts.append(
            {
                'severity': 'warning',
                'message_en': f'{int(gencount)} generation incident(s) logged.',
                'message_ar': f'{int(gencount)} حادث توليد مسجل.',
            }
        )

    has_data = bool(
        national_facts
        or generation_units
        or fuel_chart
        or g_ar
        or hydro_rows
        or gen_inc
        or grid_inc
        or notes_items
    )
    if not has_data:
        empty = _empty_info_dashboard(period=period, month=month)
        empty['available_dates'] = sorted_dates
        empty['available_months'] = sorted_months
        return empty

    maintenance_groups = [
        g.strip() for g in maintenance_ar.replace('\r', '\n').split('\n') if g.strip()
    ]

    return {
        'period': period,
        'month': month,
        'report_date': anchor,
        'anchor_date': anchor,
        'reports_count': len(national_items) or 1,
        'days_covered': len({i.get('report_date') for i in national_items if i.get('report_date')})
        or 1,
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': electricity_category_name(),
        'peak_generation_time': peak_time,
        'kpis': kpis,
        'kpi_groups': kpi_groups_out,
        'status_cards': _status_cards(),
        'charts': {
            'generation_mix': {
                'labels_en': mix_labels_en,
                'labels_ar': mix_labels_ar,
                'values': mix_values,
            },
            'generation_units': generation_units,
            'governorate_load': {
                'labels_en': g_en,
                'labels_ar': g_ar,
                'consumed': consumed,
                'allocated': allocated,
            },
            'fuel_tanks': fuel_chart,
            'hydro': hydro_rows,
            'maintenance_groups_ar': maintenance_ar,
            'maintenance_groups': maintenance_groups,
        },
        'trends': trends,
        'alerts': alerts,
        'notes': notes
        or [
            {
                'ar': 'المؤشرات مأخوذة من Info المقبول تحت فئة إدارة قطاع الكهرباء.',
                'en': 'KPIs are sourced from accepted Info under the electricity title category.',
            }
        ],
        'incidents': {
            'generation': gen_inc,
            'grid': grid_inc,
            'by_day': incidents_by_day,
        },
        'available_dates': sorted_dates,
        'available_months': sorted_months,
    }
