from __future__ import annotations

import math
from typing import Any


def _cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique
    if len(unique) == 2:
        return unique

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def expand_polygon(points: list[tuple[float, float]], factor: float = 1.12) -> list[tuple[float, float]]:
    if len(points) < 3:
        return points
    lon_avg = sum(p[0] for p in points) / len(points)
    lat_avg = sum(p[1] for p in points) / len(points)
    expanded: list[tuple[float, float]] = []
    for lon, lat in points:
        expanded.append(
            (
                lon_avg + (lon - lon_avg) * factor,
                lat_avg + (lat - lat_avg) * factor,
            ),
        )
    return expanded


def polygon_area_km2(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    lat_ref = sum(p[1] for p in points) / len(points)
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat_ref))
    xs = [p[0] * km_per_deg_lon for p in points]
    ys = [p[1] * km_per_deg_lat for p in points]
    area = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(area) / 2.0


def ring_to_geojson_polygon(ring: list[tuple[float, float]]) -> dict[str, Any]:
    if len(ring) < 3:
        return {'type': 'Polygon', 'coordinates': []}
    coords = [[lon, lat] for lon, lat in ring]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return {'type': 'Polygon', 'coordinates': [coords]}


def circle_polygon(lon: float, lat: float, radius_km: float = 25, steps: int = 24) -> dict[str, Any]:
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat))
    ring: list[tuple[float, float]] = []
    for i in range(steps):
        angle = 2 * math.pi * i / steps
        ring.append(
            (
                lon + (radius_km * math.cos(angle)) / km_per_deg_lon,
                lat + (radius_km * math.sin(angle)) / km_per_deg_lat,
            ),
        )
    return ring_to_geojson_polygon(ring)
