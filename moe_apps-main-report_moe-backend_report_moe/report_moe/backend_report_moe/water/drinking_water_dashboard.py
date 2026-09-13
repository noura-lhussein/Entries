from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal
from typing import Any

from django.db import connection
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear

from .info_dashboard import drinking_station_info_facts
from .models import DrinkingWaterStation

# Assessment/condition fields that now live exclusively in Info (keyed by station id),
# not on DrinkingWaterStation anymore — see module docstring/PR notes. Station identity
# and geography (station_code, name, governorate, district, ..., lat/lon) stay on the
# legacy model and are still queried via the ORM as before.
BOOL_INFO_KEYS = (
    'is_operational',
    'is_boosting_station',
    'is_well_station',
    'is_filtration_station',
    'needs_solar_power',
    'has_grid_power',
    'previously_rehabilitated',
    'has_water_hammer_protection',
    'has_public_grid_supply',
    'grid_connection_working',
    'solar_power_available',
    'needs_solar_installation',
    'generator_available',
    'alternative_power_source',
    'solar_space_available',
    'is_water_analyzed',
    'has_water_tanks',
)
CHOICE_INFO_KEYS = (
    'non_operational_reason',
    'building_condition',
    'safety_procedures',
    'rehabilitation_type',
    'water_hammer_efficiency',
    'electrical_connection_efficiency',
    'electrical_panel_efficiency',
    'transformer_efficiency',
    'solar_system_efficiency',
    'grid_power_productivity',
    'solar_power_productivity',
    'lab_equipment_status',
)


def _fact_bool(facts: dict[str, str], key: str) -> bool | None:
    """Parse a Info boolean cell ('true'/'false' strings, or missing/blank = unknown)."""
    raw = facts.get(key)
    if raw is None or raw == '':
        return None
    return raw == 'true'


def _fact_str(facts: dict[str, str], key: str) -> str:
    return facts.get(key) or ''


def _rows_for_ids(
    station_ids: list[int],
    governorates: dict[int, str],
    info_by_station: dict[int, dict[str, str]],
) -> list[tuple[int, str, dict[str, str]]]:
    """(station_id, governorate, facts) tuples — the shared shape every chart helper
    below aggregates over in Python, since the condition fields no longer live on the
    ORM model. Stations with no Info rows at all fall back to an empty facts dict
    (every field reads as unknown/None), not a crash."""
    return [
        (sid, governorates.get(sid, ''), info_by_station.get(sid, {}))
        for sid in station_ids
    ]

GOVERNORATE_AR: dict[str, str] = {
    'Damascus': 'دمشق',
    'Rural Damascus': 'ريف دمشق',
    'Hama': 'حماة',
    "Dar'a": 'درعا',
    'Al-Hasakeh': 'الحسكة',
    'Aleppo': 'حلب',
    'Homs': 'حمص',
    'As-Sweida': 'السويداء',
    'Idleb': 'إدلب',
    'Tartous': 'طرطوس',
    'Lattakia': 'اللاذقية',
    'Deir-ez-Zor': 'دير الزور',
    'Quneitra': 'القنيطرة',
    'Ar-Raqqa': 'الرقة',
}

GOVERNORATE_ORDER = (
    'Aleppo',
    'Al-Hasakeh',
    'Ar-Raqqa',
    'As-Sweida',
    'Damascus',
    "Dar'a",
    'Deir-ez-Zor',
    'Hama',
    'Homs',
    'Idleb',
    'Lattakia',
    'Quneitra',
    'Rural Damascus',
    'Tartous',
)

PBI_COLORS = [
    '#118DFF',
    '#12239E',
    '#E66C37',
    '#6B007B',
    '#E044A7',
    '#744EC2',
    '#D9B300',
    '#D64550',
    '#197278',
    '#1AAB40',
    '#15C6F4',
    '#4096FF',
    '#8C8C8C',
    '#0D3B66',
]


def _float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _kpi(
    *,
    kpi_id: str,
    label_en: str,
    label_ar: str,
    value: float | int | None,
    unit: str = '',
    status: str = 'neutral',
) -> dict[str, Any]:
    return {
        'id': kpi_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'unit': unit,
        'delta_pct': None,
        'status': status,
    }


def _filter_option(slug: str, count: int) -> dict[str, Any]:
    return {
        'slug': slug,
        'name_en': slug,
        'name_ar': GOVERNORATE_AR.get(slug, slug),
        'count': count,
    }


