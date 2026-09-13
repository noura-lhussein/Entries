"""
Water portal dashboards from accepted Info (TitleCategory «إدارة قطاع المياه»).

Rainfall KPIs, charts, and map metrics come from Info; station/basin master
tables supply coordinates and filter catalogs only (no RainfallObservation).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from functools import lru_cache
from typing import Any

from django.db import DatabaseError
from projects.display_models import (
    ReportDynamicFormsAttribute,
    ReportDynamicFormsInfo,
    ReportDynamicFormsTitle,
)
from projects.report_forms_read import ACCEPTED

from water.info_scope import water_category_name

# Stable codes assigned by report_moe's seed_*_info_forms commands
# (dynamic_forms_title.code) — never match a Title by its Arabic `name`, which
# is free-text and can be renamed at any time from the report_moe UI.
TITLE_NATIONAL = 'water.national'
TITLE_EUPHRATES = 'water.euphrates'
TITLE_RAINFALL_ENTITY = 'water.rainfall_entity'
TITLE_DAM_ENTITY = 'water.dam_entity'
TITLE_DRINKING_STATION_ENTITY = 'water.drinking_station_entity'

# Entity scoping for the drinking-station title (dynamic_forms_info.entity_type) —
# other entity types can share the same attribute ids in theory, so this filter is
# required, not just belt-and-braces.
DRINKING_STATION_ENTITY_TYPE = 'drinking_station'

MONTH_LABELS_EN = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]
MONTH_LABELS_AR = [
    'كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران',
    'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول',
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
    try:
        return date.fromisoformat(str(value or '').strip()[:10])
    except ValueError:
        return None


def _kpi(
    *,
    kpi_id: str,
    label_en: str,
    label_ar: str,
    value: float | int | None,
    unit: str = '',
    delta_pct: float | None = None,
    status: str = 'neutral',
) -> dict[str, Any]:
    return {
        'id': kpi_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'unit': unit,
        'delta_pct': delta_pct,
        'status': status,
    }


def _load_title_context(title_code: str) -> tuple[
    list[Any],
    dict[int, ReportDynamicFormsAttribute],
    dict[int, str],
]:
    """Fetch every accepted Info row for one title's own attributes.

    Deliberately scoped to a single title rather than the whole water
    category: a shared row-count cap across every water title combined means
    that once any single title's history (e.g. Euphrates, ~100k rows for ~13
    metrics/day since 2000) approaches that cap, it silently truncates *every
    other* title's data too — confirmed live the day Euphrates was fully
    migrated. Scoping per-title means one title's volume can never starve
    another's.
    """
    by_key = _title_attrs_by_code(title_code)
    attr_ids = {a.id for a in by_key.values()}
    if not attr_ids:
        return [], {}, {}
    try:
        qs = ReportDynamicFormsInfo.objects.filter(
            confirmed=ACCEPTED, attribute_id__in=attr_ids,
        )
        if hasattr(ReportDynamicFormsInfo, 'archived'):
            qs = qs.filter(archived=False)
        infos = list(qs.iterator(chunk_size=5000))
        attrs = {a.id: a for a in by_key.values()}
        title = ReportDynamicFormsTitle.objects.filter(
            code=title_code
        ).first()
        titles = {title.id: title.code} if title else {}
    except DatabaseError:
        return [], {}, {}
    return infos, attrs, titles


def _row_facts(
    infos: list[Any],
    attrs: dict[int, ReportDynamicFormsAttribute],
    titles: dict[int, str],
    title_code: str,
) -> dict[str, dict[str, str]]:
    """Group Info rows by row_key, keyed by Attribute.key (never `.label`).

    Also stamps a synthetic `_date` slot on any row whose title has a
    `type='date'` attribute, regardless of that attribute's own key name
    (`report_date` vs `reading_date` vs `observation_date` across titles) —
    this is what lets `_facts_date` stay title-agnostic.
    """
    title_attr_ids = {
        aid for aid, a in attrs.items() if titles.get(a.title_id) == title_code
    }
    rows: dict[str, dict[str, str]] = defaultdict(dict)
    for info in infos:
        # Not "if title_attr_ids and ..." — an empty title_attr_ids means this
        # title genuinely has no matching attributes in the loaded batch (a
        # title with zero real data yet), which must produce zero rows, not
        # "no filter" (that Python truthiness gotcha silently made every
        # dashboard built this way return every OTHER title's data whenever
        # the target title had none — confirmed live: it showed a fully
        # populated Euphrates dashboard while the table had 0 real rows).
        if info.attribute_id not in title_attr_ids:
            continue
        attr = attrs.get(info.attribute_id)
        if not attr or not info.row_key:
            continue
        rk = str(info.row_key)
        if attr.key:
            rows[rk][attr.key] = str(info.value or '')
        if attr.type == 'date':
            rows[rk]['_date'] = str(info.value or '')
        if getattr(info, 'entity_id', None):
            rows[rk]['_entity_id'] = str(info.entity_id)
        if getattr(info, 'entity_type', None):
            rows[rk]['_entity_type'] = str(info.entity_type)
    return rows


def _facts_date(facts: dict[str, str]) -> date | None:
    return _parse_date(facts.get('_date', ''))


def _national_metrics_by_date(
    infos: list[Any] | None = None,
    attrs: dict[int, ReportDynamicFormsAttribute] | None = None,
    titles: dict[int, str] | None = None,
) -> dict[date, dict[str, float]]:
    if infos is None:
        infos, attrs, titles = _load_title_context(TITLE_NATIONAL)
    assert attrs is not None and titles is not None
    rows = _row_facts(infos, attrs, titles, TITLE_NATIONAL)
    by_date: dict[date, dict[str, float]] = {}
    for facts in rows.values():
        d = _facts_date(facts)
        if d is None:
            continue
        metrics: dict[str, float] = {}
        for key, raw in facts.items():
            if key.startswith('_'):
                continue
            num = _parse_number(raw)
            if num is not None:
                metrics[key] = num
        if not metrics:
            continue
        by_date.setdefault(d, {}).update(metrics)
    return by_date


@lru_cache(maxsize=64)
def _title_attrs_by_code(title_code: str) -> dict[str, ReportDynamicFormsAttribute]:
    """Attributes of a dynamic_forms title, keyed by `Attribute.key` only.

    Never keyed by `.label` — label is free-text Arabic display text that can
    change at any time from the report_moe UI; `key` is the stable contract
    (see moeds' `check_info_contract` command and report_moe's `is_system`
    protection on Title/Attribute).

    Cached: title/attribute *schema* (not report data) changes only via admin seed
    commands, so re-querying it 5-6x per dashboard build (once per helper call) is
    pure waste. Call `_title_attrs_by_code.cache_clear()` after running any
    seed_*_info_forms command in the same process (e.g. a long-lived shell/worker).
    """
    title = ReportDynamicFormsTitle.objects.filter(code=title_code).first()
    if title is None:
        return {}
    by_key: dict[str, ReportDynamicFormsAttribute] = {}
    for attr in ReportDynamicFormsAttribute.objects.filter(title_id=title.id):
        if attr.key:
            by_key[attr.key] = attr
        if attr.type == 'date':
            by_key.setdefault('_date', attr)
    return by_key


def _date_attr_ids(by_key: dict[str, ReportDynamicFormsAttribute]) -> list[int]:
    attr = by_key.get('_date')
    return [attr.id] if attr else []


def _row_keys_for_years(
    date_attr_ids: list[int],
    years: set[int],
    *,
    entity_ids: set[int] | None = None,
) -> dict[Any, date]:
    """Direct, uncapped lookup of row_keys whose date-cell falls in `years`.

    Queries only the (small) date attribute rows instead of the whole water
    category, so it stays correct regardless of how much other Info exists.
    """
    if not date_attr_ids or not years:
        return {}
    qs = ReportDynamicFormsInfo.objects.filter(
        confirmed=ACCEPTED, attribute_id__in=date_attr_ids,
    )
    if entity_ids is not None:
        qs = qs.filter(entity_id__in=entity_ids)
    year_prefixes = {str(y) for y in years}
    row_key_dates: dict[Any, date] = {}
    for rk, val in qs.values_list('row_key', 'value').iterator(chunk_size=5000):
        if not val or val[:4] not in year_prefixes:
            continue
        d = _parse_date(val)
        if d is not None:
            row_key_dates[rk] = d
    return row_key_dates


def _facts_for_row_keys(
    row_keys: list[Any],
    by_name: dict[str, ReportDynamicFormsAttribute],
) -> dict[Any, dict[str, str]]:
    if not row_keys:
        return {}
    # An attribute can appear under more than one name (its real `key`, plus the
    # synthetic `_date` slot for the title's date field) — keep every name, not
    # just the last one written, or the date value silently loses its real key.
    names_by_attr: dict[int, list[str]] = defaultdict(list)
    for name, attr in by_name.items():
        names_by_attr[attr.id].append(name)
    qs = ReportDynamicFormsInfo.objects.filter(
        confirmed=ACCEPTED, row_key__in=row_keys, attribute_id__in=list(
            names_by_attr.keys()),
    )
    facts: dict[Any, dict[str, str]] = defaultdict(dict)
    for rk, aid, val, eid in qs.values_list('row_key', 'attribute_id', 'value', 'entity_id'):
        for name in names_by_attr.get(aid, ()):
            facts[rk][name] = val or ''
        if eid is not None:
            facts[rk]['_entity_id'] = str(eid)
    return facts


def _national_rain_metrics_for_years(years: set[int]) -> dict[date, dict[str, float]]:
    by_name = _title_attrs_by_code(TITLE_NATIONAL)
    date_attr_ids = _date_attr_ids(by_name)
    row_key_dates = _row_keys_for_years(date_attr_ids, years)
    facts_by_rk = _facts_for_row_keys(list(row_key_dates.keys()), by_name)
    by_date: dict[date, dict[str, float]] = {}
    for rk, d in row_key_dates.items():
        facts = facts_by_rk.get(rk, {})
        metrics: dict[str, float] = {}
        for key in ('rainfall_total_mm', 'rainfall_stations_reporting'):
            num = _parse_number(facts.get(key, ''))
            if num is not None:
                metrics[key] = num
        if metrics:
            by_date.setdefault(d, {}).update(metrics)
    return by_date


def _entity_rain_metrics_for_years(
    years: set[int],
    station_ids: set[int] | None,
) -> dict[date, dict[str, float]]:
    by_name = _title_attrs_by_code(TITLE_RAINFALL_ENTITY)
    date_attr_ids = _date_attr_ids(by_name)
    row_key_dates = _row_keys_for_years(
        date_attr_ids, years, entity_ids=station_ids)
    facts_by_rk = _facts_for_row_keys(list(row_key_dates.keys()), by_name)
    by_date: dict[date, dict[str, float]] = {}
    for rk, d in row_key_dates.items():
        facts = facts_by_rk.get(rk, {})
        mm = _parse_number(facts.get('precipitation_mm', ''))
        if mm is None:
            continue
        metrics = by_date.setdefault(
            d, {'rainfall_total_mm': 0.0, 'rainfall_stations_reporting': 0})
        metrics['rainfall_total_mm'] += mm
        metrics['rainfall_stations_reporting'] += 1
    return by_date


def _rainfall_years_available(*, station_ids: set[int] | None) -> list[int]:
    title_code = TITLE_RAINFALL_ENTITY if station_ids is not None else TITLE_NATIONAL
    by_name = _title_attrs_by_code(title_code)
    date_attr_ids = _date_attr_ids(by_name)
    if not date_attr_ids:
        return []
    qs = ReportDynamicFormsInfo.objects.filter(
        confirmed=ACCEPTED, attribute_id__in=date_attr_ids,
    )
    if station_ids is not None:
        qs = qs.filter(entity_id__in=station_ids)
    else:
        # TITLE_NATIONAL's date attribute is shared by dam/drinking-water rows too —
        # restrict to row_keys that actually carry a rainfall metric.
        rain_attr_ids = [
            attr.id for name, attr in by_name.items()
            if name in ('rainfall_total_mm', 'rainfall_stations_reporting')
        ]
        if not rain_attr_ids:
            return []
        rain_row_keys = list(
            ReportDynamicFormsInfo.objects
            .filter(confirmed=ACCEPTED, attribute_id__in=rain_attr_ids)
            .values_list('row_key', flat=True)
        )
        if not rain_row_keys:
            return []
        qs = qs.filter(row_key__in=rain_row_keys)
    years: set[int] = set()
    for val in qs.values_list('value', flat=True).iterator(chunk_size=5000):
        if val and val[:4].isdigit():
            years.add(int(val[:4]))
    return sorted(years, reverse=True)


def build_water_info_sector_payload(*, year: int | None = None) -> dict[str, Any]:
    by_date = _national_metrics_by_date()
    if year:
        by_date = {d: m for d, m in by_date.items() if d.year == year}
    if not by_date:
        return {
            'status': 'empty',
            'source': 'dynamic_forms',
            'category_name': water_category_name(),
            'has_info': False,
            'kpis': [],
            'available_dates': [],
        }

    latest = max(by_date.keys())
    metrics = by_date[latest]
    kpis = [
        {
            'id': 'rainfall_stations_reporting',
            'label_en': 'Rainfall stations reporting',
            'label_ar': 'محطات الهطول المبلّغة',
            'value': metrics.get('rainfall_stations_reporting'),
            'unit': '',
        },
        {
            'id': 'rainfall_total_mm',
            'label_en': 'Total rainfall',
            'label_ar': 'إجمالي الهطول',
            'value': metrics.get('rainfall_total_mm'),
            'unit': 'mm',
        },
        {
            'id': 'dams_with_readings',
            'label_en': 'Dams with readings',
            'label_ar': 'سدود بقراءات',
            'value': metrics.get('dams_with_readings'),
            'unit': '',
        },
        {
            'id': 'dam_storage_avg_mcm',
            'label_en': 'Average dam storage',
            'label_ar': 'متوسط تخزين السدود',
            'value': metrics.get('dam_storage_avg_mcm'),
            'unit': 'M m³',
        },
        {
            'id': 'drinking_stations_total',
            'label_en': 'Drinking water stations',
            'label_ar': 'محطات مياه الشرب',
            'value': metrics.get('drinking_stations_total'),
            'unit': '',
        },
        {
            'id': 'drinking_stations_operational',
            'label_en': 'Operational stations',
            'label_ar': 'محطات عاملة',
            'value': metrics.get('drinking_stations_operational'),
            'unit': '',
        },
    ]
    return {
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': water_category_name(),
        'has_info': True,
        'report_date': latest.isoformat(),
        'kpis': kpis,
        'available_dates': [d.isoformat() for d in sorted(by_date.keys(), reverse=True)[:90]],
    }


def build_rainfall_info_dashboard(
    *,
    year: int | None = None,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> dict[str, Any] | None:
    """Build rainfall KPIs/charts from national Info, or from scoped station Info when
    a basin/governorate is selected. Returns None if no coverage."""
    scoped_station_ids: set[int] | None = None
    if basin_slug or governorate:
        from water.models import RainfallStation

        qs = RainfallStation.objects.all()
        if basin_slug:
            qs = qs.filter(basin__slug=basin_slug)
        if governorate:
            qs = qs.filter(governorate=governorate)
        scoped_station_ids = set(qs.values_list('id', flat=True))
        if not scoped_station_ids:
            return None

    years = _rainfall_years_available(station_ids=scoped_station_ids)
    if not years:
        return None
    selected_year = year if year in years else years[0]
    annual_years = sorted(y for y in years if y >= selected_year - 10)[-11:]
    needed_years = set(annual_years) | {selected_year, selected_year - 1}

    if scoped_station_ids is not None:
        rain_dates = _entity_rain_metrics_for_years(
            needed_years, scoped_station_ids)
    else:
        rain_dates = _national_rain_metrics_for_years(needed_years)
    if not rain_dates:
        return None

    year_days = {d: m for d, m in rain_dates.items() if d.year ==
                 selected_year}
    if not year_days:
        return None

    totals = [m.get('rainfall_total_mm') or 0 for m in year_days.values()]
    total_mm = round(sum(totals), 1)
    rain_days = sum(1 for v in totals if v > 0)
    stations_vals = [
        m.get('rainfall_stations_reporting')
        for m in year_days.values()
        if m.get('rainfall_stations_reporting') is not None
    ]
    active_stations = int(max(stations_vals)) if stations_vals else 0
    avg_per_station = round(total_mm / active_stations,
                            1) if active_stations else 0.0

    prev_days = {d: m for d, m in rain_dates.items() if d.year ==
                 selected_year - 1}
    prev_total = sum(m.get('rainfall_total_mm')
                     or 0 for m in prev_days.values())
    delta_pct = None
    if prev_total > 0:
        delta_pct = round((total_mm - prev_total) / prev_total * 100, 1)

    monthly_map = defaultdict(float)
    for d, m in year_days.items():
        monthly_map[d.month] += m.get('rainfall_total_mm') or 0

    annual_values = []
    for y in annual_years:
        annual_values.append(
            round(
                sum(
                    (m.get('rainfall_total_mm') or 0)
                    for d, m in rain_dates.items()
                    if d.year == y
                ),
                1,
            )
        )

    # Station daily Info for the selected year (map, top list, basin charts).
    top_by_name = _title_attrs_by_code(TITLE_RAINFALL_ENTITY)
    top_date_attr_ids = _date_attr_ids(top_by_name)
    top_row_key_dates = _row_keys_for_years(
        top_date_attr_ids, {selected_year}, entity_ids=scoped_station_ids
    )
    top_facts_by_rk = _facts_for_row_keys(
        list(top_row_key_dates.keys()), top_by_name)
    station_totals: dict[int, float] = defaultdict(float)
    station_rain_days: dict[int, int] = defaultdict(int)
    station_max_daily: dict[int, float] = defaultdict(float)
    observations_count = 0
    for rk in top_row_key_dates:
        facts = top_facts_by_rk.get(rk, {})
        eid = facts.get('_entity_id')
        if eid is None:
            continue
        mm = _parse_number(facts.get('precipitation_mm', ''))
        if mm is None:
            continue
        observations_count += 1
        sid = int(eid)
        station_totals[sid] += mm
        if mm > 0:
            station_rain_days[sid] += 1
        if mm > station_max_daily[sid]:
            station_max_daily[sid] = mm

    from water.models import RainfallBasin, RainfallStation
    from water.rainfall_dashboard import build_basin_choropleth

    station_ids = list(station_totals.keys())
    stations_by_id = {
        s.id: s
        for s in RainfallStation.objects.filter(id__in=station_ids).select_related('basin')
    }

    top_stations = []
    for sid, total in sorted(station_totals.items(), key=lambda x: x[1], reverse=True)[:10]:
        st = stations_by_id.get(sid)
        top_stations.append(
            {
                'name': st.name if st else f'Station {sid}',
                'governorate': st.governorate if st else '',
                'basin_en': st.basin.name_en if st and st.basin_id else '',
                'total_mm': round(total, 1),
                'rain_days': station_rain_days.get(sid, 0),
                'max_daily_mm': round(station_max_daily.get(sid, 0), 1),
            }
        )

    map_station_qs = RainfallStation.objects.select_related('basin')
    if basin_slug:
        map_station_qs = map_station_qs.filter(basin__slug=basin_slug)
    if governorate:
        map_station_qs = map_station_qs.filter(governorate=governorate)
    map_stations: list[dict[str, Any]] = []
    basin_metrics: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {'total_mm': 0.0, 'station_count': 0}
    )
    for station in map_station_qs:
        total = station_totals.get(station.id, 0.0)
        rain_days_n = station_rain_days.get(station.id, 0)
        if total <= 0 and not rain_days_n:
            continue
        map_stations.append(
            {
                'id': station.id,
                'name': station.name,
                'governorate': station.governorate,
                'basin_slug': station.basin.slug,
                'basin_en': station.basin.name_en,
                'basin_ar': station.basin.name_ar,
                'latitude': float(station.latitude) if station.latitude is not None else None,
                'longitude': float(station.longitude) if station.longitude is not None else None,
                'total_mm': round(total, 1),
                'rain_days': rain_days_n,
                'max_daily_mm': round(station_max_daily.get(station.id, 0), 1),
            }
        )
        slug = station.basin.slug
        basin_metrics[slug]['total_mm'] = float(
            basin_metrics[slug]['total_mm']) + total
        basin_metrics[slug]['station_count'] = int(
            basin_metrics[slug]['station_count']) + 1

    basins = list(
        RainfallBasin.objects.order_by('name_en').values(
            'slug', 'name_en', 'name_ar'),
    )
    gov_qs = RainfallStation.objects.exclude(governorate='')
    if basin_slug:
        gov_qs = gov_qs.filter(basin__slug=basin_slug)
    # Prefer governorates that have Info readings this year; else all master values.
    govs_with_data = sorted(
        {
            stations_by_id[sid].governorate
            for sid in station_totals
            if sid in stations_by_id and stations_by_id[sid].governorate
        }
    )
    governorates = govs_with_data or sorted(
        gov_qs.values_list('governorate', flat=True).order_by().distinct()
    )

    basin_rows = [
        (
            b['slug'],
            b['name_en'],
            b['name_ar'],
            float(basin_metrics[b['slug']]['total_mm']),
        )
        for b in basins
        if basin_metrics[b['slug']]['total_mm']
    ]
    basin_rows.sort(key=lambda row: row[3], reverse=True)
    basin_comparison = {
        'labels_en': [row[1] for row in basin_rows],
        'labels_ar': [row[2] for row in basin_rows],
        'values': [round(row[3], 1) for row in basin_rows],
    }

    data_through = max(year_days.keys()).isoformat()
    return {
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': water_category_name(),
        'data_through': data_through,
        'observations_count': observations_count,
        'active_stations_count': active_stations,
        'filters': {
            'years': years,
            'basins': basins,
            'governorates': governorates,
        },
        'selected_year': selected_year,
        'selected_basin': basin_slug,
        'selected_governorate': governorate,
        'kpis': [
            _kpi(
                kpi_id='total-rainfall',
                label_en='Total rainfall',
                label_ar='إجمالي الهطول',
                value=total_mm,
                unit='mm',
                delta_pct=delta_pct,
                status='ok' if (delta_pct or 0) >= 0 else 'warning',
            ),
            _kpi(
                kpi_id='rain-days',
                label_en='Rain days',
                label_ar='أيام الهطول',
                value=rain_days,
            ),
            _kpi(
                kpi_id='active-stations',
                label_en='Active stations',
                label_ar='المحطات',
                value=active_stations,
            ),
            _kpi(
                kpi_id='avg-per-station',
                label_en='Avg. per station',
                label_ar='متوسط لكل محطة',
                value=avg_per_station,
                unit='mm',
            ),
        ],
        'insights': [
            {
                'id': 'info-source',
                'text_en': 'Rainfall KPIs and map from accepted Info (no legacy observation tables).',
                'text_ar': 'مؤشرات الهطول والخريطة من بيانات Info المعتمدة (بدون جداول القراءات القديمة).',
                'severity': 'info',
            }
        ],
        'charts': {
            'annual_trend': {'labels': [str(y) for y in annual_years], 'values': annual_values},
            'monthly_distribution': {
                'labels_en': MONTH_LABELS_EN,
                'labels_ar': MONTH_LABELS_AR,
                'values': [round(monthly_map.get(m, 0), 1) for m in range(1, 13)],
            },
            'basin_comparison': basin_comparison,
            'top_stations': top_stations,
        },
        'map': {
            'stations': map_stations,
            'basin_choropleth': build_basin_choropleth(
                year=selected_year,
                basin_metrics=dict(basin_metrics),
            ),
        },
    }


def _dam_years_available() -> list[int]:
    by_name = _title_attrs_by_code(TITLE_NATIONAL)
    dam_attr_ids = [
        attr.id for name, attr in by_name.items()
        if name in ('dams_with_readings', 'dam_storage_avg_mcm', 'dam_storage_total_mcm')
    ]
    date_attr_ids = _date_attr_ids(by_name)
    if not dam_attr_ids or not date_attr_ids:
        return []
    row_keys = list(
        ReportDynamicFormsInfo.objects
        .filter(confirmed=ACCEPTED, attribute_id__in=dam_attr_ids)
        .values_list('row_key', flat=True)
    )
    if not row_keys:
        return []
    qs = ReportDynamicFormsInfo.objects.filter(
        confirmed=ACCEPTED, attribute_id__in=date_attr_ids, row_key__in=row_keys,
    )
    years: set[int] = set()
    for val in qs.values_list('value', flat=True).iterator(chunk_size=5000):
        if val and val[:4].isdigit():
            years.add(int(val[:4]))
    return sorted(years, reverse=True)


def _national_dam_metrics_for_years(years: set[int]) -> dict[date, dict[str, float]]:
    by_name = _title_attrs_by_code(TITLE_NATIONAL)
    date_attr_ids = _date_attr_ids(by_name)
    row_key_dates = _row_keys_for_years(date_attr_ids, years)
    facts_by_rk = _facts_for_row_keys(list(row_key_dates.keys()), by_name)
    by_date: dict[date, dict[str, float]] = {}
    for rk, d in row_key_dates.items():
        facts = facts_by_rk.get(rk, {})
        metrics: dict[str, float] = {}
        for key in ('dams_with_readings', 'dam_storage_avg_mcm', 'dam_storage_total_mcm'):
            num = _parse_number(facts.get(key, ''))
            if num is not None:
                metrics[key] = num
        if metrics:
            by_date.setdefault(d, {}).update(metrics)
    return by_date


def _dam_latest_readings_for_year(year: int) -> dict[int, tuple[date, float]]:
    """Each dam's most recent storage reading within `year` (entity-level Info)."""
    by_name = _title_attrs_by_code(TITLE_DAM_ENTITY)
    date_attr_ids = _date_attr_ids(by_name)
    row_key_dates = _row_keys_for_years(date_attr_ids, {year})
    facts_by_rk = _facts_for_row_keys(list(row_key_dates.keys()), by_name)
    latest: dict[int, tuple[date, float]] = {}
    for rk, d in row_key_dates.items():
        facts = facts_by_rk.get(rk, {})
        eid = facts.get('_entity_id')
        storage = _parse_number(facts.get('storage_mcm', ''))
        if eid is None or storage is None:
            continue
        dam_id = int(eid)
        prev = latest.get(dam_id)
        if prev is None or d > prev[0]:
            latest[dam_id] = (d, storage)
    return latest


