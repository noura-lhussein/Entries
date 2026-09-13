from __future__ import annotations

from datetime import date
from typing import Any

from django.http import HttpResponse

from .drinking_water_survey_schema import (
    NON_OPERATIONAL_REASON_EXPORT,
    PRODUCTIVITY_EXPORT,
    SURVEY_PORTAL_COLUMNS,
    portal_header_row,
)
from .models import DrinkingWaterStation
from .template_generator import _xlsx_response


def _bool_export(value: bool | None) -> str:
    if value is True:
        return 'yes'
    if value is False:
        return 'no'
    return ''


def _date_export(value: date | None) -> str:
    return value.isoformat() if value else ''


def _productivity_export(value: str | None) -> str:
    text = (value or '').strip()
    if not text:
        return ''
    return PRODUCTIVITY_EXPORT.get(text, text.replace('_', '-'))


def _reason_export(value: str | None) -> str:
    text = (value or '').strip()
    if not text:
        return ''
    return NON_OPERATIONAL_REASON_EXPORT.get(text, text)


def station_to_portal_row(station: DrinkingWaterStation) -> list[Any]:
    values: dict[str, Any] = {
        'tei_id': station.tei_id or '',
        'station_code': station.station_code or '',
        'name': station.name or '',
        'governorate': station.governorate or '',
        'enrollment_date': _date_export(station.enrollment_date),
        'org_unit': station.org_unit or '',
        'building_condition': station.building_condition or '',
        'is_operational': _bool_export(station.is_operational),
        'non_operational_reason': _reason_export(station.non_operational_reason),
        'previously_rehabilitated': _bool_export(station.previously_rehabilitated),
        'rehabilitation_type': station.rehabilitation_type or '',
        'has_water_hammer_protection': _bool_export(station.has_water_hammer_protection),
        'water_hammer_efficiency': station.water_hammer_efficiency or '',
        'needs_solar_installation': _bool_export(station.needs_solar_installation),
        'solar_space_available': _bool_export(station.solar_space_available),
        'safety_procedures': station.safety_procedures or '',
        'has_water_tanks': _bool_export(station.has_water_tanks),
        'has_public_grid_supply': _bool_export(station.has_public_grid_supply),
        'grid_connection_working': _bool_export(station.grid_connection_working),
        'electrical_connection_efficiency': station.electrical_connection_efficiency or '',
        'transformer_efficiency': station.transformer_efficiency or '',
        'electrical_panel_efficiency': station.electrical_panel_efficiency or '',
        'grid_power_productivity': _productivity_export(station.grid_power_productivity),
        'solar_power_available': _bool_export(station.solar_power_available),
        'solar_power_productivity': _productivity_export(station.solar_power_productivity),
        'solar_system_efficiency': station.solar_system_efficiency or '',
        'generator_available': _bool_export(station.generator_available),
        'alternative_power_source': _bool_export(station.alternative_power_source),
        'is_well_station': _bool_export(station.is_well_station),
        'is_filtration_station': _bool_export(station.is_filtration_station),
        'is_boosting_station': _bool_export(station.is_boosting_station),
        'is_water_analyzed': _bool_export(station.is_water_analyzed),
        'lab_equipment_status': station.lab_equipment_status or '',
    }
    return [values[key] for key, _, _ in SURVEY_PORTAL_COLUMNS]


def build_survey_export_rows() -> list[list[Any]]:
    rows: list[list[Any]] = [portal_header_row()]
    for station in DrinkingWaterStation.objects.order_by('governorate', 'name', 'station_code'):
        rows.append(station_to_portal_row(station))
    return rows


def build_survey_template_rows() -> list[list[Any]]:
    return [portal_header_row()]


def drinking_water_survey_export_response() -> HttpResponse:
    return _xlsx_response('drinking_water_tei_survey_export.xlsx', build_survey_export_rows)


def drinking_water_survey_template_response() -> HttpResponse:
    return _xlsx_response('drinking_water_tei_survey_template.xlsx', build_survey_template_rows)
