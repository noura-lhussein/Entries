from __future__ import annotations

from typing import Any

from .geology_layer_catalog import GEOLOGY_LAYER_BY_ID, GEOLOGY_LAYER_SPECS, GeologyLayerSpec
from .water_layer_catalog import WATER_LAYER_BY_ID, WATER_LAYER_SPECS, WaterLayerSpec

MAP_LAYER_SPECS: tuple[WaterLayerSpec | GeologyLayerSpec, ...] = WATER_LAYER_SPECS + GEOLOGY_LAYER_SPECS
MAP_LAYER_BY_ID: dict[str, WaterLayerSpec | GeologyLayerSpec] = {
    **WATER_LAYER_BY_ID,
    **GEOLOGY_LAYER_BY_ID,
}


def layer_geometry_type(layer: WaterLayerSpec | GeologyLayerSpec) -> str:
    return layer.geometry_type


def layer_to_dict(layer: WaterLayerSpec | GeologyLayerSpec) -> dict[str, Any]:
    sector = 'mineral-resources' if isinstance(layer, GeologyLayerSpec) else 'water-resources'
    return {
        'id': layer.id,
        'name_en': layer.name_en,
        'name_ar': layer.name_ar,
        'geometry_type': layer_geometry_type(layer),
        'default_visible': layer.default_visible,
        'sort_order': layer.sort_order,
        'sector': sector,
    }
