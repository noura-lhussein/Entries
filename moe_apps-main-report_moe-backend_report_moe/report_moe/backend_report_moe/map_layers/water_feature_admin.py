"""Admin CRUD helpers for gis_water_feature rows (editable name, props, coordinates)."""

from __future__ import annotations

from typing import Any

from django.db import connection
from rest_framework.exceptions import NotFound

from .feature_properties import parse_feature_properties
from .geology_layer_catalog import GEOLOGY_LAYER_BY_ID
from .water_layer_catalog import WATER_LAYER_BY_ID, water_feature_name

# Editable scalar fields exposed in the portal admin form (besides name / lat / lon).
_GEOLOGY_EDITABLE = ('era', 'litho_type', 'lithology_en', 'age')

LAYER_EDITABLE_PROPS: dict[str, tuple[str, ...]] = {
    'water-lakes': ('governorate_name', 'notes'),
    'water-rivers': ('river_type', 'notes'),
    'water-streams': ('arc_id', 'up_cells', 'notes'),
    'water-springs': ('governorate_name', 'elevation_m', 'avg_flow_25y', 'notes'),
    'water-dams': (
        'governorate_name',
        'basin_name',
        'purpose',
        'status',
        'dam_type',
        'dam_year',
        'storage_mm',
        'dam_height_m',
        'notes',
    ),
    **{layer_id: _GEOLOGY_EDITABLE for layer_id in GEOLOGY_LAYER_BY_ID},
}


def _float_or_none(value: Any) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


_GENERIC_LAYER_NAMES = frozenset({
    'main rivers',
    'lakes',
    'stream network',
    'drainage network',
    'springs',
    'dams',
    'البحيرات',
    'الأنهار الرئيسية',
    'شبكة المسيلات المائية',
    'الينابيع',
    'السدود',
})


def _resolved_feature_name(layer_id: str, stored_name: str | None, props: dict[str, Any]) -> str:
    """Prefer real feature names over generic layer labels used as placeholders."""
    prop_name = str(props.get('name') or props.get('NAME') or '').strip()
    stored = str(stored_name or '').strip()
    if prop_name and prop_name.casefold() not in _GENERIC_LAYER_NAMES:
        return prop_name
    if stored and stored.casefold() not in _GENERIC_LAYER_NAMES:
        return stored
    return water_feature_name(layer_id, props) if prop_name or stored else ''


