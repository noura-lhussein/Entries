from __future__ import annotations

import math
from typing import Any

SYRIA_LNG = (35.5, 42.5)
SYRIA_LAT = (32.0, 37.5)


def is_valid_lng_lat(lng: float, lat: float) -> bool:
    return (
        math.isfinite(lng)
        and math.isfinite(lat)
        and -180.0 <= lng <= 180.0
        and -90.0 <= lat <= 90.0
    )


def _sanitize_position(position: Any) -> list[float] | None:
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        return None
    try:
        lng = float(position[0])
        lat = float(position[1])
    except (TypeError, ValueError):
        return None
    if not is_valid_lng_lat(lng, lat):
        return None
    return [lng, lat]


def sanitize_geometry(geometry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not geometry or not isinstance(geometry, dict):
        return None

    geom_type = geometry.get('type')
    if geom_type == 'Point':
        position = _sanitize_position(geometry.get('coordinates'))
        if position is None:
            return None
        return {'type': 'Point', 'coordinates': position}

    if geom_type == 'LineString':
        raw = geometry.get('coordinates')
        if not isinstance(raw, list):
            return None
        coordinates = [position for item in raw if (position := _sanitize_position(item)) is not None]
        if len(coordinates) < 2:
            return None
        return {'type': 'LineString', 'coordinates': coordinates}

    if geom_type == 'MultiLineString':
        raw = geometry.get('coordinates')
        if not isinstance(raw, list):
            return None
        lines: list[list[list[float]]] = []
        for line in raw:
            if not isinstance(line, list):
                continue
            coordinates = [position for item in line if (position := _sanitize_position(item)) is not None]
            if len(coordinates) >= 2:
                lines.append(coordinates)
        if not lines:
            return None
        if len(lines) == 1:
            return {'type': 'LineString', 'coordinates': lines[0]}
        return {'type': 'MultiLineString', 'coordinates': lines}

    if geom_type == 'Polygon':
        raw = geometry.get('coordinates')
        if not isinstance(raw, list):
            return None
        rings: list[list[list[float]]] = []
        for ring in raw:
            if not isinstance(ring, list):
                continue
            coordinates = [position for item in ring if (position := _sanitize_position(item)) is not None]
            if len(coordinates) >= 4:
                rings.append(coordinates)
        if not rings:
            return None
        return {'type': 'Polygon', 'coordinates': rings}

    if geom_type == 'MultiPolygon':
        raw = geometry.get('coordinates')
        if not isinstance(raw, list):
            return None
        polygons: list[list[list[list[float]]]] = []
        for polygon in raw:
            if not isinstance(polygon, list):
                continue
            rings: list[list[list[float]]] = []
            for ring in polygon:
                if not isinstance(ring, list):
                    continue
                coordinates = [position for item in ring if (position := _sanitize_position(item)) is not None]
                if len(coordinates) >= 4:
                    rings.append(coordinates)
            if rings:
                polygons.append(rings)
        if not polygons:
            return None
        return {'type': 'MultiPolygon', 'coordinates': polygons}

    return None


def sanitize_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    geometry = sanitize_geometry(feature.get('geometry'))
    if geometry is None:
        return None
    properties = feature.get('properties')
    if not isinstance(properties, dict):
        properties = {}
    return {
        'type': 'Feature',
        'geometry': geometry,
        'properties': properties,
    }


def sanitize_feature_collection(geojson: dict[str, Any]) -> dict[str, Any]:
    if geojson.get('type') != 'FeatureCollection':
        return geojson

    features: list[dict[str, Any]] = []
    for feature in geojson.get('features') or []:
        if not isinstance(feature, dict):
            continue
        cleaned = sanitize_feature(feature)
        if cleaned is not None:
            features.append(cleaned)

    return {'type': 'FeatureCollection', 'features': features}