def build_dams_info_dashboard(
    *,
    year: int | None = None,
    governorate: str | None = None,
) -> dict[str, Any] | None:
    """Build dams KPIs/charts from national (+ entity) Info. Map filled by caller."""
    if governorate:
        return None

    years = _dam_years_available()
    if not years:
        return None
    selected_year = year if year in years else years[0]
    trend_years = sorted(y for y in years if y >= selected_year - 10)[-11:]
    needed_years = set(trend_years) | {selected_year, selected_year - 1}

    dam_dates = _national_dam_metrics_for_years(needed_years)
    if not dam_dates:
        return None

    year_days = {d: m for d, m in dam_dates.items() if d.year == selected_year}
    if not year_days:
        return None

    latest = max(year_days.keys())
    metrics = year_days[latest]

    # total_storage/delta_pct come from each dam's own latest reading in the year
    # (entity-level Info) rather than the national daily aggregate, so this figure
    # is internally consistent with national_fill/top_dams/the map below — mirrors
    # production's single-source _aggregate_snapshot approach.
    latest_by_dam = _dam_latest_readings_for_year(selected_year)
    total_storage = sum(
        storage for _d, storage in latest_by_dam.values()) if latest_by_dam else None

    prev_latest_by_dam = _dam_latest_readings_for_year(selected_year - 1)
    prev_total = sum(storage for _d, storage in prev_latest_by_dam.values(
    )) if prev_latest_by_dam else None
    delta_pct = None
    if prev_total and prev_total > 0 and total_storage is not None:
        delta_pct = round((total_storage - prev_total) / prev_total * 100, 1)

    annual_values = []
    for y in trend_years:
        yd = {d: m for d, m in dam_dates.items() if d.year == y}
        if not yd:
            annual_values.append(0)
            continue
        ld = max(yd.keys())
        m = yd[ld]
        v = m.get('dam_storage_total_mcm')
        if v is None and m.get('dam_storage_avg_mcm') and m.get('dams_with_readings'):
            v = m['dam_storage_avg_mcm'] * m['dams_with_readings']
        annual_values.append(round(float(v or 0), 2))

    # Individual reading count for the year (distinct from len(latest_by_dam), which
    # dedupes to one — the latest — reading per dam).
    _dam_by_name_for_count = _title_attrs_by_code(TITLE_DAM_ENTITY)
    dam_row_key_dates = _row_keys_for_years(
        _date_attr_ids(_dam_by_name_for_count), {selected_year},
    )

    top_dams: list[dict[str, Any]] = []
    fill_bands = {'critical': 0, 'low': 0,
                  'moderate': 0, 'high': 0, 'unknown': 0}
    if latest_by_dam:
        try:
            from water.models import Dam

            dams = {d.id: d for d in Dam.objects.filter(
                id__in=latest_by_dam.keys())}
            for dam_id, (rd, storage) in latest_by_dam.items():
                dam = dams.get(dam_id)
                max_s = float(
                    dam.max_storage_mcm) if dam and dam.max_storage_mcm else None
                fill = round(storage / max_s * 100,
                             1) if max_s and max_s > 0 else None
                if fill is None:
                    band = 'unknown'
                elif fill < 15:
                    band = 'critical'
                elif fill < 35:
                    band = 'low'
                elif fill < 65:
                    band = 'moderate'
                else:
                    band = 'high'
                fill_bands[band] += 1
                top_dams.append(
                    {
                        'dam_id': dam_id,
                        'name': dam.name if dam else f'Dam {dam_id}',
                        'governorate': dam.governorate if dam else '',
                        'storage_mcm': round(storage, 3),
                        'max_storage_mcm': round(max_s, 3) if max_s else None,
                        'fill_pct': fill,
                        'fill_band': band,
                        'reading_date': rd.isoformat(),
                        'latitude': float(dam.latitude) if dam and dam.latitude else None,
                        'longitude': float(dam.longitude) if dam and dam.longitude else None,
                        'purpose': dam.purpose if dam else '',
                        'dam_type': dam.dam_type if dam else '',
                    }
                )
            top_dams.sort(key=lambda r: r['storage_mcm'], reverse=True)
        except Exception:  # noqa: BLE001
            top_dams = []

    # `dams_with_readings` from the national daily aggregate counts only the single
    # latest date; len(latest_by_dam) is the count with any reading in the whole
    # selected year (matches the map/top_dams scope), so prefer it.
    monitored = len(latest_by_dam) or int(
        metrics.get('dams_with_readings') or 0)
    critical = fill_bands['critical']

    # Two distinct metrics (mirrors production's dams_dashboard.py::_aggregate_snapshot):
    # avg_fill = simple mean of each dam's own fill % (small dams weigh as much as large ones).
    # national_fill = total stored volume / total registered capacity (capacity-weighted).
    avg_fill = None
    fills = [r['fill_pct'] for r in top_dams if r.get('fill_pct') is not None]
    if fills:
        avg_fill = round(sum(fills) / len(fills), 1)

    capacity_rows = [r for r in top_dams if r.get(
        'max_storage_mcm') and r['max_storage_mcm'] > 0]
    total_capacity = sum(r['max_storage_mcm'] for r in capacity_rows)
    total_reported_storage = sum(r['storage_mcm'] for r in top_dams)
    national_fill = (
        round(total_reported_storage / total_capacity *
              100, 1) if total_capacity > 0 else None
    )

    # Per-governorate snapshot: capacity-weighted fill (same formula as the national one),
    # not a simple mean — mirrors production's _gov_totals_from_rows/_aggregate_snapshot.
    by_gov: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in top_dams:
        gov = row.get('governorate') or ''
        if gov:
            by_gov[gov].append(row)

    gov_totals: list[dict[str, Any]] = []
    for gov, gov_rows in by_gov.items():
        gov_storage_total = sum(r['storage_mcm'] for r in gov_rows)
        gov_capacity_rows = [r for r in gov_rows if r.get(
            'max_storage_mcm') and r['max_storage_mcm'] > 0]
        gov_capacity_total = sum(r['max_storage_mcm']
                                 for r in gov_capacity_rows)
        gov_fill = (
            round(gov_storage_total / gov_capacity_total *
                  100, 1) if gov_capacity_total > 0 else None
        )
        gov_totals.append({
            'slug': gov,
            'name_ar': gov,
            'storage_mcm': round(gov_storage_total, 2),
            'fill_pct': gov_fill,
        })
    gov_totals.sort(key=lambda row: row['storage_mcm'], reverse=True)

    insights: list[dict[str, Any]] = []
    if prev_total and prev_total > 0 and total_storage is not None:
        change_pct = round(
            (float(total_storage) - float(prev_total)) / float(prev_total) * 100, 1)
        if change_pct >= 10:
            insights.append({
                'id': 'storage-up',
                'text_en': (
                    f'National stored volume rose {change_pct:+.1f}% vs {selected_year - 1} '
                    f'({float(total_storage):,.1f} million m³).'
                ),
                'text_ar': (
                    f'ارتفع الحجم المخزّن وطنياً بنسبة {change_pct:+.1f}% مقارنة بـ{selected_year - 1} '
                    f'({float(total_storage):,.1f} مليون م³).'
                ),
                'severity': 'info',
            })
        elif change_pct <= -10:
            insights.append({
                'id': 'storage-down',
                'text_en': f'National stored volume fell {change_pct:+.1f}% vs {selected_year - 1} — review supply planning.',
                'text_ar': (
                    f'انخفض الحجم المخزّن وطنياً بنسبة {abs(change_pct):.1f}% مقارنة بـ{selected_year - 1} '
                    f'— راجع خطط الإمداد.'
                ),
                'severity': 'warning',
            })

    if national_fill is not None:
        if national_fill < 25:
            insights.append({
                'id': 'low-national-fill',
                'text_en': f'National fill level is {national_fill:.1f}% of registered capacity — drought stress signal.',
                'text_ar': f'نسبة الامتلاء {national_fill:.1f}% من السعة المسجلة — مؤشر ضغط جفاف.',
                'severity': 'critical' if national_fill < 15 else 'warning',
            })
        elif national_fill >= 60:
            insights.append({
                'id': 'healthy-fill',
                'text_en': f'Reservoirs are at {national_fill:.1f}% of registered capacity — comfortable storage buffer.',
                'text_ar': f'نسبة امتلاء السدود {national_fill:.1f}% من السعة المسجلة — مخزون مريح.',
                'severity': 'info',
            })

    if critical:
        insights.append({
            'id': 'critical-dams',
            'text_en': f'{critical} dam(s) below 15% fill require immediate operational review.',
            'text_ar': f'{critical} سداً أقل من 15% امتلاءً تحتاج مراجعة تشغيلية فورية.',
            'severity': 'critical',
        })

    if gov_totals and not governorate:
        lowest = min(
            gov_totals, key=lambda r: r['fill_pct'] if r['fill_pct'] is not None else 999)
        highest = max(gov_totals, key=lambda r: r['storage_mcm'])
        if lowest.get('fill_pct') is not None:
            insights.append({
                'id': 'gov-contrast',
                'text_en': (
                    f'{lowest["name_ar"]} shows the lowest average fill ({lowest["fill_pct"]:.1f}%) '
                    f'while {highest["name_ar"]} holds the largest stored volume '
                    f'({highest["storage_mcm"]:,.1f} MCM).'
                ),
                'text_ar': (
                    f'{lowest["name_ar"]} تسجل أدنى متوسط امتلاء ({lowest["fill_pct"]:.1f}%) '
                    f'بينما {highest["name_ar"]} تحتفظ بأكبر حجم مخزّن '
                    f'({highest["storage_mcm"]:,.1f} مليون متر مكعب).'
                ),
                'severity': 'info',
            })

    critical_rows = sorted(
        [r for r in top_dams if r.get('fill_band') in (
            'critical', 'low') and r.get('fill_pct') is not None],
        key=lambda r: r['fill_pct'] or 0,
    )[:1]
    for row in critical_rows:
        insights.append({
            'id': f'dam-{row["dam_id"]}-low',
            'text_en': (
                f'{row["name"]} ({row.get("governorate", "")}) at {row["fill_pct"]:.1f}% '
                f'({row["storage_mcm"]:.2f} / {(row.get("max_storage_mcm") or 0):.2f} MCM).'
            ),
            'text_ar': (
                f'{row["name"]} ({row.get("governorate", "")}) عند {row["fill_pct"]:.1f}% '
                f'({row["storage_mcm"]:.2f} / {(row.get("max_storage_mcm") or 0):.2f} مليون متر مكعب).'
            ),
            'severity': 'critical' if row['fill_band'] == 'critical' else 'warning',
        })

    if not insights:
        insights.append({
            'id': 'placeholder',
            'text_en': 'Dam KPIs from accepted Info aggregates.',
            'text_ar': 'مؤشرات السدود من مجاميع Info المعتمدة.',
            'severity': 'info',
        })
    insights = insights[:6]

    return {
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': water_category_name(),
        'data_through': latest.isoformat(),
        'readings_count': len(dam_row_key_dates),
        'dams_with_data_count': monitored,
        'filters': {
            'years': years,
            'governorates': [],
        },
        'selected_year': selected_year,
        'selected_governorate': governorate,
        'kpis': [
            _kpi(
                kpi_id='total-storage',
                label_en='Total stored volume',
                label_ar='إجمالي المخزون',
                value=round(float(total_storage),
                            2) if total_storage is not None else None,
                unit='MCM',
                delta_pct=delta_pct,
                status='ok' if (delta_pct or 0) >= 0 else 'warning',
            ),
            _kpi(
                kpi_id='national-fill',
                label_en='National fill level',
                label_ar='نسبة الامتلاء',
                value=national_fill,
                unit='%',
                status='critical' if (
                    national_fill or 100) < 20 else 'neutral',
            ),
            _kpi(
                kpi_id='monitored-dams',
                label_en='Monitored dams',
                label_ar='السدود المراقبة',
                value=monitored,
            ),
            _kpi(
                kpi_id='critical-dams',
                label_en='Critical dams (<15%)',
                label_ar='سدود قاربت للحد الميت (<15%)',
                value=critical,
                status='critical' if critical else 'ok',
            ),
            _kpi(
                kpi_id='avg-fill',
                label_en='Average dam fill',
                label_ar='متوسط امتلاء السدود',
                value=avg_fill if avg_fill is not None else metrics.get(
                    'dam_storage_avg_mcm'),
                unit='%' if avg_fill is not None else 'MCM',
            ),
        ],
        'insights': insights,
        'charts': {
            'annual_trend': {'labels': [str(y) for y in trend_years], 'values': annual_values},
            'fill_distribution': {
                'labels_en': [
                    'Critical (<15%)',
                    'Low (15–35%)',
                    'Moderate (35–65%)',
                    'High (>65%)',
                    'Unknown',
                ],
                'labels_ar': [
                    'قاربت للحد الميت (<15%)',
                    'منخفض (15–35%)',
                    'متوسط (35–65%)',
                    'مرتفع (>65%)',
                    'غير معروف',
                ],
                'values': [
                    fill_bands['critical'],
                    fill_bands['low'],
                    fill_bands['moderate'],
                    fill_bands['high'],
                    fill_bands['unknown'],
                ],
            },
            'governorate_comparison': {
                'labels_en': [],
                'labels_ar': [row['name_ar'] for row in gov_totals[:10]],
                'values': [row['storage_mcm'] for row in gov_totals[:10]],
            },
            'top_dams': top_dams[:10],
        },
        'map': {
            'dams': [
                row
                for row in top_dams
                if row.get('latitude') is not None and row.get('longitude') is not None
            ]
        },
    }


