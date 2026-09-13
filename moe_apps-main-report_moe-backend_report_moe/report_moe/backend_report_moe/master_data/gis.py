"""
GIS feature CRUD for gis_electricity_feature / gis_water_feature.

Ported from moeds gis/electricity_feature_admin.py and gis/water_feature_admin.py,
on the default connection; `search_path` covers both schemas.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from django.db import connections

from .exceptions import MasterDataError

logger = logging.getLogger(__name__)

GisTable = Literal['gis_electricity_feature', 'gis_water_feature']

ELECTRICITY_LAYER_PROPS: dict[str, tuple[str, ...]] = {
    'power-gis-substations-66': ('status', 'description', 'voltage_kv'),
    'power-gis-substations-230': ('status', 'description', 'voltage_kv'),
    'power-gis-substations-400': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-66': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-230': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-400': ('status', 'description', 'voltage_kv'),
    'power-gis-renewable-sites': ('site_type', 'description'),
}

WATER_LAYER_PROPS: dict[str, tuple[str, ...]] = {
    'water-lakes': ('governorate_name', 'notes'),
    'water-rivers': ('river_type', 'notes'),
    'water-streams': ('arc_id', 'up_cells', 'notes'),
    'water-springs': ('governorate_name', 'elevation_m', 'avg_flow_25y', 'notes'),
    'geology-official': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-era': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-cenozoic': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-quaternary': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-mesozoic': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-sedimentary': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-volcanic': ('era', 'litho_type', 'lithology_en', 'age'),
    'geology-minerals': ('mineral_type_ar', 'source_x_dms', 'source_y_dms'),
    'geology-geomillion': ('symbol', 'legend', 'sym_color', 'info_path'),
    'geology-faults': ('class_name', 'sheet'),
    'geology-extinct-volcanoes': ('class_name', 'sheet'),
}

LAYER_TABLE: dict[str, GisTable] = {
    **{lid: 'gis_electricity_feature' for lid in ELECTRICITY_LAYER_PROPS},
    **{lid: 'gis_water_feature' for lid in WATER_LAYER_PROPS},
}

LAYER_EDITABLE_PROPS: dict[str, tuple[str, ...]] = {
    **ELECTRICITY_LAYER_PROPS,
    **WATER_LAYER_PROPS,
}

_READ_ONLY_PROPS = frozenset({'voltage_kv'})
_NUMERIC_PROPS = frozenset({
    'elevation_m', 'avg_flow_25y', 'storage_mm', 'dam_height_m', 'up_cells', 'dam_year', 'voltage_kv',
})


def _cursor():
    return connections['default'].cursor()


def parse_feature_properties(raw: Any) -> dict[str, Any]:
    current: Any = raw
    for _ in range(3):
        if current is None:
            return {}
        if isinstance(current, dict):
            return current
        if isinstance(current, bytes):
            current = current.decode('utf-8')
            continue
        if isinstance(current, str):
            stripped = current.strip()
            if not stripped:
                return {}
            try:
                current = json.loads(stripped)
            except json.JSONDecodeError:
                return {}
            continue
        return {}
    return current if isinstance(current, dict) else {}


def _float_or_none(value: Any) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _assert_known_layer(layer_id: str) -> GisTable:
    table = LAYER_TABLE.get(layer_id)
    if not table:
        raise MasterDataError('Unknown GIS layer.', status=404)
    return table


def field_schema_for_layer(layer_id: str) -> list[dict[str, Any]]:
    _assert_known_layer(layer_id)
    fields: list[dict[str, Any]] = [
        {'name': 'id', 'type': 'number', 'required': False, 'read_only': True},
        {'name': 'name', 'type': 'string', 'required': False, 'read_only': False, 'max_length': 255},
        {'name': 'latitude', 'type': 'number', 'required': False, 'read_only': False, 'decimal_places': 6},
        {'name': 'longitude', 'type': 'number', 'required': False, 'read_only': False, 'decimal_places': 6},
        {'name': 'geometry_type', 'type': 'string', 'required': False, 'read_only': True},
    ]
    prop_types = {
        'status': 'string',
        'description': 'textarea',
        'voltage_kv': 'number',
        'site_type': 'string',
        'governorate_name': 'string',
        'river_type': 'string',
        'notes': 'textarea',
        'arc_id': 'string',
        'up_cells': 'number',
        'elevation_m': 'number',
        'avg_flow_25y': 'number',
        'era': 'string',
        'litho_type': 'string',
        'lithology_en': 'string',
        'age': 'string',
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        ptype = prop_types.get(key, 'string')
        fields.append(
            {
                'name': key,
                'type': ptype,
                'required': False,
                'read_only': key in _READ_ONLY_PROPS,
                'max_length': 255 if ptype == 'string' else None,
                **({'decimal_places': 6} if ptype == 'number' else {}),
            }
        )
    return fields


def list_display_for_layer(layer_id: str) -> tuple[str, ...]:
    base = ('name', 'latitude', 'longitude')
    extras = LAYER_EDITABLE_PROPS.get(layer_id, ())
    preferred = [
        k
        for k in extras
        if k in ('status', 'voltage_kv', 'site_type', 'governorate_name', 'river_type', 'elevation_m', 'era', 'litho_type')
    ]
    return base + tuple(preferred[:2])


def _row_to_dict(layer_id: str, row: tuple[Any, ...]) -> dict[str, Any]:
    feature_id, name, properties, lat, lon, geom_type = row
    props = parse_feature_properties(properties)
    display_name = str(props.get('name') or name or '').strip()
    data: dict[str, Any] = {
        'id': feature_id,
        'name': display_name,
        'latitude': float(lat) if lat is not None else None,
        'longitude': float(lon) if lon is not None else None,
        'geometry_type': geom_type or '',
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        data[key] = props.get(key)
        if data[key] is None and key in _NUMERIC_PROPS:
            data[key] = _float_or_none(props.get(key))
    return data


# `gis_water_feature.name` and `gis_electricity_feature.name` are both varchar(255).
# The ORM resources get this check from full_clean(); the raw-SQL GIS path has no model,
# so enforce it here — otherwise Postgres raises StringDataRightTruncation and the client
# gets a leaked driver message instead of a field error.
_NAME_MAX_LENGTH = 255


def _clean_feature_name(value: Any) -> str | None:
    name = str(value or '').strip()
    if not name:
        return None
    if len(name) > _NAME_MAX_LENGTH:
        raise MasterDataError(
            f'name: تجاوز الحد الأقصى {_NAME_MAX_LENGTH} حرفاً (المُرسل {len(name)}).',
            status=400,
        )
    return name


def _props_from_payload(
    layer_id: str,
    payload: dict[str, Any],
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    props = dict(existing or {})
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        if key in _READ_ONLY_PROPS:
            continue
        if key in payload:
            value = payload[key]
            if key in _NUMERIC_PROPS:
                props[key] = _float_or_none(value)
            else:
                props[key] = '' if value is None else str(value).strip()
    name = payload.get('name')
    if name is not None:
        props['name'] = str(name).strip()
    return props


def list_features(
    layer_id: str,
    *,
    search: str = '',
    page: int = 1,
    page_size: int = 10,
    sort: str = '',
    direction: str = 'asc',
) -> dict[str, Any]:
    table = _assert_known_layer(layer_id)
    order_dir = 'DESC' if direction == 'desc' else 'ASC'
    sort_map = {
        'name': 'f.name',
        'latitude': 'lat',
        'longitude': 'lon',
        'id': 'f.id',
        'status': "f.properties->>'status'",
        'site_type': "f.properties->>'site_type'",
        'river_type': "COALESCE(f.properties->>'river_type', f.properties->>'type')",
    }
    order_col = sort_map.get(sort, 'f.name')

    where = 'WHERE f.layer_id = %s'
    params: list[Any] = [layer_id]
    if search.strip():
        where += ' AND (f.name ILIKE %s OR f.properties::text ILIKE %s)'
        like = f'%{search.strip()}%'
        params.extend([like, like])

    with _cursor() as cursor:
        cursor.execute(f'SELECT COUNT(*) FROM {table} f {where}', params)
        total_count = int(cursor.fetchone()[0])

    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = min(max(1, page), total_pages)
    offset = (page - 1) * page_size

    sql = f"""
        SELECT
            f.id,
            f.name,
            f.properties,
            ST_Y(ST_Centroid(f.geom)) AS lat,
            ST_X(ST_Centroid(f.geom)) AS lon,
            GeometryType(f.geom) AS geom_type
        FROM {table} f
        {where}
        ORDER BY {order_col} {order_dir} NULLS LAST, f.id ASC
        LIMIT %s OFFSET %s
    """
    with _cursor() as cursor:
        cursor.execute(sql, [*params, page_size, offset])
        rows = cursor.fetchall()

    return {
        'slug': layer_id,
        'count': len(rows),
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': [_row_to_dict(layer_id, row) for row in rows],
    }


def get_feature(layer_id: str, pk: str) -> dict[str, Any]:
    table = _assert_known_layer(layer_id)
    sql = f"""
        SELECT
            f.id,
            f.name,
            f.properties,
            ST_Y(ST_Centroid(f.geom)) AS lat,
            ST_X(ST_Centroid(f.geom)) AS lon,
            GeometryType(f.geom) AS geom_type
        FROM {table} f
        WHERE f.layer_id = %s AND f.id = %s
    """
    with _cursor() as cursor:
        cursor.execute(sql, [layer_id, pk])
        row = cursor.fetchone()
    if not row:
        raise MasterDataError('Not found.', status=404)
    return _row_to_dict(layer_id, row)


def create_feature(layer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    table = _assert_known_layer(layer_id)
    lat = _float_or_none(payload.get('latitude'))
    lon = _float_or_none(payload.get('longitude'))
    if lat is None or lon is None:
        raise MasterDataError('latitude and longitude are required to create a feature.', status=400)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise MasterDataError('Invalid latitude/longitude.', status=400)

    props = _props_from_payload(layer_id, payload)
    name = _clean_feature_name(props.get('name') or payload.get('name'))

    sql = f"""
        INSERT INTO {table} (layer_id, name, properties, geom)
        VALUES (
            %s, %s, %s::jsonb,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        )
        RETURNING id
    """
    with _cursor() as cursor:
        cursor.execute(
            sql,
            [layer_id, name, json.dumps(props, ensure_ascii=False, default=str), lon, lat],
        )
        new_id = cursor.fetchone()[0]
    return get_feature(layer_id, str(new_id))


def update_feature(layer_id: str, pk: str, payload: dict[str, Any]) -> dict[str, Any]:
    table = _assert_known_layer(layer_id)
    current = get_feature(layer_id, pk)
    with _cursor() as cursor:
        # FOR UPDATE locks the row for the caller's transaction. Without it, two
        # concurrent PATCHes both read the old `properties` and the second silently
        # discards the first's changes (READ COMMITTED lets both reads succeed).
        # Callers must therefore run this inside transaction.atomic().
        cursor.execute(
            f'SELECT properties FROM {table} WHERE layer_id = %s AND id = %s FOR UPDATE',
            [layer_id, pk],
        )
        row = cursor.fetchone()
    existing_props = parse_feature_properties(row[0]) if row else {}
    props = _props_from_payload(layer_id, payload, existing_props)
    name = _clean_feature_name(props.get('name') or payload.get('name') or current.get('name'))

    lat = _float_or_none(payload.get('latitude')) if 'latitude' in payload else current.get('latitude')
    lon = _float_or_none(payload.get('longitude')) if 'longitude' in payload else current.get('longitude')

    sets = ['name = %s', 'properties = %s::jsonb']
    params: list[Any] = [name, json.dumps(props, ensure_ascii=False, default=str)]

    if lat is not None and lon is not None:
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise MasterDataError('Invalid latitude/longitude.', status=400)
        sets.append(
            """
            geom = CASE
                WHEN GeometryType(geom) IN ('POINT', 'MULTIPOINT')
                    THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                ELSE ST_Translate(
                    geom,
                    %s - ST_X(ST_Centroid(geom)),
                    %s - ST_Y(ST_Centroid(geom))
                )
            END
            """
        )
        params.extend([lon, lat, lon, lat])

    sql = f"""
        UPDATE {table}
        SET {', '.join(sets)}
        WHERE layer_id = %s AND id = %s
    """
    params.extend([layer_id, pk])
    with _cursor() as cursor:
        cursor.execute(sql, params)
        if cursor.rowcount == 0:
            raise MasterDataError('Not found.', status=404)
    return get_feature(layer_id, pk)


def delete_feature(layer_id: str, pk: str) -> None:
    table = _assert_known_layer(layer_id)
    with _cursor() as cursor:
        cursor.execute(
            f'DELETE FROM {table} WHERE layer_id = %s AND id = %s',
            [layer_id, pk],
        )
        if cursor.rowcount == 0:
            raise MasterDataError('Not found.', status=404)
    logger.info('master_data.gis.delete layer=%s pk=%s', layer_id, pk)


def upsert_water_layer_catalog(layers) -> None:
    """Upsert rows in gis_water_layer for the given RawMaterialLayerSpec iterable."""
    with _cursor() as cursor:
        for layer in layers:
            cursor.execute(
                """
                INSERT INTO gis_water_layer (
                    id, name_en, name_ar, geometry_type, default_visible, sort_order
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name_en = EXCLUDED.name_en,
                    name_ar = EXCLUDED.name_ar,
                    geometry_type = EXCLUDED.geometry_type,
                    default_visible = EXCLUDED.default_visible,
                    sort_order = EXCLUDED.sort_order
                """,
                [
                    layer.id,
                    layer.name_en,
                    layer.name_ar,
                    layer.geometry_type,
                    layer.default_visible,
                    layer.sort_order,
                ],
            )


def clear_water_layer_features(layer_id: str) -> None:
    with _cursor() as cursor:
        cursor.execute('DELETE FROM gis_water_feature WHERE layer_id = %s', [layer_id])


def bulk_insert_water_feature(
    layer_id: str,
    name: str,
    properties: dict[str, Any],
    geometry: dict[str, Any],
) -> None:
    with _cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO gis_water_feature (layer_id, name, properties, geom)
            VALUES (%s, %s, %s::jsonb, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            """,
            [
                layer_id,
                name or None,
                json.dumps(properties, ensure_ascii=False, default=str),
                json.dumps(geometry, ensure_ascii=False),
            ],
        )
