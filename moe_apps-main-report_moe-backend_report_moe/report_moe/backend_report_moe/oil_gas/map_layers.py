from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from .operational_models import Facility, Field, Pipeline, Refinery, Well

OIL_GAS_MAP_LAYER_IDS = frozenset({
    'oil-fields',
    'oil-wells',
    'oil-refineries',
    'oil-pipelines',
    'oil-fuel-stations',
})


def _float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _has_coords(lat: Decimal | None, lng: Decimal | None) -> bool:
    return lat is not None and lng is not None


def _circle_ring(lat: float, lng: float, radius_deg: float = 0.07, segments: int = 24) -> list[list[float]]:
    ring: list[list[float]] = []
    for index in range(segments + 1):
        angle = (2 * math.pi * index) / segments
        ring.append([
            lng + radius_deg * math.cos(angle),
            lat + radius_deg * math.sin(angle),
        ])
    return ring


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


def _field_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for field in Field.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        lat = _float(field.latitude)
        lng = _float(field.longitude)
        if lat is None or lng is None:
            continue
        props = {
            'feature_id': field.id,
            'code': field.code,
            'name': field.name_en or field.name_ar or field.code,
            'name_en': field.name_en,
            'name_ar': field.name_ar,
            'field_type': field.field_type,
            'governorate': field.governorate,
            'status': field.status,
            'operator_company': field.operator_company,
            'design_capacity_bpd': _float(field.design_capacity_bpd),
            'notes': field.notes,
        }
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [_circle_ring(lat, lng)],
            },
            'properties': props,
        })
    return features


def _well_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for well in (
        Well.objects.exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .select_related('field')
    ):
        lat = _float(well.latitude)
        lng = _float(well.longitude)
        if lat is None or lng is None:
            continue
        features.append(_point_feature(lat, lng, {
            'feature_id': well.id,
            'well_code': well.well_code,
            'name': well.label_en or well.well_code,
            'name_en': well.label_en,
            'name_ar': well.label_ar,
            'governorate': well.field.governorate,
            'field_code': well.field.code,
            'field_name_en': well.field.name_en,
            'field_name_ar': well.field.name_ar,
            'well_type': well.well_type,
            'status': well.status,
            'production_capacity_bpd': _float(well.production_capacity_bpd),
        }))
    return features


def _refinery_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for refinery in Refinery.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
        lat = _float(refinery.latitude)
        lng = _float(refinery.longitude)
        if lat is None or lng is None:
            continue
        features.append(_point_feature(lat, lng, {
            'feature_id': refinery.id,
            'name': refinery.refinery_name,
            'name_en': refinery.refinery_name,
            'name_ar': refinery.label_ar,
            'governorate': refinery.governorate,
            'status': refinery.status,
            'design_capacity_bpd': _float(refinery.design_capacity_bpd),
            'notes': refinery.notes,
        }))
    return features


def _pipeline_line_coordinates(pipeline: Pipeline) -> list[list[float]] | None:
    path = pipeline.path_coordinates or []
    if isinstance(path, list) and len(path) >= 2:
        coords: list[list[float]] = []
        for point in path:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                lng = float(point[0])
                lat = float(point[1])
            except (TypeError, ValueError):
                continue
            coords.append([lng, lat])
        if len(coords) >= 2:
            return coords

    if not (
        _has_coords(pipeline.source_latitude, pipeline.source_longitude)
        and _has_coords(pipeline.dest_latitude, pipeline.dest_longitude)
    ):
        return None
    return [
        [_float(pipeline.source_longitude), _float(pipeline.source_latitude)],
        [_float(pipeline.dest_longitude), _float(pipeline.dest_latitude)],
    ]


def _pipeline_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for pipeline in Pipeline.objects.all():
        coordinates = _pipeline_line_coordinates(pipeline)
        if not coordinates:
            continue
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates,
            },
            'properties': {
                'feature_id': pipeline.id,
                'name': pipeline.name,
                'name_en': pipeline.name,
                'name_ar': pipeline.label_ar,
                'source_location': pipeline.source_location,
                'destination_location': pipeline.destination_location,
                'length_km': _float(pipeline.length_km),
                'design_capacity_bpd': _float(pipeline.design_capacity_bpd),
                'status': pipeline.status,
                'notes': pipeline.notes,
            },
        })
    return features


def _facility_point_properties(facility: Facility, *, include_location: bool = True) -> dict[str, Any]:
    props: dict[str, Any] = {
        'feature_id': facility.id,
        'code': facility.code,
        'name': facility.name_en or facility.name_ar or facility.code,
        'name_en': facility.name_en,
        'name_ar': facility.name_ar or facility.name_en,
        'facility_type': facility.facility_type,
        'governorate': facility.governorate,
        'status': facility.status,
    }
    if include_location:
        props['location'] = facility.location
    return props


def _fuel_station_features() -> list[dict[str, Any]]:
    """POS2 fuel stations stored as oil_gas_facility rows with facility_type=fuel_station."""
    features: list[dict[str, Any]] = []
    for facility in Facility.objects.filter(
        facility_type=Facility.FacilityType.FUEL_STATION,
    ).exclude(latitude__isnull=True).exclude(longitude__isnull=True).order_by('name_en'):
        lat = _float(facility.latitude)
        lng = _float(facility.longitude)
        if lat is None or lng is None:
            continue
        features.append(_point_feature(lat, lng, _facility_point_properties(facility)))
    return features


def fetch_oil_gas_layer_geojson(
    layer_id: str,
    filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if layer_id not in OIL_GAS_MAP_LAYER_IDS:
        raise KeyError(layer_id)

    from map_layers.geojson_scope import filter_geojson_by_admin_filters

    builders = {
        'oil-fields': _field_features,
        'oil-wells': _well_features,
        'oil-refineries': _refinery_features,
        'oil-pipelines': _pipeline_features,
        'oil-fuel-stations': _fuel_station_features,
    }
    payload = {
        'type': 'FeatureCollection',
        'features': builders[layer_id](),
    }
    return filter_geojson_by_admin_filters(payload, filters)
