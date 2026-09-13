"""Read accepted dynamic_forms Info rows linked to electricity master entities."""

from __future__ import annotations

from typing import Any

from django.db import connection
from projects.report_forms_read import facts_payload

from electricity.operational_models import PowerPlant, Substation, TransmissionLine

ENTITY_POWER_PLANT = 'power_plant'
ENTITY_SUBSTATION = 'substation'
ENTITY_TRANSMISSION_LINE = 'transmission_line'
ENTITY_POWER_GIS_SUBSTATION_66 = 'power_gis_substation_66'
ENTITY_POWER_GIS_SUBSTATION_230 = 'power_gis_substation_230'
ENTITY_POWER_GIS_SUBSTATION_400 = 'power_gis_substation_400'
ENTITY_POWER_GIS_RENEWABLE = 'power_gis_renewable'

_GIS_LAYER_BY_ENTITY = {
    ENTITY_POWER_GIS_SUBSTATION_66: 'power-gis-substations-66',
    ENTITY_POWER_GIS_SUBSTATION_230: 'power-gis-substations-230',
    ENTITY_POWER_GIS_SUBSTATION_400: 'power-gis-substations-400',
    ENTITY_POWER_GIS_RENEWABLE: 'power-gis-renewable-sites',
}


def power_plant_with_report_facts(plant_id: int) -> dict[str, Any] | None:
    plant = PowerPlant.objects.filter(pk=plant_id).first()
    if plant is None:
        return None
    return facts_payload(
        entity_type=ENTITY_POWER_PLANT,
        entity_id=plant_id,
        master={
            'plant_id': plant.id,
            'code': plant.code,
            'name_ar': plant.name_ar,
            'name_en': plant.name_en,
        },
    )


def substation_with_report_facts(substation_id: int) -> dict[str, Any] | None:
    row = Substation.objects.filter(pk=substation_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_SUBSTATION,
        entity_id=substation_id,
        master={
            'substation_id': row.id,
            'code': row.code,
            'name_ar': row.name_ar,
            'name_en': row.name_en,
        },
    )


def transmission_line_with_report_facts(line_id: int) -> dict[str, Any] | None:
    row = TransmissionLine.objects.filter(pk=line_id).first()
    if row is None:
        return None
    return facts_payload(
        entity_type=ENTITY_TRANSMISSION_LINE,
        entity_id=line_id,
        master={
            'line_id': row.id,
            'name': row.name,
            'status': row.status,
        },
    )


def _gis_electricity_feature_master(feature_id: int, layer_id: str) -> dict[str, Any] | None:
    sql = """
        SELECT f.id, f.name, f.layer_id
        FROM gis_electricity_feature f
        WHERE f.id = %s AND f.layer_id = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [feature_id, layer_id])
        row = cursor.fetchone()
    if not row:
        return None
    return {
        'feature_id': int(row[0]),
        'name': row[1] or '',
        'layer_id': row[2],
    }


def gis_electricity_feature_with_report_facts(
    *,
    entity_type: str,
    feature_id: int,
) -> dict[str, Any] | None:
    layer_id = _GIS_LAYER_BY_ENTITY.get(entity_type)
    if not layer_id:
        return None
    master = _gis_electricity_feature_master(feature_id, layer_id)
    if master is None:
        return None
    return facts_payload(
        entity_type=entity_type,
        entity_id=feature_id,
        master=master,
    )


def power_gis_substation_66_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_electricity_feature_with_report_facts(
        entity_type=ENTITY_POWER_GIS_SUBSTATION_66,
        feature_id=feature_id,
    )


def power_gis_substation_230_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_electricity_feature_with_report_facts(
        entity_type=ENTITY_POWER_GIS_SUBSTATION_230,
        feature_id=feature_id,
    )


def power_gis_substation_400_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_electricity_feature_with_report_facts(
        entity_type=ENTITY_POWER_GIS_SUBSTATION_400,
        feature_id=feature_id,
    )


def power_gis_renewable_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_electricity_feature_with_report_facts(
        entity_type=ENTITY_POWER_GIS_RENEWABLE,
        feature_id=feature_id,
    )