def _station_row(
    station: DrinkingWaterStation,
    *,
    info_by_station: dict[int, dict[str, str]],
    district_ar_map: dict[str, str] | None = None,
    subdistrict_ar_map: dict[str, str] | None = None,
    community_ar_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    district = station.district
    subdistrict = station.subdistrict
    community = station.community
    district_labels = district_ar_map or {}
    subdistrict_labels = subdistrict_ar_map or {}
    community_labels = community_ar_map or {}
    facts = info_by_station.get(station.id, {})
    return {
        'id': station.id,
        'station_code': station.station_code,
        'name': station.name,
        'governorate': station.governorate,
        'governorate_ar': GOVERNORATE_AR.get(station.governorate, station.governorate),
        'district': district,
        'district_ar': district_labels.get(district, district) if district else '',
        'subdistrict': subdistrict,
        'subdistrict_ar': subdistrict_labels.get(subdistrict, subdistrict) if subdistrict else '',
        'community': community,
        'community_ar': community_labels.get(community, community) if community else '',
        'address': station.address,
        'org_unit': station.org_unit,
        'enrollment_date': station.enrollment_date.isoformat() if station.enrollment_date else None,
        'incident_date': station.incident_date.isoformat() if station.incident_date else None,
        'is_operational': _fact_bool(facts, 'is_operational'),
        'is_boosting_station': _fact_bool(facts, 'is_boosting_station'),
        'is_well_station': _fact_bool(facts, 'is_well_station'),
        'is_filtration_station': _fact_bool(facts, 'is_filtration_station'),
        'needs_solar_power': _fact_bool(facts, 'needs_solar_power'),
        'has_grid_power': _fact_bool(facts, 'has_grid_power'),
        'latitude': _float(station.latitude),
        'longitude': _float(station.longitude),
    }


def _parse_bool_choices(value: str | None) -> tuple[bool, bool]:
    if not value:
        return False, False
    parts = {part.strip().lower() for part in value.split(',') if part.strip()}
    return ('yes' in parts or 'true' in parts, 'no' in parts or 'false' in parts)


def _bool_choice_ids(
    station_ids: list[int],
    info_by_station: dict[int, dict[str, str]],
    key: str,
    yes: bool,
    no: bool,
) -> set[int] | None:
    """Tri-state semantics preserved exactly: yes+no both selected, or neither, means
    'no filter' (returns None); yes-only/no-only narrows to that boolean value.
    Returns a station-id set (never None) once actually filtering."""
    if not yes and not no:
        return None
    if yes and no:
        return None
    want = yes
    return {
        sid for sid in station_ids
        if _fact_bool(info_by_station.get(sid, {}), key) is want
    }


def _parse_choice_filter(value: str | None, allowed: tuple[str, ...]) -> set[str]:
    if not value:
        return set()
    parts = {part.strip().lower() for part in value.split(',') if part.strip()}
    return {part for part in parts if part in allowed}


def _choice_filter_ids(
    station_ids: list[int],
    info_by_station: dict[int, dict[str, str]],
    key: str,
    selected: set[str],
) -> set[int] | None:
    if not selected:
        return None
    return {
        sid for sid in station_ids
        if _fact_str(info_by_station.get(sid, {}), key).lower() in selected
    }


def _apply_all_filters(
    qs,
    *,
    info_by_station: dict[int, dict[str, str]],
    governorate: str | None = None,
    district: str | None = None,
    subdistrict: str | None = None,
    org_unit: str | None = None,
    community: str | None = None,
    enrollment_year: int | None = None,
    search: str | None = None,
    station_working: tuple[bool, bool] = (False, False),
    boosting_station: tuple[bool, bool] = (False, False),
    well_station: tuple[bool, bool] = (False, False),
    filtration_station: tuple[bool, bool] = (False, False),
    needs_solar_power: tuple[bool, bool] = (False, False),
    grid_power: tuple[bool, bool] = (False, False),
    safety_procedures: set[str] | None = None,
    previously_rehabilitated: tuple[bool, bool] = (False, False),
    public_grid_supply: tuple[bool, bool] = (False, False),
    grid_connection_working: tuple[bool, bool] = (False, False),
    electrical_connection_efficiency: set[str] | None = None,
    solar_power_available: tuple[bool, bool] = (False, False),
    alternative_power_source: tuple[bool, bool] = (False, False),
    needs_solar_installation: tuple[bool, bool] = (False, False),
    solar_space_available: tuple[bool, bool] = (False, False),
):
    """Shared by the dashboard (which pre-applies governorate/district/subdistrict/org_unit/
    community itself while building cascading dropdown options, so leaves those at None here)
    and the paginated stations-list endpoint (which has no dropdown options to build and so
    passes every filter through this one function).

    Identity/geography filters still run in SQL against DrinkingWaterStation. The moved
    condition fields no longer exist as model columns, so each is resolved to a station-id
    set against the preloaded Info facts dict in Python first, then applied as a single
    `id__in` intersection.
    """
    if governorate:
        qs = qs.filter(governorate=governorate)
    if district:
        qs = qs.filter(district=district)
    if subdistrict:
        qs = qs.filter(subdistrict=subdistrict)
    if org_unit:
        qs = qs.filter(org_unit=org_unit)
    if community:
        qs = qs.filter(community=community)
    if enrollment_year:
        qs = qs.filter(
            enrollment_date__gte=date(enrollment_year, 1, 1),
            enrollment_date__lt=date(enrollment_year + 1, 1, 1),
        )
    if search:
        term = search.strip()
        qs = qs.filter(
            Q(name__icontains=term)
            | Q(station_code__icontains=term)
            | Q(community__icontains=term)
            | Q(address__icontains=term)
        )

    station_ids = list(qs.values_list('id', flat=True))
    constraint: set[int] | None = None

    def _intersect(ids: set[int] | None) -> None:
        nonlocal constraint
        if ids is None:
            return
        constraint = ids if constraint is None else (constraint & ids)

    _intersect(_bool_choice_ids(station_ids, info_by_station, 'is_operational', *station_working))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'is_boosting_station', *boosting_station))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'is_well_station', *well_station))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'is_filtration_station', *filtration_station))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'needs_solar_power', *needs_solar_power))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'has_public_grid_supply', *grid_power))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'has_public_grid_supply', *public_grid_supply))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'grid_connection_working', *grid_connection_working))
    _intersect(_choice_filter_ids(
        station_ids, info_by_station, 'electrical_connection_efficiency',
        electrical_connection_efficiency or set(),
    ))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'solar_power_available', *solar_power_available))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'alternative_power_source', *alternative_power_source))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'needs_solar_installation', *needs_solar_installation))
    _intersect(_bool_choice_ids(station_ids, info_by_station, 'solar_space_available', *solar_space_available))
    _intersect(_choice_filter_ids(station_ids, info_by_station, 'safety_procedures', safety_procedures or set()))
    _intersect(_bool_choice_ids(
        station_ids, info_by_station, 'previously_rehabilitated', *previously_rehabilitated,
    ))

    if constraint is not None:
        qs = qs.filter(id__in=constraint)
    return qs


