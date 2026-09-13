from __future__ import annotations

from typing import Any

from .models import DrinkingWaterStation

SURVEY_FIELD_NAMES = (
    'enrollment_date',
    'org_unit',
    'building_condition',
    'is_operational',
    'non_operational_reason',
    'previously_rehabilitated',
    'rehabilitation_type',
    'has_water_hammer_protection',
    'water_hammer_efficiency',
    'needs_solar_installation',
    'needs_solar_power',
    'solar_space_available',
    'safety_procedures',
    'has_water_tanks',
    'has_public_grid_supply',
    'has_grid_power',
    'grid_connection_working',
    'electrical_connection_efficiency',
    'transformer_efficiency',
    'electrical_panel_efficiency',
    'grid_power_productivity',
    'solar_power_available',
    'solar_power_productivity',
    'solar_system_efficiency',
    'generator_available',
    'alternative_power_source',
    'is_well_station',
    'is_filtration_station',
    'is_boosting_station',
    'is_water_analyzed',
    'lab_equipment_status',
)


def drinking_water_import_status() -> dict[str, Any]:
    qs = DrinkingWaterStation.objects.all()
    operational = qs.filter(is_operational=True).count()
    non_operational = qs.filter(is_operational=False).count()
    with_coordinates = qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count()
    with_survey = qs.exclude(is_operational__isnull=True).count()
    latest_enrollment = qs.exclude(enrollment_date__isnull=True).order_by('-enrollment_date').values_list(
        'enrollment_date', flat=True,
    ).first()
    return {
        'stations': qs.count(),
        'with_coordinates': with_coordinates,
        'with_survey': with_survey,
        'operational': operational,
        'non_operational': non_operational,
        'latest_enrollment_date': latest_enrollment.isoformat() if latest_enrollment else None,
    }


def drinking_water_station_lookups() -> list[dict[str, Any]]:
    return [
        {
            'id': station.id,
            'station_code': station.station_code,
            'name': station.name,
            'governorate': station.governorate,
            'district': station.district,
            'tei_id': station.tei_id,
            'is_operational': station.is_operational,
        }
        for station in DrinkingWaterStation.objects.order_by('governorate', 'name')
    ]


def serialize_drinking_water_station(station: DrinkingWaterStation) -> dict[str, Any]:
    return {
        'station_id': station.id,
        'id': station.id,
        'tei_id': station.tei_id,
        'station_code': station.station_code,
        'name': station.name,
        'governorate': station.governorate,
        'district': station.district,
        'subdistrict': station.subdistrict,
        'community': station.community,
        'address': station.address,
        'latitude': float(station.latitude) if station.latitude is not None else None,
        'longitude': float(station.longitude) if station.longitude is not None else None,
        'enrollment_date': station.enrollment_date.isoformat() if station.enrollment_date else '',
        'building_condition': station.building_condition or '',
        'is_operational': _bool_to_choice(station.is_operational),
        'non_operational_reason': station.non_operational_reason or '',
        'previously_rehabilitated': _bool_to_choice(station.previously_rehabilitated),
        'rehabilitation_type': station.rehabilitation_type or '',
        'has_water_hammer_protection': _bool_to_choice(station.has_water_hammer_protection),
        'water_hammer_efficiency': station.water_hammer_efficiency or '',
        'needs_solar_installation': _bool_to_choice(station.needs_solar_installation),
        'needs_solar_power': _bool_to_choice(station.needs_solar_power),
        'solar_space_available': _bool_to_choice(station.solar_space_available),
        'safety_procedures': station.safety_procedures or '',
        'has_water_tanks': _bool_to_choice(station.has_water_tanks),
        'has_public_grid_supply': _bool_to_choice(station.has_public_grid_supply),
        'has_grid_power': _bool_to_choice(station.has_grid_power),
        'grid_connection_working': _bool_to_choice(station.grid_connection_working),
        'electrical_connection_efficiency': station.electrical_connection_efficiency or '',
        'transformer_efficiency': station.transformer_efficiency or '',
        'electrical_panel_efficiency': station.electrical_panel_efficiency or '',
        'grid_power_productivity': station.grid_power_productivity or '',
        'solar_power_available': _bool_to_choice(station.solar_power_available),
        'solar_power_productivity': station.solar_power_productivity or '',
        'solar_system_efficiency': station.solar_system_efficiency or '',
        'generator_available': _bool_to_choice(station.generator_available),
        'alternative_power_source': _bool_to_choice(station.alternative_power_source),
        'is_well_station': _bool_to_choice(station.is_well_station),
        'is_filtration_station': _bool_to_choice(station.is_filtration_station),
        'is_boosting_station': _bool_to_choice(station.is_boosting_station),
        'is_water_analyzed': _bool_to_choice(station.is_water_analyzed),
        'lab_equipment_status': station.lab_equipment_status or '',
    }


def get_drinking_water_station(station_id: int) -> dict[str, Any] | None:
    station = DrinkingWaterStation.objects.filter(pk=station_id).first()
    if not station:
        return None
    return serialize_drinking_water_station(station)


def _bool_to_choice(value: bool | None) -> str:
    if value is True:
        return 'yes'
    if value is False:
        return 'no'
    return ''


