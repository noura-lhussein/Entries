from __future__ import annotations

import json
from typing import Any

from django.db import connection

from .feature_properties import parse_feature_properties
from .map_layer_catalog import MAP_LAYER_BY_ID, MAP_LAYER_SPECS, layer_geometry_type, layer_to_dict
from .services import _scope_boundary_subquery


def _float_or_none(value: Any) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def list_water_layers() -> list[dict[str, Any]]:
    return [layer_to_dict(layer) for layer in MAP_LAYER_SPECS]


def _filter_sql(filters: dict[str, str | None]) -> tuple[str, list[Any]]:
    boundary = _scope_boundary_subquery(filters)
    if not boundary:
        return '', []
    subquery, params = boundary
    return f' AND ST_Intersects(f.geom, ({subquery}))', params


def fetch_water_layer_geojson(
    layer_id: str,
    filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if layer_id not in MAP_LAYER_BY_ID:
        raise KeyError(layer_id)

    filter_sql, filter_params = _filter_sql(filters or {})
    sql = f"""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(
                json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(f.geom)::json,
                        'properties', f.properties
                            || jsonb_build_object('name', f.name)
                            || jsonb_build_object('feature_id', f.id)
                    )
                    ORDER BY f.name NULLS LAST, f.id
                ),
                '[]'::json
            )
        )
        FROM gis_water_feature f
        WHERE f.layer_id = %s
        {filter_sql}
    """
    params = [layer_id, *filter_params]
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    if not row or not row[0]:
        return {'type': 'FeatureCollection', 'features': []}
    return row[0]


def fetch_springs_map_catalog() -> dict[str, Any]:
    """Spring points from gis_water_feature (layer water-springs)."""
    sql = """
        SELECT f.id, f.name, f.properties, ST_Y(f.geom) AS lat, ST_X(f.geom) AS lon
        FROM gis_water_feature f
        WHERE f.layer_id = 'water-springs'
        ORDER BY f.name NULLS LAST, f.id
    """
    springs: list[dict[str, Any]] = []
    with connection.cursor() as cursor:
        cursor.execute(sql)
        for feature_id, name, properties, lat, lon in cursor.fetchall():
            props = parse_feature_properties(properties)
            springs.append({
                'feature_id': feature_id,
                'name': name or '',
                'governorate': str(props.get('governorate_name') or props.get('mohafaza') or '').strip(),
                'elevation_m': _float_or_none(props.get('elevation_m')),
                'avg_flow_25y': _float_or_none(props.get('avg_flow_25y', props.get('AVG25y'))),
                'latitude': float(lat) if lat is not None else None,
                'longitude': float(lon) if lon is not None else None,
            })
    return {'springs': springs}


def upsert_water_layer_catalog() -> None:
    with connection.cursor() as cursor:
        for layer in MAP_LAYER_SPECS:
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
                    layer_geometry_type(layer),
                    layer.default_visible,
                    layer.sort_order,
                ],
            )


def clear_water_layer_features(layer_id: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM gis_water_feature WHERE layer_id = %s', [layer_id])


def insert_water_feature(
    layer_id: str,
    name: str,
    properties: dict[str, Any],
    geometry: dict[str, Any],
) -> None:
    with connection.cursor() as cursor:
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