def list_drinking_water_stations(
    *,
    offset: int = 0,
    limit: int = 50,
    governorate: str | None = None,
    district: str | None = None,
    subdistrict: str | None = None,
    org_unit: str | None = None,
    community: str | None = None,
    enrollment_year: int | None = None,
    search: str | None = None,
    station_working: tuple[bool, bool] = (False, False),
    boosting_station: tuple[bool, bool] = (False, False),
    well_station: tuple[bool, bool] = (False, False),
    filtration_station: tuple[bool, bool] = (False, False),
    needs_solar_power: tuple[bool, bool] = (False, False),
    grid_power: tuple[bool, bool] = (False, False),
    safety_procedures: set[str] | None = None,
    previously_rehabilitated: tuple[bool, bool] = (False, False),
    public_grid_supply: tuple[bool, bool] = (False, False),
    grid_connection_working: tuple[bool, bool] = (False, False),
    electrical_connection_efficiency: set[str] | None = None,
    solar_power_available: tuple[bool, bool] = (False, False),
    alternative_power_source: tuple[bool, bool] = (False, False),
    needs_solar_installation: tuple[bool, bool] = (False, False),
    solar_space_available: tuple[bool, bool] = (False, False),
) -> dict[str, Any]:
    """Paginated station rows for the table's infinite scroll. Same filter set as the
    dashboard, applied directly — there's no cascading dropdown-options scope to reuse
    here since this endpoint only ever returns rows, not filter option lists."""
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    info_by_station = drinking_station_info_facts()
    base_qs = DrinkingWaterStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    filtered = _apply_all_filters(
        base_qs,
        info_by_station=info_by_station,
        governorate=governorate,
        district=district,
        subdistrict=subdistrict,
        org_unit=org_unit,
        community=community,
        enrollment_year=enrollment_year,
        search=search,
        station_working=station_working,
        boosting_station=boosting_station,
        well_station=well_station,
        filtration_station=filtration_station,
        needs_solar_power=needs_solar_power,
        grid_power=grid_power,
        safety_procedures=safety_procedures,
        previously_rehabilitated=previously_rehabilitated,
        public_grid_supply=public_grid_supply,
        grid_connection_working=grid_connection_working,
        electrical_connection_efficiency=electrical_connection_efficiency,
        solar_power_available=solar_power_available,
        alternative_power_source=alternative_power_source,
        needs_solar_installation=needs_solar_installation,
        solar_space_available=solar_space_available,
    )

    total = filtered.count()
    # Stable order (governorate/name ties broken by id) so consecutive scroll-triggered
    # pages never skip or repeat a row.
    page_qs = list(
        filtered.order_by('governorate', 'name', 'id').only(
            'id',
            'station_code',
            'name',
            'governorate',
            'district',
            'subdistrict',
            'community',
            'address',
            'org_unit',
            'enrollment_date',
            'incident_date',
            'latitude',
            'longitude',
        )[offset : offset + limit]
    )

    district_ar_map = _admin_name_ar_map('district', {s.district for s in page_qs if s.district})
    subdistrict_ar_map = _admin_name_ar_map('subdistrict', {s.subdistrict for s in page_qs if s.subdistrict})
    community_ar_map = _admin_name_ar_map(
        'populated-places', {s.community for s in page_qs if s.community},
    )

    rows = [
        _station_row(
            station,
            info_by_station=info_by_station,
            district_ar_map=district_ar_map,
            subdistrict_ar_map=subdistrict_ar_map,
            community_ar_map=community_ar_map,
        )
        for station in page_qs
    ]

    return {'stations': rows, 'total': total, 'offset': offset, 'limit': limit}


NON_OPERATIONAL_REASON_LABELS: dict[str, tuple[str, str]] = {
    'other': ('Other reasons', 'أسباب أخرى'),
    'theft_vandalism': ('Theft & Vandalism', 'سرقة وتخريب'),
    'completely_destroyed': ('Completely destroyed', 'مدمرة بالكامل'),
    'emergency_maintenance': ('Requires emergency maintenance', 'تحتاج صيانة طارئة'),
    'administrative': ('Administrative reasons', 'أسباب إدارية'),
    'routine_maintenance': ('Requires routine maintenance', 'تحتاج صيانة دورية'),
    'ongoing_maintenance': ('Ongoing maintenance', 'صيانة جارية'),
}

BUILDING_CONDITION_LABELS: dict[str, tuple[str, str]] = {
    '1': ('1 - Bad', '1 - سيء'),
    '2': ('2 - Medium', '2 - متوسط'),
    '3': ('3 - No intervention needed', '3 - لا حاجة للتدخل'),
}

SAFETY_PROCEDURE_LABELS: dict[str, tuple[str, str]] = {
    'no': ('No', 'لا'),
    'partially': ('Partially', 'جزئياً'),
    'yes': ('Yes', 'نعم'),
}

REHABILITATION_TYPE_LABELS: dict[str, tuple[str, str]] = {
    'partial': ('Partial Rehabilitation', 'تأهيل جزئي'),
    'complete': ('Complete Rehabilitation', 'تأهيل كامل'),
}

WATER_HAMMER_EFFICIENCY_LABELS: dict[str, tuple[str, str]] = {
    '1': ('1 - Requires replacement', '1 - يحتاج استبدال'),
    '2': ('2 - Requires partial maintenance', '2 - يحتاج صيانة جزئية'),
    '3': ('3 - No intervention needed', '3 - لا حاجة للتدخل'),
}

NON_OPERATIONAL_REASON_ORDER = (
    'other',
    'theft_vandalism',
    'completely_destroyed',
    'emergency_maintenance',
    'administrative',
    'routine_maintenance',
    'ongoing_maintenance',
)
BUILDING_CONDITION_ORDER = ('1', '2', '3')
SAFETY_PROCEDURE_ORDER = ('no', 'partially', 'yes')
REHABILITATION_TYPE_ORDER = ('partial', 'complete')
WATER_HAMMER_EFFICIENCY_ORDER = ('1', '2', '3')

EFFICIENCY_LABELS: dict[str, tuple[str, str]] = {
    '1': ('1 - Requires replacement', '1 - يحتاج استبدال'),
    '2': ('2 - Requires regular maintenance', '2 - يحتاج صيانة دورية'),
    '3': ('3 - No intervention needed', '3 - لا حاجة للتدخل'),
}
EFFICIENCY_ORDER = ('1', '2', '3')

PRODUCTIVITY_LABELS: dict[str, tuple[str, str]] = {
    '0': ('0', '0'),
    '1_25': ('1-25', '1-25'),
    '26_50': ('26-50', '26-50'),
    '51_75': ('51-75', '51-75'),
    '76_99': ('76-99', '76-99'),
    '100': ('Full (100%)', 'كامل (100%)'),
}
PRODUCTIVITY_ORDER = ('0', '1_25', '26_50', '51_75', '76_99', '100')

