"""
Browse accepted dynamic_forms Info for electricity TitleCategory.
Used by the portal Data page when sector=electricity (Info-only, not Dataset).
"""

from __future__ import annotations

from typing import Any

from django.db import DatabaseError
from projects.display_models import (
    ReportDynamicFormsAttribute,
    ReportDynamicFormsInfo,
    ReportDynamicFormsTitle,
)
from projects.report_forms_read import ACCEPTED

from electricity.info_scope import (
    accepted_infos_for_electricity_category,
    electricity_category_name,
    resolve_electricity_category_id,
)
from electricity.report_forms_read import (
    ENTITY_POWER_GIS_RENEWABLE,
    ENTITY_POWER_GIS_SUBSTATION_66,
    ENTITY_POWER_GIS_SUBSTATION_230,
    ENTITY_POWER_GIS_SUBSTATION_400,
    ENTITY_POWER_PLANT,
    ENTITY_SUBSTATION,
    ENTITY_TRANSMISSION_LINE,
)

ENTITY_FUEL_TANK_STATION = 'fuel_tank_station'
ENTITY_HYDRO_DAM = 'hydro_dam'
ENTITY_LOAD_GOVERNORATE = 'load_governorate'

ELECTRICITY_ENTITY_TYPES = (
    ENTITY_POWER_PLANT,
    ENTITY_SUBSTATION,
    ENTITY_TRANSMISSION_LINE,
    ENTITY_POWER_GIS_SUBSTATION_66,
    ENTITY_POWER_GIS_SUBSTATION_230,
    ENTITY_POWER_GIS_SUBSTATION_400,
    ENTITY_POWER_GIS_RENEWABLE,
    ENTITY_FUEL_TANK_STATION,
    ENTITY_HYDRO_DAM,
    ENTITY_LOAD_GOVERNORATE,
)

ENTITY_ATTR_TYPES = frozenset(ELECTRICITY_ENTITY_TYPES)


def _entity_label(entity_type: str, entity_id: int | None) -> str:
    if entity_id is None:
        return ''
    from electricity.operational_models import (
        FuelTankStation,
        HydroDam,
        LoadGovernorate,
        PowerPlant,
        Substation,
        TransmissionLine,
    )

    if entity_type == ENTITY_POWER_PLANT:
        row = PowerPlant.objects.filter(pk=entity_id).first()
        if row:
            return row.name_ar or row.name_en or row.code or str(entity_id)
    elif entity_type == ENTITY_SUBSTATION:
        row = Substation.objects.filter(pk=entity_id).first()
        if row:
            return row.name_ar or row.name_en or row.code or str(entity_id)
    elif entity_type == ENTITY_TRANSMISSION_LINE:
        row = TransmissionLine.objects.filter(pk=entity_id).first()
        if row:
            return row.name or str(entity_id)
    elif entity_type == ENTITY_FUEL_TANK_STATION:
        row = FuelTankStation.objects.filter(pk=entity_id).first()
        if row:
            return row.name_ar or row.name_en or row.code or str(entity_id)
    elif entity_type == ENTITY_HYDRO_DAM:
        row = HydroDam.objects.filter(pk=entity_id).first()
        if row:
            return row.name_ar or row.name_en or row.code or str(entity_id)
    elif entity_type == ENTITY_LOAD_GOVERNORATE:
        row = LoadGovernorate.objects.filter(pk=entity_id).first()
        if row:
            return row.name_ar or row.name_en or row.code or str(entity_id)
    else:
        from django.db import connection as default_conn

        layer_map = {
            ENTITY_POWER_GIS_SUBSTATION_66: 'power-gis-substations-66',
            ENTITY_POWER_GIS_SUBSTATION_230: 'power-gis-substations-230',
            ENTITY_POWER_GIS_SUBSTATION_400: 'power-gis-substations-400',
            ENTITY_POWER_GIS_RENEWABLE: 'power-gis-renewable-sites',
        }
        layer_id = layer_map.get(entity_type)
        if layer_id:
            with default_conn.cursor() as cursor:
                cursor.execute(
                    'SELECT name FROM gis_electricity_feature WHERE id = %s AND layer_id = %s',
                    [entity_id, layer_id],
                )
                hit = cursor.fetchone()
                if hit and hit[0]:
                    return str(hit[0])
    return str(entity_id)


