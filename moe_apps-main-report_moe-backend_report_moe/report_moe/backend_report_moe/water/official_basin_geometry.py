from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

GEOJSON_PATH = Path(__file__).resolve().parent / 'data' / 'syria_hydro_basins.geojson'


def _polygon_area_km2(geometry: dict) -> float:
    """Approximate geometry area in km² for Polygon or MultiPolygon."""
    import math

    def ring_area(ring: list[list[float]]) -> float:
        if len(ring) < 3:
            return 0.0
        avg_lat = sum(pt[1] for pt in ring) / len(ring)
        lat_scale = 111.32
        lon_scale = 111.32 * math.cos(math.radians(avg_lat))
        area = 0.0
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][0] * lon_scale, ring[i][1] * lat_scale
            x2, y2 = ring[i + 1][0] * lon_scale, ring[i + 1][1] * lat_scale
            area += x1 * y2 - x2 * y1
        return abs(area) / 2.0

    def polygon_area(coords: list) -> float:
        if not coords:
            return 0.0
        outer = ring_area(coords[0])
        holes = sum(ring_area(hole) for hole in coords[1:])
        return max(outer - holes, 0.0)

    geom_type = geometry.get('type')
    coordinates = geometry.get('coordinates') or []
    if geom_type == 'Polygon':
        return polygon_area(coordinates)
    if geom_type == 'MultiPolygon':
        return sum(polygon_area(poly) for poly in coordinates)
    return 0.0


@lru_cache(maxsize=1)
def load_official_basin_features() -> dict[str, dict[str, Any]]:
    if not GEOJSON_PATH.is_file():
        return {}

    with GEOJSON_PATH.open(encoding='utf-8') as handle:
        payload = json.load(handle)

    indexed: dict[str, dict[str, Any]] = {}
    for feature in payload.get('features') or []:
        props = feature.get('properties') or {}
        slug = (props.get('slug') or '').strip()
        geometry = feature.get('geometry')
        if not slug or not geometry:
            continue
        area_km2 = _polygon_area_km2(geometry)
        indexed[slug] = {
            'geometry': geometry,
            'area_km2': area_km2,
            'geometry_source': props.get('geometry_source') or 'official_gis',
        }
    return indexed