def _dam_latest_row_keys_all_time() -> dict[int, tuple[Any, date]]:
    """dam_id -> (winning row_key, latest date), across every year.

    Queries only the (small) date-attribute Info rows — one per dam per date,
    not one per dam per date per metric — to find each dam's latest reading
    cheaply, before fetching full facts for just those winning row_keys.
    """
    by_name = _title_attrs_by_code(TITLE_DAM_ENTITY)
    date_attr_ids = _date_attr_ids(by_name)
    if not date_attr_ids:
        return {}
    qs = ReportDynamicFormsInfo.objects.filter(
        confirmed=ACCEPTED, attribute_id__in=date_attr_ids,
    )
    latest: dict[int, tuple[Any, date]] = {}
    for rk, eid, val in qs.values_list('row_key', 'entity_id', 'value').iterator(chunk_size=5000):
        if eid is None:
            continue
        d = _parse_date(val)
        if d is None:
            continue
        dam_id = int(eid)
        prev = latest.get(dam_id)
        if prev is None or d > prev[1]:
            latest[dam_id] = (rk, d)
    return latest


def _dam_latest_readings_all_time() -> dict[int, tuple[date, float]]:
    """Each dam's most recent storage reading across all years (for map popups)."""
    by_name = _title_attrs_by_code(TITLE_DAM_ENTITY)
    latest_rk = _dam_latest_row_keys_all_time()
    if not latest_rk:
        return {}
    row_keys = [rk for rk, _ in latest_rk.values()]
    facts_by_rk = _facts_for_row_keys(row_keys, by_name)
    latest: dict[int, tuple[date, float]] = {}
    for dam_id, (rk, d) in latest_rk.items():
        facts = facts_by_rk.get(rk, {})
        storage = _parse_number(facts.get('storage_mcm', ''))
        if storage is not None:
            latest[dam_id] = (d, storage)
    return latest


