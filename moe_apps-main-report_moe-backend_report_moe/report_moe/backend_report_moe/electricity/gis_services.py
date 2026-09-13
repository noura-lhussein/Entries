from __future__ import annotations

import json
from typing import Any

from django.db import connection
from map_layers.geojson_sanitize import sanitize_feature_collection, sanitize_geometry
from map_layers.services import _scope_boundary_subquery

from .gis_layer_catalog import ELECTRICITY_GIS_LAYER_BY_ID, ELECTRICITY_GIS_LAYER_SPECS


def _filter_sql(filters: dict[str, str | None]) -> tuple[str, list[Any]]:
    boundary = _scope_boundary_subquery(filters)
    if not boundary:
        return '', []
    subquery, params = boundary
    return f' AND ST_Intersects(f.geom, ({subquery}))', params


def fetch_electricity_gis_layer_geojson(
    layer_id: str,
    filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if layer_id not in ELECTRICITY_GIS_LAYER_BY_ID:
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
        FROM gis_electricity_feature f
        WHERE f.layer_id = %s
        {filter_sql}
    """
    params = [layer_id, *filter_params]
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    if not row or not row[0]:
        return {'type': 'FeatureCollection', 'features': []}
    return sanitize_feature_collection(row[0])


def upsert_electricity_gis_layer_catalog() -> None:
    with connection.cursor() as cursor:
        for layer in ELECTRICITY_GIS_LAYER_SPECS:
            cursor.execute(
                """
                INSERT INTO gis_electricity_layer (
                    id, name_en, name_ar, geometry_type, voltage_kv, default_visible, sort_order
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name_en = EXCLUDED.name_en,
                    name_ar = EXCLUDED.name_ar,
                    geometry_type = EXCLUDED.geometry_type,
                    voltage_kv = EXCLUDED.voltage_kv,
                    default_visible = EXCLUDED.default_visible,
                    sort_order = EXCLUDED.sort_order
                """,
                [
                    layer.id,
                    layer.name_en,
                    layer.name_ar,
                    layer.geometry_type,
                    layer.voltage_kv,
                    layer.default_visible,
                    layer.sort_order,
                ],
            )


def clear_electricity_gis_layer_features(layer_id: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM gis_electricity_feature WHERE layer_id = %s', [layer_id])


def insert_electricity_gis_feature(
    layer_id: str,
    name: str,
    properties: dict[str, Any],
    geometry: dict[str, Any],
) -> None:
    cleaned = sanitize_geometry(geometry)
    if cleaned is None:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO gis_electricity_feature (layer_id, name, properties, geom)
            VALUES (%s, %s, %s::jsonb, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
            """,
            [
                layer_id,
                name or None,
                json.dumps(properties, ensure_ascii=False, default=str),
                json.dumps(cleaned, ensure_ascii=False),
            ],
        )
