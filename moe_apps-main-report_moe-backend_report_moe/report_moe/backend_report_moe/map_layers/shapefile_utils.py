from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import shapefile
from pyproj import CRS, Transformer

WGS84 = 'EPSG:4326'
SYRIA_UTM_FALLBACK = 'EPSG:32637'


def _looks_like_wgs84(bbox: tuple[float, float, float, float]) -> bool:
    xmin, ymin, xmax, ymax = bbox
    return (
        -180 <= xmin <= 180
        and -180 <= xmax <= 180
        and -90 <= ymin <= 90
        and -90 <= ymax <= 90
    )


def _resolve_transformer(shp_path: Path, bbox: tuple[float, float, float, float]) -> Transformer | None:
    prj_path = shp_path.with_suffix('.prj')
    if prj_path.exists():
        try:
            source = CRS.from_wkt(prj_path.read_text(encoding='utf-8', errors='replace'))
            if source == CRS.from_epsg(4326):
                return None
            return Transformer.from_crs(source, WGS84, always_xy=True)
        except Exception:
            pass

    if _looks_like_wgs84(bbox):
        return None

    try:
        return Transformer.from_crs(SYRIA_UTM_FALLBACK, WGS84, always_xy=True)
    except Exception:
        return None


def is_valid_lng_lat(lng: float, lat: float) -> bool:
    import math

    return (
        math.isfinite(lng)
        and math.isfinite(lat)
        and -180.0 <= lng <= 180.0
        and -90.0 <= lat <= 90.0
    )


def _transform_point(x: float, y: float, transformer: Transformer | None) -> list[float] | None:
    if transformer is None:
        lng, lat = float(x), float(y)
    else:
        lng, lat = transformer.transform(x, y)
    if not is_valid_lng_lat(lng, lat):
        return None
    return [lng, lat]


def _shape_to_geojson(shape: shapefile._Shape, transformer: Transformer | None) -> dict[str, Any] | None:
    if shape.shapeType == shapefile.NULL:
        return None

    if shape.shapeType in (shapefile.POINT, shapefile.POINTZ, shapefile.POINTM):
        position = _transform_point(shape.points[0][0], shape.points[0][1], transformer)
        if position is None:
            return None
        return {
            'type': 'Point',
            'coordinates': position,
        }

    if shape.shapeType in (shapefile.POLYLINE, shapefile.POLYLINEZ, shapefile.POLYLINEM):
        if len(shape.parts) <= 1:
            coordinates = [
                position
                for x, y in shape.points
                if (position := _transform_point(x, y, transformer)) is not None
            ]
            if len(coordinates) < 2:
                return None
            return {
                'type': 'LineString',
                'coordinates': coordinates,
            }
        lines: list[list[list[float]]] = []
        parts = list(shape.parts) + [len(shape.points)]
        for index in range(len(shape.parts)):
            segment = shape.points[parts[index] : parts[index + 1]]
            coordinates = [
                position
                for x, y in segment
                if (position := _transform_point(x, y, transformer)) is not None
            ]
            if len(coordinates) >= 2:
                lines.append(coordinates)
        if not lines:
            return None
        if len(lines) == 1:
            return {'type': 'LineString', 'coordinates': lines[0]}
        return {'type': 'MultiLineString', 'coordinates': lines}

    if shape.shapeType in (shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM):
        rings: list[list[list[float]]] = []
        parts = list(shape.parts) + [len(shape.points)]
        for index in range(len(shape.parts)):
            ring = [
                position
                for x, y in shape.points[parts[index] : parts[index + 1]]
                if (position := _transform_point(x, y, transformer)) is not None
            ]
            if len(ring) >= 4:
                rings.append(ring)
        if not rings:
            return None
        if len(rings) == 1:
            return {'type': 'Polygon', 'coordinates': rings}
        return {'type': 'MultiPolygon', 'coordinates': [[ring] for ring in rings]}

    return None


def _record_to_dict(fields: list[Any], record: tuple[Any, ...]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for field, value in zip(fields, record, strict=False):
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        props[field] = value
    return props


def _shapefile_has_dbf(shp_path: Path) -> bool:
    return shp_path.with_suffix('.dbf').is_file()


def iter_shapefile_geometries(shp_path: Path):
    """Yield geometries when DBF is missing (attributes will be empty)."""
    reader = shapefile.Reader(str(shp_path))
    transformer = _resolve_transformer(shp_path, tuple(reader.bbox))
    for index, shape in enumerate(reader.shapes()):
        geometry = _shape_to_geojson(shape, transformer)
        if geometry is None:
            continue
        yield index, geometry


def iter_shapefile_features(
    shp_path: Path,
    *,
    encoding: str | None = None,
):
    if not _shapefile_has_dbf(shp_path):
        for index, geometry in iter_shapefile_geometries(shp_path):
            yield [], {}, geometry
        return

    encodings = [encoding] if encoding else ('utf-8', 'cp1256', 'latin-1')
    last_error: Exception | None = None

    for candidate in encodings:
        try:
            reader = shapefile.Reader(str(shp_path), encoding=candidate)
            field_names = [field[0] for field in reader.fields[1:]]
            transformer = _resolve_transformer(shp_path, tuple(reader.bbox))

            for shape, record in zip(reader.shapes(), reader.records(), strict=False):
                geometry = _shape_to_geojson(shape, transformer)
                if geometry is None:
                    continue
                yield field_names, _record_to_dict(field_names, record), geometry
            return
        except UnicodeDecodeError as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error

    reader = shapefile.Reader(str(shp_path), encoding='utf-8', encodingErrors='replace')
    field_names = [field[0] for field in reader.fields[1:]]
    transformer = _resolve_transformer(shp_path, tuple(reader.bbox))
    for shape, record in zip(reader.shapes(), reader.records(), strict=False):
        geometry = _shape_to_geojson(shape, transformer)
        if geometry is None:
            continue
        yield field_names, _record_to_dict(field_names, record), geometry


def geometry_to_json(geometry: dict[str, Any]) -> str:
    return json.dumps(geometry, ensure_ascii=False)