def build_dams_map_catalog_info() -> dict[str, Any]:
    """Lightweight dam list for portal map popups: asset fields from the Dam
    master table, storage/fill/reading_date from Info exclusively."""
    from water.models import Dam

    latest = _dam_latest_readings_all_time()
    dams: list[dict[str, Any]] = []
    for dam in Dam.objects.all().order_by('governorate', 'name'):
        reading = latest.get(dam.id)
        storage = reading[1] if reading else None
        max_storage = float(
            dam.max_storage_mcm) if dam.max_storage_mcm else None
        fill = (
            round(storage / max_storage * 100, 1)
            if storage is not None and max_storage and max_storage > 0
            else None
        )
        dams.append({
            'dam_id': dam.id,
            'name': dam.name,
            'governorate': dam.governorate,
            'latitude': float(dam.latitude) if dam.latitude else None,
            'longitude': float(dam.longitude) if dam.longitude else None,
            'dam_type': dam.dam_type,
            'purpose': dam.purpose,
            'height_m': float(dam.height_m) if dam.height_m else None,
            'length_m': float(dam.length_m) if dam.length_m else None,
            'max_storage_mcm': round(max_storage, 3) if max_storage else None,
            'dead_storage_mcm': float(dam.dead_storage_mcm) if dam.dead_storage_mcm else None,
            'built_year': dam.built_year,
            'status_note': dam.status_note,
            'storage_mcm': round(storage, 3) if storage is not None else None,
            'fill_pct': fill,
            'reading_date': reading[0].isoformat() if reading else None,
        })
    return {'dams': dams}