def build_electricity_info_catalog() -> dict[str, Any]:
    """Latest accepted Info logical rows under electricity TitleCategory."""
    category_id = resolve_electricity_category_id()
    infos = accepted_infos_for_electricity_category(limit=12000)
    if not infos:
        return {
            'source': 'dynamic_forms',
            'category_name': electricity_category_name(),
            'category_id': category_id,
            'titles': [],
            'entries': [],
            'total': 0,
        }

    row_keys = {row.row_key for row in infos if row.row_key}
    by_id = {row.id: row for row in infos}
    entity_by_row_key: dict[str, tuple[str, int]] = {
        str(row.row_key): (row.entity_type, int(row.entity_id))
        for row in infos
        if row.row_key and row.entity_type and row.entity_id is not None
    }
    if row_keys:
        try:
            for row in ReportDynamicFormsInfo.objects.filter(
                row_key__in=row_keys, confirmed=ACCEPTED
            ):
                by_id[row.id] = row
                if row.row_key and row.entity_type and row.entity_id is not None:
                    entity_by_row_key.setdefault(
                        str(row.row_key), (row.entity_type, int(row.entity_id))
                    )
        except DatabaseError:
            pass

    all_rows = list(by_id.values())
    attr_ids = {r.attribute_id for r in all_rows}
    try:
        attrs = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(id__in=attr_ids)
        }
    except DatabaseError:
        attrs = {}

    title_ids = sorted({a.title_id for a in attrs.values() if a.title_id})
    try:
        titles = {
            t.id: t.name
            for t in ReportDynamicFormsTitle.objects.filter(id__in=title_ids)
        }
    except DatabaseError:
        titles = {}

    groups: dict[tuple[Any, ...], list[ReportDynamicFormsInfo]] = {}
    group_order: list[tuple[Any, ...]] = []
    for row in sorted(
        all_rows,
        key=lambda r: (-(r.created_at.timestamp() if r.created_at else 0), -r.id),
    ):
        if row.entity_type and row.entity_id is not None:
            entity_type, entity_id = row.entity_type, int(row.entity_id)
        elif row.row_key and str(row.row_key) in entity_by_row_key:
            entity_type, entity_id = entity_by_row_key[str(row.row_key)]
        else:
            entity_type, entity_id = '', None
        attr = attrs.get(row.attribute_id)
        title_id = getattr(attr, 'title_id', None) or 0
        key = (
            title_id,
            entity_type,
            entity_id,
            str(row.row_key) if row.row_key else f'id-{row.id}',
        )
        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(row)

    seen: set[tuple[Any, ...]] = set()
    entries: list[dict[str, Any]] = []
    title_counts: dict[int, dict[str, Any]] = {}

    for key in group_order:
        title_id, entity_type, entity_id, rk = key
        dedupe_key = (title_id, entity_type, entity_id, rk)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        rows = groups[key]
        latest_by_attr: dict[int, ReportDynamicFormsInfo] = {}
        for r in sorted(
            rows,
            key=lambda x: (-(x.created_at.timestamp() if x.created_at else 0), -x.id),
        ):
            if r.attribute_id not in latest_by_attr:
                latest_by_attr[r.attribute_id] = r

        facts = []
        updated_at = None
        for attr_id, info in sorted(latest_by_attr.items(), key=lambda x: x[0]):
            attr = attrs.get(attr_id)
            attr_type = getattr(attr, 'type', '') or ''
            if attr_type in ENTITY_ATTR_TYPES:
                continue
            facts.append(
                {
                    'attribute_label': getattr(attr, 'label', None) or str(attr_id),
                    'attribute_type': attr_type,
                    'value': info.value,
                }
            )
            if info.created_at and (updated_at is None or info.created_at.isoformat() > updated_at):
                updated_at = info.created_at.isoformat()

        entry = {
            'title_id': title_id,
            'title_name': titles.get(title_id, f'Title {title_id}' if title_id else ''),
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entity_label': _entity_label(entity_type, entity_id) if entity_id is not None else '',
            'facts': facts,
            'updated_at': updated_at,
            'row_key': rk if not str(rk).startswith('id-') else None,
        }
        entries.append(entry)

        if title_id not in title_counts:
            title_counts[title_id] = {
                'id': title_id,
                'name': entry['title_name'],
                'entity_type': entity_type,
                'entry_count': 0,
            }
        title_counts[title_id]['entry_count'] += 1

    return {
        'source': 'dynamic_forms',
        'category_name': electricity_category_name(),
        'category_id': category_id,
        'titles': sorted(title_counts.values(), key=lambda t: t['name']),
        'entries': entries,
        'total': len(entries),
    }