def _row_to_dict(layer_id: str, row: tuple[Any, ...]) -> dict[str, Any]:
    feature_id, name, properties, lat, lon, geom_type = row
    props = parse_feature_properties(properties)
    data: dict[str, Any] = {
        'id': feature_id,
        'name': _resolved_feature_name(layer_id, name, props),
        'latitude': float(lat) if lat is not None else None,
        'longitude': float(lon) if lon is not None else None,
        'geometry_type': geom_type or '',
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        data[key] = props.get(key)
        if data[key] is None and key in ('elevation_m', 'avg_flow_25y', 'storage_mm', 'dam_height_m', 'up_cells'):
            data[key] = _float_or_none(props.get(key))
    return data


def field_schema_for_layer(layer_id: str) -> list[dict[str, Any]]:
    """Synthetic field schema so AdminResourceComponent can render forms."""
    fields: list[dict[str, Any]] = [
        {'name': 'id', 'type': 'number', 'required': False, 'read_only': True},
        {'name': 'name', 'type': 'string', 'required': False, 'read_only': False, 'max_length': 255},
        {'name': 'latitude', 'type': 'number', 'required': False, 'read_only': False, 'decimal_places': 6},
        {'name': 'longitude', 'type': 'number', 'required': False, 'read_only': False, 'decimal_places': 6},
        {'name': 'geometry_type', 'type': 'string', 'required': False, 'read_only': True},
    ]
    prop_types = {
        'governorate_name': 'string',
        'basin_name': 'string',
        'river_type': 'string',
        'purpose': 'string',
        'status': 'string',
        'dam_type': 'string',
        'notes': 'textarea',
        'arc_id': 'string',
        'up_cells': 'number',
        'elevation_m': 'number',
        'avg_flow_25y': 'number',
        'dam_year': 'number',
        'storage_mm': 'number',
        'dam_height_m': 'number',
        'era': 'string',
        'litho_type': 'string',
        'lithology_en': 'string',
        'age': 'string',
    }
    for key in LAYER_EDITABLE_PROPS.get(layer_id, ()):
        fields.append(
            {
                'name': key,
                'type': prop_types.get(key, 'string'),
                'required': False,
                'read_only': False,
                'max_length': 255 if prop_types.get(key) == 'string' else None,
            }
        )
    return fields


def list_display_for_layer(layer_id: str) -> tuple[str, ...]:
    base = ('name', 'latitude', 'longitude')
    extras = LAYER_EDITABLE_PROPS.get(layer_id, ())
    # Prefer a short list for the table.
    preferred = [
        k
        for k in extras
        if k in ('governorate_name', 'river_type', 'elevation_m', 'purpose', 'status', 'era', 'litho_type')
    ]
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
    if layer_id not in WATER_LAYER_BY_ID and layer_id not in GEOLOGY_LAYER_BY_ID and layer_id not in LAYER_EDITABLE_PROPS:
        raise NotFound('Unknown water layer.')

    # Display name used for sorting: properties.name, else column name (skip generic labels).
    display_name_sql = """
        NULLIF(
            TRIM(
                CASE
                    WHEN COALESCE(NULLIF(TRIM(f.properties->>'name'), ''), '') <> ''
                        AND LOWER(TRIM(f.properties->>'name')) NOT IN (
                            'main rivers', 'lakes', 'stream network', 'springs', 'dams'
                        )
                    THEN TRIM(f.properties->>'name')
                    WHEN COALESCE(NULLIF(TRIM(f.name), ''), '') <> ''
                        AND LOWER(TRIM(f.name)) NOT IN (
                            'main rivers', 'lakes', 'stream network', 'springs', 'dams'
                        )
                    THEN TRIM(f.name)
                    ELSE ''
                END
            ),
            ''
        )
    """

    sort_map = {
        'name': 'display_name',
        'latitude': 'lat',
        'longitude': 'lon',
        'id': 'f.id',
        'river_type': "COALESCE(f.properties->>'river_type', f.properties->>'type')",
    }
    order_col = sort_map.get(sort, 'display_name')
    order_dir = 'DESC' if direction == 'desc' else 'ASC'

    # Named features first; for rivers prefer "رئيسي" before "ثانوي".
    if layer_id == 'water-rivers' and not sort:
        order_sql = f"""
            CASE WHEN {display_name_sql} IS NULL THEN 1 ELSE 0 END ASC,
            CASE
                WHEN COALESCE(f.properties->>'river_type', f.properties->>'type') = 'نهر رئيسي' THEN 0
                ELSE 1
            END ASC,
            {display_name_sql} ASC NULLS LAST,
            f.id ASC
        """
    elif order_col == 'display_name':
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

    count_sql = f'SELECT COUNT(*) FROM gis_water_feature f {where}'
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
        FROM gis_water_feature f
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
        FROM gis_water_feature f
        WHERE f.layer_id = %s AND f.id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [layer_id, pk])
        row = cursor.fetchone()
    if not row:
        raise NotFound('Not found.')
    return _row_to_dict(layer_id, row)


# create_feature/update_feature/delete_feature removed: gis_water_feature is
# written through raw SQL rather than the ORM, because the table carries a geometry
# entirely (it can only guard ORM models, and this table has none). GIS feature
# writes moved to report_moe; callers must reject spec.gis_layer_id writes
# explicitly (see water/api.py and geology/api.py admin_create/update/delete).