def build_euphrates_info_dashboard(*, month: str | None = None) -> dict[str, Any] | None:
    infos, attrs, titles = _load_title_context(TITLE_EUPHRATES)
    rows = _row_facts(infos, attrs, titles, TITLE_EUPHRATES)
    by_date: dict[date, dict[str, Any]] = {}
    for facts in rows.values():
        d = _facts_date(facts)
        if d is None:
            continue
        metrics: dict[str, Any] = {}
        for key, raw in facts.items():
            if key.startswith('_'):
                continue
            if key == 'report_label':
                metrics[key] = raw
                continue
            num = _parse_number(raw)
            if num is not None:
                metrics[key] = num
        if metrics:
            by_date[d] = metrics
    if not by_date:
        return None

    months = sorted({d.strftime('%Y-%m') for d in by_date}, reverse=True)
    selected_month = month if month in months else months[0]
    year_i, mon_i = (int(p) for p in selected_month.split('-'))
    month_days = sorted(
        [d for d in by_date if d.year == year_i and d.month == mon_i]
    )
    if not month_days:
        return None

    readings = [(d, by_date[d]) for d in month_days]
    latest_d, latest = readings[-1]
    prev = readings[-2][1] if len(readings) > 1 else None
    labels = [d.isoformat() for d, _ in readings]
    day_labels = [str(d.day) for d, _ in readings]

    def series(key: str) -> list[float | None]:
        return [m.get(key) for _, m in readings]

    def cascade_storage() -> list[float | None]:
        out: list[float | None] = []
        for _, m in readings:
            f = m.get('furat_storage_mcm')
            t = m.get('tishreen_storage_mcm')
            if f is None and t is None:
                out.append(None)
            else:
                out.append(round((f or 0) + (t or 0), 2))
        return out

    cascade = cascade_storage()
    kpis = [
        _kpi(
            kpi_id='jarabulus-inflow',
            label_en='Jarabulus inflow',
            label_ar='وارد جرابلس',
            value=latest.get('inflow_jarabulus'),
            unit='m³/s',
        ),
        _kpi(
            kpi_id='furat-level',
            label_en='Euphrates lake level',
            label_ar='منسوب بحيرة الفرات',
            value=latest.get('furat_level_m'),
            unit='m',
            delta_pct=(
                round(
                    (latest['furat_level_m'] - prev['furat_level_m'])
                    / prev['furat_level_m']
                    * 100,
                    2,
                )
                if prev
                and latest.get('furat_level_m')
                and prev.get('furat_level_m')
                else None
            ),
        ),
        _kpi(
            kpi_id='tishreen-level',
            label_en='Tishreen dam level',
            label_ar='منسوب سد تشرين',
            value=latest.get('tishreen_level_m'),
            unit='m',
        ),
        _kpi(
            kpi_id='total-generation',
            label_en='Total daily generation',
            label_ar='إجمالي التوليد اليومي',
            value=latest.get('total_generation_mwh'),
            unit='MWh',
            status='ok',
        ),
        _kpi(
            kpi_id='furat-storage',
            label_en='Cascade lake storage',
            label_ar='تخزين بحيرات السلسلة',
            value=cascade[-1] if cascade else None,
            unit='BCM',
        ),
    ]

    return {
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': water_category_name(),
        'data_through': latest_d.isoformat(),
        'readings_count': len(readings),
        'report_label': str(latest.get('report_label') or ''),
        'filters': {'months': months},
        'selected_month': selected_month,
        'kpis': kpis,
        'insights': [
            {
                'id': 'info-source',
                'text_en': 'Euphrates cascade from accepted Info.',
                'text_ar': 'سلسلة الفرات من Info المعتمد.',
                'severity': 'info',
            }
        ],
        'month_summary': {},
        'executive': {
            'labels': day_labels,
            'inflow': {'values': series('inflow_jarabulus')},
            'generation': {'values': series('total_generation_mwh')},
            'storage': {'values': cascade},
        },
        'charts': {
            'inflow': {'labels': labels, 'values': series('inflow_jarabulus')},
            'levels': {
                'labels': labels,
                'series': [
                    {
                        'key': 'tishreen',
                        'label_en': 'Tishreen',
                        'label_ar': 'تشرين',
                        'values': series('tishreen_level_m'),
                    },
                    {
                        'key': 'furat',
                        'label_en': 'Euphrates lake',
                        'label_ar': 'بحيرة الفرات',
                        'values': series('furat_level_m'),
                    },
                ],
            },
            'generation': {
                'labels': labels,
                'series': [
                    {
                        'key': 'tishreen',
                        'label_en': 'Tishreen',
                        'label_ar': 'تشرين',
                        'values': series('tishreen_generation_mwh'),
                    },
                    {
                        'key': 'furat',
                        'label_en': 'Euphrates',
                        'label_ar': 'الفرات',
                        'values': series('furat_generation_mwh'),
                    },
                    {
                        'key': 'kadiran',
                        'label_en': 'Kadiran',
                        'label_ar': 'كديران',
                        'values': series('kadiran_generation_mwh'),
                    },
                    {
                        'key': 'total',
                        'label_en': 'Total',
                        'label_ar': 'الإجمالي',
                        'values': series('total_generation_mwh'),
                    },
                ],
            },
            'storage': {
                'labels': labels,
                'series': [
                    {
                        'key': 'tishreen',
                        'label_en': 'Tishreen',
                        'label_ar': 'تشرين',
                        'values': series('tishreen_storage_mcm'),
                    },
                    {
                        'key': 'furat',
                        'label_en': 'Euphrates',
                        'label_ar': 'الفرات',
                        'values': series('furat_storage_mcm'),
                    },
                ],
            },
        },
        'dams': [
            {
                'slug': 'tishreen',
                'name_en': 'Tishreen Dam',
                'name_ar': 'سد تشرين',
                'level_m': latest.get('tishreen_level_m'),
                'storage_bcm': latest.get('tishreen_storage_mcm'),
                'outflow': latest.get('tishreen_outflow'),
                'generation_mwh': latest.get('tishreen_generation_mwh'),
                'max_storage_bcm': 1.883,
            },
            {
                'slug': 'furat',
                'name_en': 'Euphrates Dam (Tabqa)',
                'name_ar': 'سد الفرات (طبقة)',
                'level_m': latest.get('furat_level_m'),
                'storage_bcm': latest.get('furat_storage_mcm'),
                'outflow': latest.get('furat_outflow'),
                'generation_mwh': latest.get('furat_generation_mwh'),
                'max_storage_bcm': 14.1,
            },
            {
                'slug': 'kadiran',
                'name_en': 'Kadiran Dam',
                'name_ar': 'سد كديران',
                'level_m': None,
                'storage_bcm': None,
                'outflow': latest.get('kadiran_outflow'),
                'generation_mwh': latest.get('kadiran_generation_mwh'),
                'max_storage_bcm': 0.09,
            },
        ],
        'readings_table': [
            {
                'date': d.isoformat(),
                'inflow_jarabulus': m.get('inflow_jarabulus'),
                'tishreen_level_m': m.get('tishreen_level_m'),
                'furat_level_m': m.get('furat_level_m'),
                'tishreen_storage_bcm': m.get('tishreen_storage_mcm'),
                'furat_storage_bcm': m.get('furat_storage_mcm'),
                'cascade_storage_bcm': (
                    round(
                        (m.get('furat_storage_mcm') or 0)
                        + (m.get('tishreen_storage_mcm') or 0),
                        2,
                    )
                    if m.get('furat_storage_mcm') is not None
                    or m.get('tishreen_storage_mcm') is not None
                    else None
                ),
                'tishreen_outflow': m.get('tishreen_outflow'),
                'furat_outflow': m.get('furat_outflow'),
                'kadiran_outflow': m.get('kadiran_outflow'),
                'tishreen_generation_mwh': m.get('tishreen_generation_mwh'),
                'furat_generation_mwh': m.get('furat_generation_mwh'),
                'kadiran_generation_mwh': m.get('kadiran_generation_mwh'),
                'total_generation_mwh': m.get('total_generation_mwh'),
            }
            for d, m in reversed(readings)
        ],
    }


