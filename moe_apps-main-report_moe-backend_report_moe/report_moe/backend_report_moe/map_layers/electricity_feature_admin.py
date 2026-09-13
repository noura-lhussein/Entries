"""Admin CRUD helpers for gis_electricity_feature rows (name, props, coordinates)."""

from __future__ import annotations

from typing import Any

from django.db import connection
from electricity.gis_layer_catalog import (
    ELECTRICITY_GIS_LAYER_BY_ID,
    sanitize_electricity_feature_name,
)
from rest_framework.exceptions import NotFound

from .feature_properties import parse_feature_properties

# Editable scalar fields exposed in the portal admin form (besides name / lat / lon).
LAYER_EDITABLE_PROPS: dict[str, tuple[str, ...]] = {
    'power-gis-substations-66': ('status', 'description', 'voltage_kv'),
    'power-gis-substations-230': ('status', 'description', 'voltage_kv'),
    'power-gis-substations-400': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-66': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-230': ('status', 'description', 'voltage_kv'),
    'power-gis-lines-400': ('status', 'description', 'voltage_kv'),
    'power-gis-renewable-sites': ('site_type', 'description'),
}


def _float_or_none(value: Any) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_to_dict(layer_id: str, row: tuple[Any, ...]) -> dict[str, Any]:
    feature_id, name, properties, lat, lon, geom_type = row
    props = parse_feature_properties(properties)
    display_name = sanitize_electricity_feature_name(props.get('name') or name)
    data: dict[str, Any] = {
        'id': feature_id,
        'name': display_name,
        'latitude': float(lat) if lat is not None else None,
        'longitude': float(lon) if lon is not None else None,
        'geometry_type': geom_type or '',
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        data[key] = props.get(key)
        if data[key] is None and key == 'voltage_kv':
            data[key] = _float_or_none(props.get(key))
    return data


def field_schema_for_layer(layer_id: str) -> list[dict[str, Any]]:
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
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        fields.append(
            {
                'name': key,
                'type': prop_types.get(key, 'string'),
                'required': False,
                'read_only': key == 'voltage_kv',
                'max_length': 255 if prop_types.get(key) == 'string' else None,
            }
        )
    return fields


def list_display_for_layer(layer_id: str) -> tuple[str, ...]:
    base = ('name', 'latitude', 'longitude')
    extras = LAYER_EDITABLE_PROPS.get(layer_id, ())
    preferred = [k for k in extras if k in ('status', 'voltage_kv', 'site_type', 'description')]
    return base + tuple(preferred[:2])


def list_features(
    layer_id: str,
    *,
    search: str = '',
    page: int = 1,
    page_size: int = 10,
    sort: str = '',
    direction: str = 'asc',
) -> dict[str, Any]:
    if layer_id not in ELECTRICITY_GIS_LAYER_BY_ID:
        raise NotFound('Unknown electricity GIS layer.')

    display_name_sql = """
        NULLIF(
            TRIM(
                COALESCE(
                    NULLIF(TRIM(f.properties->>'name'), ''),
                    NULLIF(TRIM(f.name), '')
                )
            ),
            ''
        )
    """

    sort_map = {
        'name': 'display_name',
        'latitude': 'lat',
        'longitude': 'lon',
        'id': 'f.id',
        'status': "f.properties->>'status'",
        'voltage_kv': "(NULLIF(TRIM(f.properties->>'voltage_kv'), ''))::float",
        'site_type': "f.properties->>'site_type'",
    }
    order_col = sort_map.get(sort, 'display_name')
    order_dir = 'DESC' if direction == 'desc' else 'ASC'

    if order_col == 'display_name':
        order_sql = f"""
            CASE WHEN {display_name_sql} IS NULL THEN 1 ELSE 0 END ASC,
            {display_name_sql} {order_dir} NULLS LAST,
            f.id ASC
        """
    else:
        order_sql = f'{order_col} {order_dir} NULLS LAST, f.id ASC'

    where = 'WHERE f.layer_id = %s'
    params: list[Any] = [layer_id]
    if search.strip():
        where += ' AND (f.name ILIKE %s OR f.properties::text ILIKE %s)'
        like = f'%{search.strip()}%'
        params.extend([like, like])

    count_sql = f'SELECT COUNT(*) FROM gis_electricity_feature f {where}'
    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
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
        FROM gis_electricity_feature f
        {where}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [*params, page_size, offset])
        rows = cursor.fetchall()

    results = [_row_to_dict(layer_id, row) for row in rows]
    return {
        'slug': layer_id,
        'count': len(results),
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': results,
    }


def get_feature(layer_id: str, pk: str) -> dict[str, Any]:
    sql = """
        SELECT
            f.id,
            f.name,
            f.properties,
            ST_Y(ST_Centroid(f.geom)) AS lat,
            ST_X(ST_Centroid(f.geom)) AS lon,
            GeometryType(f.geom) AS geom_type
        FROM gis_electricity_feature f
        WHERE f.layer_id = %s AND f.id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [layer_id, pk])
        row = cursor.fetchone()
    if not row:
        raise NotFound('Not found.')
    return _row_to_dict(layer_id, row)


# Feature writes (create/update/delete) moved to report_moe — it owns gis_electricity_feature.
# See: report_moe/backend_report_moe/master_data/gis.py
