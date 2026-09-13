from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from map_layers.shapefile_utils import iter_shapefile_features

from .basin_catalog import BASIN_SPEC_BY_SHAPEFILE_NAME, BASIN_SPECS, BASINS_GEOJSON_PATH
from .models import RainfallBasin
from .official_basin_geometry import load_official_basin_features


def _area_km2(props: dict[str, Any]) -> Decimal | None:
    raw = props.get('مساحة')
    if raw in (None, ''):
        return None
    try:
        return Decimal(str(raw)).quantize(Decimal('0.01'))
    except Exception:
        return None


def sync_rainfall_basins_from_shapefile(shp_path: Path) -> dict[str, Any]:
    if not shp_path.is_file():
        raise FileNotFoundError(f'Basins shapefile not found: {shp_path}')

    seen_shapefile_names: set[str] = set()
    features: list[dict[str, Any]] = []

    for _fields, props, geometry in iter_shapefile_features(shp_path):
        shape_name = str(props.get('name') or '').strip()
        spec = BASIN_SPEC_BY_SHAPEFILE_NAME.get(shape_name)
        if spec is None:
            raise ValueError(f'Unmapped basin in shapefile: {shape_name!r}')

        area = _area_km2(props)
        RainfallBasin.objects.update_or_create(
            slug=spec.slug,
            defaults={
                'name_en': spec.name_en,
                'name_ar': spec.name_ar,
                'area_km2': area,
            },
        )
        seen_shapefile_names.add(shape_name)
        features.append(
            {
                'type': 'Feature',
                'properties': {
                    'slug': spec.slug,
                    'name_en': spec.name_en,
                    'name_ar': spec.name_ar,
                    'area_km2': float(area) if area is not None else None,
                    'geometry_source': 'moe_basins_map',
                },
                'geometry': geometry,
            },
        )

    missing = [spec.shapefile_name for spec in BASIN_SPECS if spec.shapefile_name not in seen_shapefile_names]
    if missing:
        raise ValueError(f'Missing basins in shapefile: {", ".join(missing)}')

    payload = {'type': 'FeatureCollection', 'features': features}
    BASINS_GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BASINS_GEOJSON_PATH.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, ensure_ascii=False)

    load_official_basin_features.cache_clear()

    return {
        'basins_updated': len(features),
        'geojson_path': str(BASINS_GEOJSON_PATH),
    }
