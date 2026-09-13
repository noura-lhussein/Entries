from __future__ import annotations

import json
from typing import Any

from django.db import connection

from .layer_catalog import ADMIN_LAYER_BY_ID, ADMIN_LAYER_SPECS


def list_admin_layers() -> list[dict[str, Any]]:
    return [
        {
            'id': layer.id,
            'name_en': layer.name_en,
            'name_ar': layer.name_ar,
            'geometry_type': layer.geometry_type,
            'admin_level': layer.admin_level,
            'default_visible': layer.default_visible,
            'sort_order': layer.sort_order,
            'filter_key': layer.filter_key,
            'group': 'administrative_units',
        }
        for layer in ADMIN_LAYER_SPECS
    ]


def _scope_filter_sql(layer_id: str, filters: dict[str, str | None]) -> tuple[str, list[Any]]:
    """Apply the most relevant admin scope for each layer (not cumulative AND)."""
    governorate = filters.get('governorate') or None
    district = filters.get('district') or None
    subdistrict = filters.get('subdistrict') or None

    if not any((governorate, district, subdistrict)):
        return '', []

    if layer_id == 'admin0':
        return '', []

    if layer_id == 'governorate':
        if governorate:
            return ' AND (f.pcode = %s OR f.adm1_pcode = %s)', [governorate, governorate]
        if district:
            return (
                ' AND f.pcode = (SELECT adm1_pcode FROM gis_admin_feature '
                'WHERE layer_id = %s AND pcode = %s LIMIT 1)',
                ['district', district],
            )
        if subdistrict:
            return (
                ' AND f.pcode = (SELECT adm1_pcode FROM gis_admin_feature '
                'WHERE layer_id = %s AND pcode = %s LIMIT 1)',
                ['subdistrict', subdistrict],
            )

    if layer_id == 'district':
        if district:
            return ' AND f.pcode = %s', [district]
        if subdistrict:
            return (
                ' AND f.pcode = (SELECT adm2_pcode FROM gis_admin_feature '
                'WHERE layer_id = %s AND pcode = %s LIMIT 1)',
                ['subdistrict', subdistrict],
            )
        if governorate:
            return ' AND f.adm1_pcode = %s', [governorate]

    if layer_id == 'subdistrict':
        if subdistrict:
            return ' AND f.pcode = %s', [subdistrict]
        if district:
            return ' AND f.adm2_pcode = %s', [district]
        if governorate:
            return ' AND f.adm1_pcode = %s', [governorate]

    if subdistrict:
        return ' AND (f.adm3_pcode = %s OR f.pcode = %s)', [subdistrict, subdistrict]
    if district:
        return ' AND (f.adm2_pcode = %s OR f.pcode = %s)', [district, district]
    if governorate:
        return ' AND (f.adm1_pcode = %s OR f.pcode = %s)', [governorate, governorate]

    return '', []


def _scope_boundary_subquery(filters: dict[str, str | None]) -> tuple[str, list[Any]] | None:
    subdistrict = filters.get('subdistrict') or None
    district = filters.get('district') or None
    governorate = filters.get('governorate') or None

    if subdistrict:
        return (
            "SELECT geom FROM gis_admin_feature WHERE layer_id = 'subdistrict' AND pcode = %s LIMIT 1",
            [subdistrict],
        )
    if district:
        return (
            "SELECT geom FROM gis_admin_feature WHERE layer_id = 'district' AND pcode = %s LIMIT 1",
            [district],
        )
    if governorate:
        return (
            "SELECT geom FROM gis_admin_feature WHERE layer_id = 'governorate' AND pcode = %s LIMIT 1",
            [governorate],
        )
    return None


def _filter_sql(filters: dict[str, str | None]) -> tuple[str, list[Any]]:
    """Hierarchy filters for filter dropdown option lists."""
    clauses: list[str] = []
    params: list[Any] = []

    if filters.get('governorate'):
        clauses.append('f.adm1_pcode = %s')
        params.append(filters['governorate'])
    if filters.get('district'):
        clauses.append('f.adm2_pcode = %s')
        params.append(filters['district'])

    if not clauses:
        return '', params
    return ' AND ' + ' AND '.join(clauses), params


