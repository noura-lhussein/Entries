from __future__ import annotations

import json
from typing import Any

from django.db import connection

from .services import _scope_boundary_subquery

_BATCH_SIZE = 250


def _governorate_label_names(pcode: str) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT name_en, name_ar
            FROM gis_admin_feature
            WHERE layer_id = 'governorate' AND pcode = %s
            LIMIT 1
            """,
            [pcode],
        )
        row = cursor.fetchone()
    if not row:
        return set()
    return {
        str(name).strip().lower()
        for name in row
        if name and str(name).strip()
    }


def _feature_matches_governorate_label(feature: dict[str, Any], names: set[str]) -> bool:
    if not names:
        return False
    props = feature.get('properties') or {}
    value = str(props.get('governorate') or props.get('governorate_name') or '').strip().lower()
    if not value:
        return False
    return any(name in value or value in name for name in names)


def _boundary_geometry_geojson(subquery: str, boundary_params: list[Any]) -> str | None:
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT ST_AsGeoJSON(({subquery}))::text', boundary_params)
        row = cursor.fetchone()
    if not row or not row[0]:
        return None
    return str(row[0])


def _intersecting_feature_indices(
    features: list[dict[str, Any]],
    subquery: str,
    boundary_params: list[Any],
) -> set[int]:
    indexed: list[tuple[int, str]] = []
    for index, feature in enumerate(features):
        geometry = feature.get('geometry')
        if geometry:
            indexed.append((index, json.dumps(geometry)))

    if not indexed:
        return set()

    boundary_geojson = _boundary_geometry_geojson(subquery, boundary_params)
    if not boundary_geojson:
        return set()

    kept: set[int] = set()
    sql = """
        WITH boundary AS (
            SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) AS geom
        ),
        batch AS (
            SELECT * FROM unnest(%s::int[], %s::text[]) AS t(feature_idx, geom_json)
        )
        SELECT b.feature_idx
        FROM batch b, boundary
        WHERE ST_Intersects(
            ST_SetSRID(ST_GeomFromGeoJSON(b.geom_json), 4326),
            boundary.geom
        )
    """

    with connection.cursor() as cursor:
        for start in range(0, len(indexed), _BATCH_SIZE):
            chunk = indexed[start:start + _BATCH_SIZE]
            indices = [item[0] for item in chunk]
            geometries = [item[1] for item in chunk]
            cursor.execute(sql, [boundary_geojson, indices, geometries])
            kept.update(int(row[0]) for row in cursor.fetchall())

    return kept


def filter_geojson_by_admin_filters(
    geojson: dict[str, Any],
    filters: dict[str, str | None] | None,
) -> dict[str, Any]:
    """Keep only features whose geometry intersects the active admin filter scope."""
    if geojson.get('type') != 'FeatureCollection':
        return geojson

    active_filters = filters or {}
    if not any(active_filters.get(key) for key in ('governorate', 'district', 'subdistrict')):
        return geojson

    features = geojson.get('features') or []
    if not features:
        return geojson

    boundary = _scope_boundary_subquery(active_filters)
    if not boundary:
        return geojson

    subquery, boundary_params = boundary
    governorate_names: set[str] = set()
    if active_filters.get('governorate') and not active_filters.get('district'):
        governorate_names = _governorate_label_names(str(active_filters['governorate']))

    kept_indices = _intersecting_feature_indices(features, subquery, boundary_params)
    kept: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        if index in kept_indices:
            kept.append(feature)
            continue
        if governorate_names and _feature_matches_governorate_label(feature, governorate_names):
            kept.append(feature)

    return {**geojson, 'features': kept}
