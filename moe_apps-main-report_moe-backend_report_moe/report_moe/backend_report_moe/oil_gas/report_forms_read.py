"""Read accepted dynamic_forms Info rows linked to oil/gas master entities."""

from __future__ import annotations

from typing import Any

from projects.report_forms_read import facts_payload

from oil_gas.operational_models import Facility, Field, Pipeline, Refinery, Well

ENTITY_OIL_FIELD = 'oil_field'
ENTITY_OIL_WELL = 'oil_well'
ENTITY_OIL_REFINERY = 'oil_refinery'
ENTITY_FUEL_STATION = 'fuel_station'
ENTITY_STORAGE_DEPOT = 'storage_depot'
ENTITY_PIPELINE = 'pipeline'


def oil_field_with_report_facts(field_id: int) -> dict[str, Any] | None:
    row = Field.objects.filter(pk=field_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_OIL_FIELD,
        entity_id=field_id,
        master={
            'field_id': row.id,
            'code': row.code,
            'name_ar': row.name_ar,
            'name_en': row.name_en,
        },
    )


def oil_well_with_report_facts(well_id: int) -> dict[str, Any] | None:
    row = Well.objects.filter(pk=well_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_OIL_WELL,
        entity_id=well_id,
        master={
            'well_id': row.id,
            'well_code': row.well_code,
            'name_ar': getattr(row, 'name_ar', '') or '',
        },
    )


def oil_refinery_with_report_facts(refinery_id: int) -> dict[str, Any] | None:
    row = Refinery.objects.filter(pk=refinery_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_OIL_REFINERY,
        entity_id=refinery_id,
        master={
            'refinery_id': row.id,
            'refinery_name': row.refinery_name,
            'name_ar': row.name_ar,
        },
    )


def fuel_station_with_report_facts(facility_id: int) -> dict[str, Any] | None:
    row = Facility.objects.filter(
        pk=facility_id,
        facility_type=Facility.FacilityType.FUEL_STATION,
    ).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_FUEL_STATION,
        entity_id=facility_id,
        master={
            'facility_id': row.id,
            'code': row.code,
            'name_ar': row.name_ar,
            'name_en': row.name_en,
        },
    )


def storage_depot_with_report_facts(facility_id: int) -> dict[str, Any] | None:
    row = Facility.objects.filter(
        pk=facility_id,
        facility_type=Facility.FacilityType.STORAGE_DEPOT,
    ).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_STORAGE_DEPOT,
        entity_id=facility_id,
        master={
            'facility_id': row.id,
            'code': row.code,
            'name_ar': row.name_ar,
            'name_en': row.name_en,
        },
    )


def pipeline_with_report_facts(pipeline_id: int) -> dict[str, Any] | None:
    row = Pipeline.objects.filter(pk=pipeline_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_PIPELINE,
        entity_id=pipeline_id,
        master={
            'pipeline_id': row.id,
            'name': row.name,
            'name_ar': row.name_ar,
            'status': row.status,
        },
    )