def _layer_filter_sql(layer_id: str, filters: dict[str, str | None]) -> tuple[str, list[Any]]:
    if layer_id == 'admin-lines':
        boundary = _scope_boundary_subquery(filters)
        if boundary:
            subquery, params = boundary
            return f' AND ST_Intersects(f.geom, ({subquery}))', params
        return '', []

    return _scope_filter_sql(layer_id, filters)


def fetch_layer_geojson(layer_id: str, filters: dict[str, str | None] | None = None) -> dict[str, Any]:
    if layer_id not in ADMIN_LAYER_BY_ID:
        raise KeyError(layer_id)

    filter_sql, filter_params = _layer_filter_sql(layer_id, filters or {})
    sql = f"""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(
                json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(f.geom)::json,
                        'properties', f.properties
                            || jsonb_build_object(
                                'pcode', f.pcode,
                                'name_en', f.name_en,
                                'name_ar', f.name_ar,
                                'adm0_pcode', f.adm0_pcode,
                                'adm1_pcode', f.adm1_pcode,
                                'adm2_pcode', f.adm2_pcode,
                                'adm3_pcode', f.adm3_pcode
                            )
                    )
                    ORDER BY f.name_en NULLS LAST, f.pcode
                ),
                '[]'::json
            )
        )
        FROM gis_admin_feature f
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


def fetch_filter_options(
    layer_id: str,
    filters: dict[str, str | None] | None = None,
) -> list[dict[str, str | None]]:
    if layer_id not in ADMIN_LAYER_BY_ID:
        raise KeyError(layer_id)

    filter_sql, filter_params = _filter_sql(filters or {})
    sql = f"""
        SELECT DISTINCT f.pcode, f.name_en, f.name_ar
        FROM gis_admin_feature f
        WHERE f.layer_id = %s
          AND f.pcode IS NOT NULL
        {filter_sql}
        ORDER BY f.name_en NULLS LAST, f.pcode
    """
    params = [layer_id, *filter_params]
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    return [
        {'pcode': pcode, 'name_en': name_en, 'name_ar': name_ar}
        for pcode, name_en, name_ar in rows
    ]


def upsert_layer_catalog() -> None:
    with connection.cursor() as cursor:
        for layer in ADMIN_LAYER_SPECS:
            cursor.execute(
                """
                INSERT INTO gis_admin_layer (
                    id, name_en, name_ar, geometry_type, admin_level,
                    default_visible, sort_order, filter_key
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name_en = EXCLUDED.name_en,
                    name_ar = EXCLUDED.name_ar,
                    geometry_type = EXCLUDED.geometry_type,
                    admin_level = EXCLUDED.admin_level,
                    default_visible = EXCLUDED.default_visible,
                    sort_order = EXCLUDED.sort_order,
                    filter_key = EXCLUDED.filter_key
                """,
                [
                    layer.id,
                    layer.name_en,
                    layer.name_ar,
                    layer.geometry_type,
                    layer.admin_level,
                    layer.default_visible,
                    layer.sort_order,
                    layer.filter_key,
                ],
            )


def clear_layer_features(layer_id: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM gis_admin_feature WHERE layer_id = %s', [layer_id])


def insert_feature(layer_id: str, fields: dict[str, Any], geometry: dict[str, Any], properties: dict[str, Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO gis_admin_feature (
                layer_id, pcode, name_en, name_ar,
                adm0_pcode, adm1_pcode, adm2_pcode, adm3_pcode,
                properties, geom
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s::jsonb,
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
            )
            """,
            [
                layer_id,
                fields.get('pcode'),
                fields.get('name_en'),
                fields.get('name_ar'),
                fields.get('adm0_pcode'),
                fields.get('adm1_pcode'),
                fields.get('adm2_pcode'),
                fields.get('adm3_pcode'),
                json.dumps(properties, ensure_ascii=False),
                json.dumps(geometry, ensure_ascii=False),
            ],
        )
