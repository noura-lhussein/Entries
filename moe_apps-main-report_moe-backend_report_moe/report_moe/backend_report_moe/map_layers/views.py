"""Map layer endpoints.

Converted from Django Ninja. The URLs, the payloads and the status codes are
unchanged on purpose — the portal reads them directly, so `tests/parity` compares
these responses against the ones Ninja produced.

The views stay thin: catalogs come from the `*_layer_catalog` modules and geometry
from `services` / `water_services`, exactly as before. Only the framework wrapper
around them is new.
"""

from __future__ import annotations

from accounts.drf_permissions import CanAccessMineral, CanAccessWater
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .geology_info_loader import load_geology_info_catalog
from .geology_layer_catalog import GEOLOGY_LAYER_BY_ID, GEOLOGY_LAYER_SPECS
from .map_layer_catalog import layer_to_dict
from .services import fetch_filter_options, fetch_layer_geojson, list_admin_layers
from .water_layer_catalog import WATER_LAYER_SPECS
from .water_services import fetch_springs_map_catalog, fetch_water_layer_geojson

# Query parameters accepted by the admin-boundary layers, in the order the
# GeoJSON services expect them.
ADMIN_FILTER_KEYS = (
    "governorate",
    "district",
    "subdistrict",
    "adm0_pcode",
    "adm1_pcode",
    "adm2_pcode",
    "adm3_pcode",
    "pcode",
)
AREA_FILTER_KEYS = ("governorate", "district", "subdistrict")

# `filter_key` is part of the public URL; the value is the catalog layer it reads.
FILTER_LAYERS = {
    "governorate": "governorate",
    "district": "district",
    "subdistrict": "subdistrict",
}


def _filters(request, keys: tuple[str, ...]) -> dict[str, str | None]:
    """Every key is always present — the services distinguish absent from empty."""
    return {key: request.query_params.get(key) for key in keys}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_layers(request):
    return Response(list_admin_layers())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_layer_geojson(request, layer_id: str):
    try:
        return Response(fetch_layer_geojson(layer_id, _filters(request, ADMIN_FILTER_KEYS)))
    except KeyError:
        raise NotFound("Layer not found.")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def filter_options(request, filter_key: str):
    layer_id = FILTER_LAYERS.get(filter_key)
    if not layer_id:
        raise NotFound("Filter not found.")
    try:
        return Response(fetch_filter_options(layer_id, _filters(request, ("governorate", "district"))))
    except KeyError:
        raise NotFound("Filter not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def water_layers(request):
    return Response([layer_to_dict(layer) for layer in WATER_LAYER_SPECS])


@api_view(["GET"])
@permission_classes([CanAccessWater])
def water_layer_geojson(request, layer_id: str):
    # Geology layers live in the same table but are served under their own route,
    # so asking for one here is a miss rather than a cross-sector read.
    if layer_id in GEOLOGY_LAYER_BY_ID:
        raise NotFound("Layer not found.")
    try:
        return Response(fetch_water_layer_geojson(layer_id, _filters(request, AREA_FILTER_KEYS)))
    except KeyError:
        raise NotFound("Layer not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def springs_map_catalog(request):
    return Response(fetch_springs_map_catalog())


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def geology_layers(request):
    return Response([layer_to_dict(layer) for layer in GEOLOGY_LAYER_SPECS])


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def geology_layer_geojson(request, layer_id: str):
    if layer_id not in GEOLOGY_LAYER_BY_ID:
        raise NotFound("Layer not found.")
    try:
        return Response(fetch_water_layer_geojson(layer_id, _filters(request, AREA_FILTER_KEYS)))
    except KeyError:
        raise NotFound("Layer not found.")


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def geology_info(request):
    return Response(load_geology_info_catalog())
