from __future__ import annotations

from decimal import Decimal
from typing import Any

from oil_gas.operational_models import Facility as OilGasFacility

from .gis_layer_catalog import ELECTRICITY_GIS_LAYER_IDS
from .gis_services import fetch_electricity_gis_layer_geojson
from .operational_models import PowerPlant, Substation, TransmissionLine

ELECTRICITY_MAP_LAYER_IDS = frozenset({
    'power-generation',
    'power-substations',
    'power-transmission',
}) | ELECTRICITY_GIS_LAYER_IDS

# Approximate Syria bounds (aligned with portal map SYRIA_BOUNDS).
_SYRIA_LAT = (32.0, 37.5)
_SYRIA_LNG = (35.5, 42.5)


def _in_syria(lat: float, lng: float) -> bool:
    return _SYRIA_LAT[0] <= lat <= _SYRIA_LAT[1] and _SYRIA_LNG[0] <= lng <= _SYRIA_LNG[1]


def _float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _has_coords(lat: Decimal | None, lng: Decimal | None) -> bool:
    return lat is not None and lng is not None


def _point_feature(
    lat: float,
    lng: float,
    properties: dict[str, Any],
) -> dict[str, Any]:
    return {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [lng, lat]},
        'properties': properties,
    }


def _oil_gas_facility_points(facility_type: str) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    qs = (
        OilGasFacility.objects.filter(facility_type=facility_type)
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
    )
    for facility in qs:
        lat = _float(facility.latitude)
        lng = _float(facility.longitude)
        if lat is None or lng is None or not _in_syria(lat, lng):
            continue
        features.append(_point_feature(lat, lng, {
            'feature_id': f'facility-{facility.id}',
            'code': facility.code,
            'name_en': facility.name_en,
            'name_ar': facility.name_ar or facility.name_en,
            'governorate': facility.governorate,
            'status': facility.status,
            'source': 'oil_gas_facility',
        }))
    return features


def _power_plant_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for plant in PowerPlant.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        lat = _float(plant.latitude)
        lng = _float(plant.longitude)
        if lat is None or lng is None or not _in_syria(lat, lng):
            continue
        seen_codes.add(plant.code)
        features.append(_point_feature(lat, lng, {
            'feature_id': plant.id,
            'code': plant.code,
            'name_en': plant.name_en,
            'name_ar': plant.name_ar,
            'plant_type': plant.plant_type,
            'fuel_type': plant.fuel_type,
            'governorate': plant.governorate,
            'status': plant.status,
            'installed_capacity_mw': _float(plant.installed_capacity_mw),
            'operator_company': plant.operator_company,
        }))
    for feature in _oil_gas_facility_points(OilGasFacility.FacilityType.POWER_PLANT):
        code = str(feature['properties'].get('code') or '')
        if code and code in seen_codes:
            continue
        features.append(feature)
    return features


def _substation_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for substation in Substation.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        lat = _float(substation.latitude)
        lng = _float(substation.longitude)
        if lat is None or lng is None or not _in_syria(lat, lng):
            continue
        seen_codes.add(substation.code)
        features.append(_point_feature(lat, lng, {
            'feature_id': substation.id,
            'code': substation.code,
            'name_en': substation.name_en,
            'name_ar': substation.name_ar,
            'role': substation.role,
            'governorate': substation.governorate,
            'status': substation.status,
            'voltage_kv': _float(substation.voltage_kv),
        }))
    for feature in _oil_gas_facility_points(OilGasFacility.FacilityType.SUBSTATION):
        code = str(feature['properties'].get('code') or '')
        if code and code in seen_codes:
            continue
        features.append(feature)
    return features


def _transmission_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for line in TransmissionLine.objects.all():
        if not (
            _has_coords(line.source_latitude, line.source_longitude)
            and _has_coords(line.dest_latitude, line.dest_longitude)
        ):
            continue
        src_lat = _float(line.source_latitude)
        src_lng = _float(line.source_longitude)
        dest_lat = _float(line.dest_latitude)
        dest_lng = _float(line.dest_longitude)
        if src_lat is None or src_lng is None or dest_lat is None or dest_lng is None:
            continue
        if not (_in_syria(src_lat, src_lng) and _in_syria(dest_lat, dest_lng)):
            continue
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [src_lng, src_lat],
                    [dest_lng, dest_lat],
                ],
            },
            'properties': {
                'feature_id': line.id,
                'name_en': line.name,
                'name_ar': line.name,
                'source_location': line.source_location,
                'destination_location': line.destination_location,
                'length_km': _float(line.length_km),
                'capacity_mw': _float(line.capacity_mw),
                'voltage_kv': _float(line.voltage_kv),
                'status': line.status,
            },
        })
    return features


def fetch_electricity_layer_geojson(
    layer_id: str,
    filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if layer_id not in ELECTRICITY_MAP_LAYER_IDS:
        raise KeyError(layer_id)

    from map_layers.geojson_scope import filter_geojson_by_admin_filters

    if layer_id in ELECTRICITY_GIS_LAYER_IDS:
        return fetch_electricity_gis_layer_geojson(layer_id, filters)

    builders = {
        'power-generation': _power_plant_features,
        'power-substations': _substation_features,
        'power-transmission': _transmission_features,
    }
    payload = {
        'type': 'FeatureCollection',
        'features': builders[layer_id](),
    }
    return filter_geojson_by_admin_filters(payload, filters)