def drinking_station_info_facts() -> dict[int, dict[str, str]]:
    """Bulk-load every accepted Info row for `water.drinking_station_entity`, grouped
    by station id (`entity_id`) -> {Attribute.key: value}.

    One query for the whole title (~5,710 stations x ~29 keys ~= 150k rows), grouped
    in Python — NOT a per-station query loop. Boolean-typed keys are left as the raw
    'true'/'false' strings Info stores them as; callers parse to Python bool.
    """
    by_key = _title_attrs_by_code(TITLE_DRINKING_STATION_ENTITY)
    # Build attribute_id -> key, skipping the synthetic '_date' alias (assessment_date
    # is a `type='date'` attribute so it's also aliased under '_date' by
    # `_title_attrs_by_code`; skipping avoids two keys racing to own the same id).
    attr_key_by_id = {attr.id: key for key,
                      attr in by_key.items() if key != '_date'}
    if not attr_key_by_id:
        return {}
    try:
        qs = ReportDynamicFormsInfo.objects.filter(
            confirmed=ACCEPTED,
            attribute_id__in=attr_key_by_id.keys(),
            entity_type=DRINKING_STATION_ENTITY_TYPE,
        )
        if hasattr(ReportDynamicFormsInfo, 'archived'):
            qs = qs.filter(archived=False)
        rows = qs.values_list('entity_id', 'attribute_id',
                              'value').iterator(chunk_size=5000)
        facts: dict[int, dict[str, str]] = defaultdict(dict)
        for entity_id, attribute_id, value in rows:
            if entity_id is None:
                continue
            key = attr_key_by_id.get(attribute_id)
            if not key:
                continue
            facts[int(entity_id)][key] = value or ''
    except DatabaseError:
        return {}
    return dict(facts)


