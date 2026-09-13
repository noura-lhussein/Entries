from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from map_layers.shapefile_utils import is_valid_lng_lat, iter_shapefile_features


def _line_label_from_path(shp_path: Path) -> str:
    stem = shp_path.stem.lstrip("'").replace('_', ' ').replace('-', ' ').strip()
    return stem or shp_path.stem


def _point_order(props: dict[str, Any], fallback: int) -> float:
    for key in ('name', 'Name', 'NAME', 'OID_', 'FID'):
        raw = props.get(key)
        if raw in (None, ''):
            continue
        try:
            return float(str(raw).strip())
        except ValueError:
            text = str(raw).strip()
            match = re.match(r'^(\d+(?:\.\d+)?)', text)
            if match:
                return float(match.group(1))
    return float(fallback)


def line_geometry_from_point_series_shapefile(shp_path: Path) -> dict[str, Any] | None:
    ordered_points: list[tuple[float, list[float]]] = []
    for index, (_fields, props, geometry) in enumerate(iter_shapefile_features(shp_path)):
        if geometry.get('type') != 'Point':
            continue
        coordinates = geometry.get('coordinates')
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        lng, lat = float(coordinates[0]), float(coordinates[1])
        if not is_valid_lng_lat(lng, lat):
            continue
        ordered_points.append((_point_order(props, index), coordinates))

    if len(ordered_points) < 2:
        return None

    ordered_points.sort(key=lambda item: item[0])
    return {
        'type': 'LineString',
        'coordinates': [coordinates for _, coordinates in ordered_points],
    }


def segment_line_properties(
    layer_id: str,
    shp_path: Path,
    *,
    voltage_kv: int | None = None,
) -> dict[str, Any]:
    label = _line_label_from_path(shp_path)
    if voltage_kv is None:
        if '230' in layer_id:
            voltage_kv = 230
        elif '400' in layer_id:
            voltage_kv = 400
        elif '66' in layer_id:
            voltage_kv = 66
        else:
            voltage_kv = 0
    return {
        'name': label,
        'name_en': label,
        'name_ar': label,
        'voltage_kv': voltage_kv,
        'status': '',
        'description': f'{voltage_kv} kV segment' if voltage_kv else 'Segment',
        'segment_source': shp_path.name,
        'source': 'electricity_gis',
    }