PBI_STATUS_COLORS = {
    'no': '#E66C37',
    'yes': '#1AAB40',
    'partially': '#D9B300',
    '1': '#8C8C8C',
    '2': '#D9B300',
    '3': '#1AAB40',
    'other': '#1AAB40',
    'theft_vandalism': '#1AAB40',
    'completely_destroyed': '#D64550',
    'emergency_maintenance': '#1AAB40',
    'administrative': '#1AAB40',
    'routine_maintenance': '#1AAB40',
    'ongoing_maintenance': '#1AAB40',
    'partial': '#D9B300',
    'complete': '#1AAB40',
}


ADMIN_FIELD_LAYER: dict[str, str] = {
    'district': 'district',
    'subdistrict': 'subdistrict',
    'community': 'populated-places',
}


def _normalize_admin_key(name: str) -> str:
    return ''.join(ch for ch in name.casefold() if ch.isalnum())


def _admin_name_ar_map(layer_id: str, names: set[str]) -> dict[str, str]:
    if not names:
        return {}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT name_en, name_ar
            FROM gis_admin_feature
            WHERE layer_id = %s AND name_en = ANY(%s)
            """,
            [layer_id, list(names)],
        )
        resolved = {
            name_en: name_ar
            for name_en, name_ar in cursor.fetchall()
            if name_en and name_ar
        }

    missing = names - resolved.keys()
    if not missing:
        return resolved

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT name_en, name_ar
            FROM gis_admin_feature
            WHERE layer_id = %s
            """,
            [layer_id],
        )
        normalized: dict[str, str] = {}
        for name_en, name_ar in cursor.fetchall():
            if not name_en or not name_ar:
                continue
            key = _normalize_admin_key(name_en)
            if key not in normalized:
                normalized[key] = name_ar

    for name in missing:
        arabic = normalized.get(_normalize_admin_key(name))
        if arabic:
            resolved[name] = arabic

    return resolved


def _apply_admin_ar_names(options: list[dict[str, Any]], layer_id: str) -> None:
    if not options:
        return
    ar_map = _admin_name_ar_map(layer_id, {row['slug'] for row in options if row.get('slug')})
    for row in options:
        slug = row['slug']
        row['name_ar'] = ar_map.get(slug, slug)


def _counted_options(qs, field: str, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        qs.exclude(**{f'{field}__isnull': True})
        .exclude(**{field: ''})
        .values(field)
        .annotate(count=Count('id'))
        .order_by('-count', field)[:limit]
    )
    options = [
        {
            'slug': row[field],
            'name_en': row[field],
            'name_ar': row[field],
            'count': row['count'],
        }
        for row in rows
    ]
    admin_layer_id = ADMIN_FIELD_LAYER.get(field)
    if admin_layer_id:
        _apply_admin_ar_names(options, admin_layer_id)
    return options


def _distribution_chart(options: list[dict[str, Any]], *, limit: int = 10) -> dict[str, Any]:
    top = options[:limit]
    return {
        'labels_en': [row['name_en'] for row in top],
        'labels_ar': [row['name_ar'] for row in top],
        'values': [row['count'] for row in top],
        'slugs': [row['slug'] for row in top],
    }


def _bool_distribution_chart(rows: list[tuple[int, str, dict[str, str]]], key: str) -> dict[str, Any]:
    yes = sum(1 for _sid, _gov, facts in rows if _fact_bool(facts, key) is True)
    no = sum(1 for _sid, _gov, facts in rows if _fact_bool(facts, key) is False)
    return {
        'labels_en': ['No', 'Yes'],
        'labels_ar': ['لا', 'نعم'],
        'values': [no, yes],
        'slugs': ['no', 'yes'],
        'colors': [PBI_STATUS_COLORS['no'], PBI_STATUS_COLORS['yes']],
    }


def _ordered_choice_chart(
    rows: list[tuple[int, str, dict[str, str]]],
    key: str,
    order: tuple[str, ...],
    labels: dict[str, tuple[str, str]],
) -> dict[str, Any]:
    counts = Counter(
        value for value in (_fact_str(facts, key) for _sid, _gov, facts in rows) if value
    )
    slugs = [slug for slug in order if counts.get(slug, 0) > 0]
    return {
        'labels_en': [labels[slug][0] for slug in slugs],
        'labels_ar': [labels[slug][1] for slug in slugs],
        'values': [counts.get(slug, 0) for slug in slugs],
        'slugs': list(slugs),
        'colors': [PBI_STATUS_COLORS.get(slug, PBI_COLORS[index % len(PBI_COLORS)]) for index, slug in enumerate(slugs)],
    }


def _status_charts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    non_operational = [r for r in rows if _fact_bool(r[2], 'is_operational') is False]
    rehabilitated = [r for r in rows if _fact_bool(r[2], 'previously_rehabilitated') is True]
    hammer_protected = [r for r in rows if _fact_bool(r[2], 'has_water_hammer_protection') is True]
    return {
        'station_working': _bool_distribution_chart(rows, 'is_operational'),
        'non_operational_reason': _ordered_choice_chart(
            non_operational,
            'non_operational_reason',
            NON_OPERATIONAL_REASON_ORDER,
            NON_OPERATIONAL_REASON_LABELS,
        ),
        'building_condition': _ordered_choice_chart(
            rows,
            'building_condition',
            BUILDING_CONDITION_ORDER,
            BUILDING_CONDITION_LABELS,
        ),
        'safety_procedures': _ordered_choice_chart(
            rows,
            'safety_procedures',
            SAFETY_PROCEDURE_ORDER,
            SAFETY_PROCEDURE_LABELS,
        ),
        'previously_rehabilitated': _bool_distribution_chart(rows, 'previously_rehabilitated'),
        'rehabilitation_type': _ordered_choice_chart(
            rehabilitated,
            'rehabilitation_type',
            REHABILITATION_TYPE_ORDER,
            REHABILITATION_TYPE_LABELS,
        ),
        'water_hammer_protection': _bool_distribution_chart(rows, 'has_water_hammer_protection'),
        'water_hammer_efficiency': _ordered_choice_chart(
            hammer_protected,
            'water_hammer_efficiency',
            WATER_HAMMER_EFFICIENCY_ORDER,
            WATER_HAMMER_EFFICIENCY_LABELS,
        ),
    }