def apply_drinking_info_kpis(payload: dict[str, Any]) -> dict[str, Any]:
    """Replace drinking-water summary KPIs from national Info when present."""
    by_date = _national_metrics_by_date()
    drinking_dates = {
        d: m
        for d, m in by_date.items()
        if 'drinking_stations_total' in m or 'drinking_stations_operational' in m
    }
    out = dict(payload)
    if not drinking_dates:
        out.setdefault('source', 'legacy')
        return out

    latest = max(drinking_dates.keys())
    metrics = drinking_dates[latest]
    total = metrics.get('drinking_stations_total')
    operational = metrics.get('drinking_stations_operational')
    # Keep filter-dependent charts/map/table from legacy; swap core count KPIs when unfiltered.
    if not out.get('selected_governorate') and not out.get('selected_district'):
        new_kpis = []
        for kpi in out.get('kpis') or []:
            kid = kpi.get('id')
            if kid == 'total-stations' and total is not None:
                new_kpis.append({**kpi, 'value': int(total)})
            else:
                new_kpis.append(kpi)
        # Append operational KPI if missing
        if operational is not None and not any(
            k.get('id') == 'operational-stations' for k in new_kpis
        ):
            new_kpis.insert(
                1,
                _kpi(
                    kpi_id='operational-stations',
                    label_en='Operational stations',
                    label_ar='محطات عاملة',
                    value=int(operational),
                ),
            )
        out['kpis'] = new_kpis
        out['source'] = 'dynamic_forms'
        out['info_report_date'] = latest.isoformat()
    else:
        out.setdefault('source', 'legacy')
    return out