def _operational_charts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    return {
        'station_working': _bool_distribution_chart(rows, 'is_operational'),
        'boosting_station': _bool_distribution_chart(rows, 'is_boosting_station'),
        'well_station': _bool_distribution_chart(rows, 'is_well_station'),
        'filtration_station': _bool_distribution_chart(rows, 'is_filtration_station'),
        'needs_solar_power': _bool_distribution_chart(rows, 'needs_solar_power'),
        'grid_power': _bool_distribution_chart(rows, 'has_public_grid_supply'),
    }


def _productivity_chart(rows: list[tuple[int, str, dict[str, str]]], key: str) -> dict[str, Any]:
    chart = _ordered_choice_chart(rows, key, PRODUCTIVITY_ORDER, PRODUCTIVITY_LABELS)
    chart['colors'] = ['#1AAB40'] * len(chart.get('slugs', []))
    return chart


def _power_supply_charts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    grid_scope = [r for r in rows if _fact_bool(r[2], 'has_public_grid_supply') is True]
    solar_scope = [r for r in rows if _fact_bool(r[2], 'solar_power_available') is True]
    return {
        'public_grid_supply': _bool_distribution_chart(rows, 'has_public_grid_supply'),
        'grid_connection_working': _bool_distribution_chart(grid_scope, 'grid_connection_working'),
        'electrical_connection_efficiency': _ordered_choice_chart(
            rows, 'electrical_connection_efficiency', EFFICIENCY_ORDER, EFFICIENCY_LABELS,
        ),
        'electrical_panel_efficiency': _ordered_choice_chart(
            rows, 'electrical_panel_efficiency', EFFICIENCY_ORDER, EFFICIENCY_LABELS,
        ),
        'transformer_efficiency': _ordered_choice_chart(
            rows, 'transformer_efficiency', EFFICIENCY_ORDER, EFFICIENCY_LABELS,
        ),
        'solar_power_available': _bool_distribution_chart(rows, 'solar_power_available'),
        'solar_system_efficiency': _ordered_choice_chart(
            solar_scope, 'solar_system_efficiency', EFFICIENCY_ORDER, EFFICIENCY_LABELS,
        ),
        'needs_solar_installation': _bool_distribution_chart(rows, 'needs_solar_installation'),
        'generator_available': _bool_distribution_chart(rows, 'generator_available'),
        'solar_space_available': _bool_distribution_chart(rows, 'solar_space_available'),
        'grid_power_productivity': _productivity_chart(grid_scope, 'grid_power_productivity'),
        'solar_power_productivity': _productivity_chart(solar_scope, 'solar_power_productivity'),
    }


LOCATION_REASON_MAP: dict[str, str] = {
    'administrative': 'administrative',
    'completely_destroyed': 'completely_destroyed',
    'ongoing_maintenance': 'ongoing_maintenance',
    'other': 'other',
    'emergency_maintenance': 'requires_new_equipment',
    'theft_vandalism': 'requires_spare_parts',
    'routine_maintenance': 'ongoing_maintenance',
}

LOCATION_REASON_ORDER = (
    'administrative',
    'completely_destroyed',
    'ongoing_maintenance',
    'other',
    'requires_new_equipment',
    'requires_spare_parts',
)

LOCATION_REASON_LABELS: dict[str, tuple[str, str]] = {
    'administrative': ('Administrative reasons', 'أسباب إدارية'),
    'completely_destroyed': ('Completely destroyed', 'مدمرة بالكامل'),
    'ongoing_maintenance': ('Ongoing maintenance', 'صيانة جارية'),
    'other': ('Other reasons', 'أسباب أخرى'),
    'requires_new_equipment': ('Requires new equipment', 'تحتاج معدات جديدة'),
    'requires_spare_parts': ('Requires spare parts', 'تحتاج قطع غيار'),
}

LOCATION_REASON_COLORS: dict[str, str] = {
    'administrative': '#252423',
    'completely_destroyed': '#E66C37',
    'ongoing_maintenance': '#118DFF',
    'other': '#8C8C8C',
    'requires_new_equipment': '#D9B300',
    'requires_spare_parts': '#D64550',
}


def _pct(part: int, total: int) -> float:
    if not total:
        return 0.0
    return round(part / total * 100, 1)


def _governorates_with_data(
    rows: list[tuple[int, str, dict[str, str]]], order: tuple[str, ...] = GOVERNORATE_ORDER,
) -> list[str]:
    present = {gov for _sid, gov, _facts in rows if gov}
    return [gov for gov in order if gov in present]


def _stacked_percent_chart(
    categories_en: list[str],
    categories_ar: list[str],
    series: list[dict[str, Any]],
    *,
    horizontal: bool = False,
) -> dict[str, Any]:
    return {
        'categories_en': categories_en,
        'categories_ar': categories_ar,
        'slugs': categories_en,
        'horizontal': horizontal,
        'percent': True,
        'series': series,
    }


def _bool_stacked_by_governorate(rows: list[tuple[int, str, dict[str, str]]], key: str) -> dict[str, Any]:
    categories_en: list[str] = []
    categories_ar: list[str] = []
    no_values: list[float] = []
    yes_values: list[float] = []
    for governorate in _governorates_with_data(rows):
        gov_rows = [r for r in rows if r[1] == governorate]
        total = len(gov_rows)
        if not total:
            continue
        categories_en.append(governorate)
        categories_ar.append(GOVERNORATE_AR.get(governorate, governorate))
        no_count = sum(1 for r in gov_rows if _fact_bool(r[2], key) is False)
        yes_count = sum(1 for r in gov_rows if _fact_bool(r[2], key) is True)
        no_values.append(_pct(no_count, total))
        yes_values.append(_pct(yes_count, total))
    return _stacked_percent_chart(
        categories_en,
        categories_ar,
        [
            {
                'slug': 'no',
                'label_en': 'No',
                'label_ar': 'لا',
                'values': no_values,
                'color': PBI_STATUS_COLORS['no'],
            },
            {
                'slug': 'yes',
                'label_en': 'Yes',
                'label_ar': 'نعم',
                'values': yes_values,
                'color': PBI_STATUS_COLORS['yes'],
            },
        ],
    )


def _grid_connection_stacked_by_governorate(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    categories_en: list[str] = []
    categories_ar: list[str] = []
    blank_values: list[float] = []
    no_values: list[float] = []
    yes_values: list[float] = []
    for governorate in _governorates_with_data(rows):
        gov_rows = [r for r in rows if r[1] == governorate]
        total = len(gov_rows)
        if not total:
            continue
        blank_count = sum(1 for r in gov_rows if _fact_bool(r[2], 'has_public_grid_supply') is False)
        no_count = sum(
            1 for r in gov_rows
            if _fact_bool(r[2], 'has_public_grid_supply') is True
            and _fact_bool(r[2], 'grid_connection_working') is False
        )
        yes_count = sum(
            1 for r in gov_rows
            if _fact_bool(r[2], 'has_public_grid_supply') is True
            and _fact_bool(r[2], 'grid_connection_working') is True
        )
        categories_en.append(governorate)
        categories_ar.append(GOVERNORATE_AR.get(governorate, governorate))
        blank_values.append(_pct(blank_count, total))
        no_values.append(_pct(no_count, total))
        yes_values.append(_pct(yes_count, total))
    return _stacked_percent_chart(
        categories_en,
        categories_ar,
        [
            {
                'slug': 'blank',
                'label_en': '(Blank)',
                'label_ar': '(فارغ)',
                'values': blank_values,
                'color': '#15C6F4',
            },
            {
                'slug': 'no',
                'label_en': 'No',
                'label_ar': 'لا',
                'values': no_values,
                'color': PBI_STATUS_COLORS['no'],
            },
            {
                'slug': 'yes',
                'label_en': 'Yes',
                'label_ar': 'نعم',
                'values': yes_values,
                'color': PBI_STATUS_COLORS['yes'],
            },
        ],
    )


def _solar_need_stacked_by_governorate(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    categories_en: list[str] = []
    categories_ar: list[str] = []
    blank_values: list[float] = []
    no_values: list[float] = []
    yes_values: list[float] = []
    for governorate in _governorates_with_data(rows):
        gov_rows = [r for r in rows if r[1] == governorate]
        total = len(gov_rows)
        if not total:
            continue
        blank_count = sum(1 for r in gov_rows if _fact_bool(r[2], 'solar_power_available') is True)
        yes_count = sum(
            1 for r in gov_rows
            if _fact_bool(r[2], 'solar_power_available') is False
            and _fact_bool(r[2], 'needs_solar_installation') is True
        )
        no_count = sum(
            1 for r in gov_rows
            if _fact_bool(r[2], 'solar_power_available') is False
            and _fact_bool(r[2], 'needs_solar_installation') is False
        )
        categories_en.append(governorate)
        categories_ar.append(GOVERNORATE_AR.get(governorate, governorate))
        blank_values.append(_pct(blank_count, total))
        no_values.append(_pct(no_count, total))
        yes_values.append(_pct(yes_count, total))
    return _stacked_percent_chart(
        categories_en,
        categories_ar,
        [
            {
                'slug': 'blank',
                'label_en': '(Blank)',
                'label_ar': '(فارغ)',
                'values': blank_values,
                'color': '#15C6F4',
            },
            {
                'slug': 'no',
                'label_en': 'No',
                'label_ar': 'لا',
                'values': no_values,
                'color': PBI_STATUS_COLORS['yes'],
            },
            {
                'slug': 'yes',
                'label_en': 'Yes',
                'label_ar': 'نعم',
                'values': yes_values,
                'color': PBI_STATUS_COLORS['partially'],
            },
        ],
    )


def _non_operational_reasons_stacked_by_governorate(
    rows: list[tuple[int, str, dict[str, str]]],
) -> dict[str, Any]:
    non_operational = [
        r for r in rows if _fact_bool(r[2], 'is_operational') is False and r[1]
    ]
    gov_counts = Counter(r[1] for r in non_operational)
    categories_en = [
        governorate
        for governorate, _ in sorted(gov_counts.items(), key=lambda row: (-row[1], row[0]))
    ]
    categories_ar = [GOVERNORATE_AR.get(governorate, governorate) for governorate in categories_en]
    series_values: dict[str, list[float]] = {
        slug: [] for slug in LOCATION_REASON_ORDER
    }
    for governorate in categories_en:
        gov_rows = [r for r in non_operational if r[1] == governorate]
        total = len(gov_rows)
        bucket_counts = Counter(
            LOCATION_REASON_MAP.get(reason, 'other')
            for reason in (_fact_str(r[2], 'non_operational_reason') for r in gov_rows)
            if reason
        )
        for slug in LOCATION_REASON_ORDER:
            series_values[slug].append(_pct(bucket_counts.get(slug, 0), total))
    series = [
        {
            'slug': slug,
            'label_en': LOCATION_REASON_LABELS[slug][0],
            'label_ar': LOCATION_REASON_LABELS[slug][1],
            'values': series_values[slug],
            'color': LOCATION_REASON_COLORS[slug],
        }
        for slug in LOCATION_REASON_ORDER
    ]
    return _stacked_percent_chart(categories_en, categories_ar, series, horizontal=True)


def _location_charts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    return {
        'station_working_by_location': _bool_stacked_by_governorate(rows, 'is_operational'),
        'public_grid_supply_by_location': _bool_stacked_by_governorate(rows, 'has_public_grid_supply'),
        'grid_connection_working_by_location': _grid_connection_stacked_by_governorate(rows),
        'non_operational_reasons_by_location': _non_operational_reasons_stacked_by_governorate(rows),
        'needs_solar_installation_by_location': _solar_need_stacked_by_governorate(rows),
    }


LAB_EQUIPMENT_ORDER = ('blank', 'yes', 'no', 'partially')
LAB_EQUIPMENT_LABELS: dict[str, tuple[str, str]] = {
    'blank': ('(Blank)', '(فارغ)'),
    'yes': ('Yes', 'نعم'),
    'no': ('No', 'لا'),
    'partially': ('Partially', 'جزئياً'),
}
LAB_EQUIPMENT_COLORS: dict[str, str] = {
    'blank': '#8C8C8C',
    'yes': PBI_STATUS_COLORS['yes'],
    'no': '#118DFF',
    'partially': PBI_STATUS_COLORS['partially'],
}


def _lab_equipment_counts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, int]:
    counts = {'blank': 0, 'yes': 0, 'no': 0, 'partially': 0}
    for _sid, _gov, facts in rows:
        value = _fact_str(facts, 'lab_equipment_status')
        counts[value if value in ('yes', 'no', 'partially') else 'blank'] += 1
    return counts


def _lab_equipment_summary_chart(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    counts = _lab_equipment_counts(rows)
    slugs = [slug for slug in LAB_EQUIPMENT_ORDER if counts[slug] > 0]
    return {
        'labels_en': [LAB_EQUIPMENT_LABELS[slug][0] for slug in slugs],
        'labels_ar': [LAB_EQUIPMENT_LABELS[slug][1] for slug in slugs],
        'values': [counts[slug] for slug in slugs],
        'slugs': list(slugs),
        'colors': [LAB_EQUIPMENT_COLORS[slug] for slug in slugs],
    }


def _lab_equipment_stacked_by_governorate(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    categories_en: list[str] = []
    categories_ar: list[str] = []
    series_values: dict[str, list[float]] = {slug: [] for slug in LAB_EQUIPMENT_ORDER}
    for governorate in _governorates_with_data(rows):
        gov_rows = [r for r in rows if r[1] == governorate]
        total = len(gov_rows)
        if not total:
            continue
        counts = _lab_equipment_counts(gov_rows)
        categories_en.append(governorate)
        categories_ar.append(GOVERNORATE_AR.get(governorate, governorate))
        for slug in LAB_EQUIPMENT_ORDER:
            series_values[slug].append(_pct(counts[slug], total))
    series = [
        {
            'slug': slug,
            'label_en': LAB_EQUIPMENT_LABELS[slug][0],
            'label_ar': LAB_EQUIPMENT_LABELS[slug][1],
            'values': series_values[slug],
            'color': LAB_EQUIPMENT_COLORS[slug],
        }
        for slug in LAB_EQUIPMENT_ORDER
    ]
    return _stacked_percent_chart(categories_en, categories_ar, series)


def _other_info_charts(rows: list[tuple[int, str, dict[str, str]]]) -> dict[str, Any]:
    return {
        'water_analyzed': {
            'summary': _bool_distribution_chart(rows, 'is_water_analyzed'),
            'by_location': _bool_stacked_by_governorate(rows, 'is_water_analyzed'),
        },
        'lab_equipment_complete': {
            'summary': _lab_equipment_summary_chart(rows),
            'by_location': _lab_equipment_stacked_by_governorate(rows),
        },
        'water_tanks_available': {
            'summary': _bool_distribution_chart(rows, 'has_water_tanks'),
            'by_location': _bool_stacked_by_governorate(rows, 'has_water_tanks'),
        },
    }


def build_drinking_water_dashboard_payload(
    governorate: str | None = None,
    district: str | None = None,
    subdistrict: str | None = None,
    org_unit: str | None = None,
    community: str | None = None,
    enrollment_year: int | None = None,
    search: str | None = None,
    station_working: tuple[bool, bool] = (False, False),
    boosting_station: tuple[bool, bool] = (False, False),
    well_station: tuple[bool, bool] = (False, False),
    filtration_station: tuple[bool, bool] = (False, False),
    needs_solar_power: tuple[bool, bool] = (False, False),
    grid_power: tuple[bool, bool] = (False, False),
    safety_procedures: set[str] | None = None,
    previously_rehabilitated: tuple[bool, bool] = (False, False),
    public_grid_supply: tuple[bool, bool] = (False, False),
    grid_connection_working: tuple[bool, bool] = (False, False),
    electrical_connection_efficiency: set[str] | None = None,
    solar_power_available: tuple[bool, bool] = (False, False),
    alternative_power_source: tuple[bool, bool] = (False, False),
    needs_solar_installation: tuple[bool, bool] = (False, False),
    solar_space_available: tuple[bool, bool] = (False, False),
) -> dict[str, Any]:
    info_by_station = drinking_station_info_facts()
    base_qs = DrinkingWaterStation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    total_count = base_qs.count()

    if not total_count:
        return {
            'status': 'empty',
            'selected_governorate': governorate,
            'selected_district': district,
            'selected_subdistrict': subdistrict,
            'selected_org_unit': org_unit,
            'selected_community': community,
            'selected_enrollment_year': enrollment_year,
            'search': search or '',
            'filters': {
                'governorates': [],
                'districts': [],
                'subdistricts': [],
                'org_units': [],
                'communities': [],
                'enrollment_years': [],
            },
            'kpis': [],
            'charts': {'operational': {}, 'status': {}, 'power_supply': {}, 'location': {}, 'other_info': {}},
            'map': {'stations': []},
            'table': {'stations': [], 'total': 0},
        }

    governorate_options = _counted_options(base_qs, 'governorate', limit=20)
    for row in governorate_options:
        row['name_ar'] = GOVERNORATE_AR.get(row['slug'], row['slug'])

    scope_qs = base_qs
    if governorate:
        scope_qs = scope_qs.filter(governorate=governorate)
    district_options = _counted_options(scope_qs, 'district', limit=40)

    district_scope = scope_qs
    if district:
        district_scope = district_scope.filter(district=district)
    subdistrict_options = _counted_options(district_scope, 'subdistrict', limit=40)

    org_scope = district_scope
    if subdistrict:
        org_scope = org_scope.filter(subdistrict=subdistrict)
    org_unit_options = _counted_options(org_scope, 'org_unit', limit=60)

    community_scope = org_scope
    if org_unit:
        community_scope = community_scope.filter(org_unit=org_unit)
    community_options = _counted_options(community_scope, 'community', limit=60)

    year_scope = community_scope
    if community:
        year_scope = year_scope.filter(community=community)
    enrollment_year_options = [
        {
            'slug': str(row['year']),
            'name_en': str(row['year']),
            'name_ar': str(row['year']),
            'count': row['count'],
        }
        for row in (
            year_scope.exclude(enrollment_date__isnull=True)
            .annotate(year=ExtractYear('enrollment_date'))
            .values('year')
            .annotate(count=Count('id'))
            .order_by('-year')
        )
        if row['year'] is not None
    ]

    filtered = year_scope
    if enrollment_year:
        filtered = filtered.filter(enrollment_date__year=enrollment_year)
    filtered = _apply_all_filters(
        filtered,
        info_by_station=info_by_station,
        search=search,
        station_working=station_working,
        boosting_station=boosting_station,
        well_station=well_station,
        filtration_station=filtration_station,
        needs_solar_power=needs_solar_power,
        grid_power=grid_power,
        safety_procedures=safety_procedures,
        previously_rehabilitated=previously_rehabilitated,
        public_grid_supply=public_grid_supply,
        grid_connection_working=grid_connection_working,
        electrical_connection_efficiency=electrical_connection_efficiency,
        solar_power_available=solar_power_available,
        alternative_power_source=alternative_power_source,
        needs_solar_installation=needs_solar_installation,
        solar_space_available=solar_space_available,
    )

    filtered_count = filtered.count()
    district_count = filtered.values('district').distinct().count()
    subdistrict_count = filtered.values('subdistrict').distinct().count()
    org_unit_count = filtered.values('org_unit').distinct().count()

    gov_counter = Counter(filtered.values_list('governorate', flat=True))
    filtered_rows = _rows_for_ids(
        list(filtered.values_list('id', flat=True)),
        dict(filtered.values_list('id', 'governorate')),
        info_by_station,
    )

    kpis = [
        _kpi(
            kpi_id='total-stations',
            label_en='Stations',
            label_ar='عدد المحطات',
            value=filtered_count,
            status='ok',
        ),
        _kpi(
            kpi_id='governorates',
            label_en='Governorates',
            label_ar='المحافظات',
            value=len(gov_counter) if not governorate else 1,
            status='neutral',
        ),
        _kpi(
            kpi_id='districts',
            label_en='Districts',
            label_ar='المناطق',
            value=district_count,
            status='neutral',
        ),
        _kpi(
            kpi_id='subdistricts',
            label_en='Sub-districts',
            label_ar='النواحي',
            value=subdistrict_count,
            status='neutral',
        ),
        _kpi(
            kpi_id='org-units',
            label_en='Org units',
            label_ar='الوحدات التنظيمية',
            value=org_unit_count,
            status='neutral',
        ),
    ]

    if governorate and district:
        chart_scope = _counted_options(filtered, 'subdistrict', limit=10)
        primary_chart = _distribution_chart(chart_scope, limit=10)
        primary_chart_id = 'subdistrict_distribution'
        primary_chart_label_en = 'By sub-district'
        primary_chart_label_ar = 'حسب الناحية'
    elif governorate:
        chart_scope = _counted_options(filtered, 'district', limit=10)
        primary_chart = _distribution_chart(chart_scope, limit=10)
        primary_chart_id = 'district_distribution'
        primary_chart_label_en = 'By district'
        primary_chart_label_ar = 'حسب المنطقة'
    else:
        primary_chart = _distribution_chart(governorate_options, limit=10)
        primary_chart_id = 'governorate_distribution'
        primary_chart_label_en = 'By governorate'
        primary_chart_label_ar = 'حسب المحافظة'

    donut_source = governorate_options if not governorate else _counted_options(filtered, 'governorate', limit=10)
    if governorate and district:
        donut_source = _counted_options(filtered, 'district', limit=8)
    elif governorate:
        donut_source = _counted_options(filtered, 'district', limit=8)

    district_ar_map = _admin_name_ar_map(
        'district',
        set(filtered.exclude(district='').values_list('district', flat=True)),
    )
    subdistrict_ar_map = _admin_name_ar_map(
        'subdistrict',
        set(filtered.exclude(subdistrict='').values_list('subdistrict', flat=True)),
    )
    community_ar_map = _admin_name_ar_map(
        'populated-places',
        set(filtered.exclude(community='').values_list('community', flat=True)),
    )

    map_stations = [
        _station_row(
            station,
            info_by_station=info_by_station,
            district_ar_map=district_ar_map,
            subdistrict_ar_map=subdistrict_ar_map,
            community_ar_map=community_ar_map,
        )
        for station in filtered.only(
            'id',
            'station_code',
            'name',
            'governorate',
            'district',
            'subdistrict',
            'community',
            'address',
            'org_unit',
            'enrollment_date',
            'incident_date',
            'latitude',
            'longitude',
        )
    ]

    return {
        'status': 'ready',
        'selected_governorate': governorate,
        'selected_district': district,
        'selected_subdistrict': subdistrict,
        'selected_org_unit': org_unit,
        'selected_community': community,
        'selected_enrollment_year': enrollment_year,
        'search': search or '',
        'data_total': total_count,
        'filters': {
            'governorates': governorate_options,
            'districts': district_options,
            'subdistricts': subdistrict_options,
            'org_units': org_unit_options,
            'communities': community_options,
            'enrollment_years': enrollment_year_options,
        },
        'kpis': kpis,
        'charts': {
            primary_chart_id: primary_chart,
            'primary_chart_id': primary_chart_id,
            'primary_chart_label_en': primary_chart_label_en,
            'primary_chart_label_ar': primary_chart_label_ar,
            'donut_distribution': _distribution_chart(donut_source, limit=8),
            'operational': _operational_charts(filtered_rows),
            'status': _status_charts(filtered_rows),
            'power_supply': _power_supply_charts(filtered_rows),
            'location': _location_charts(filtered_rows),
            'other_info': _other_info_charts(filtered_rows),
        },
        'map': {'stations': map_stations},
        'table': {'stations': map_stations[:500], 'total': filtered_count},
    }
