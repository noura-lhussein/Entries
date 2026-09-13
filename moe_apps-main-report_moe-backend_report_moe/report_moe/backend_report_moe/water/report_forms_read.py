"""
Read accepted dynamic_forms Info rows linked to water master entities.
"""

from __future__ import annotations

from typing import Any

from django.db import connection
from projects.report_forms_read import facts_payload, latest_accepted_facts_for_entity

from water.models import Dam, DrinkingWaterStation, RainfallBasin, RainfallStation

ENTITY_DRINKING_STATION = 'drinking_station'
ENTITY_DAM = 'dam'
ENTITY_RAINFALL_STATION = 'rainfall_station'
ENTITY_RAINFALL_BASIN = 'rainfall_basin'
ENTITY_SPRING = 'spring'
ENTITY_LAKE = 'lake'
ENTITY_RIVER = 'river'
ENTITY_STREAM = 'stream'
ENTITY_GEOLOGY_UNIT = 'geology_unit'

_GIS_LAYER_BY_ENTITY = {
    ENTITY_SPRING: 'water-springs',
    ENTITY_LAKE: 'water-lakes',
    ENTITY_RIVER: 'water-rivers',
    ENTITY_STREAM: 'water-streams',
    ENTITY_GEOLOGY_UNIT: 'geology-official',
}


def drinking_station_with_report_facts(station_id: int) -> dict[str, Any] | None:
    station = DrinkingWaterStation.objects.filter(pk=station_id).first()
    if station is None:
        return None
    payload = facts_payload(
        entity_type=ENTITY_DRINKING_STATION,
        entity_id=station_id,
        master={
            'station_id': station.id,
            'station_code': station.station_code,
            'name': station.name,
            'governorate': station.governorate,
            'is_operational': station.is_operational,
        },
    )
    if payload['fallback'] == 'legacy':
        payload['fallback'] = 'legacy_station'
    return payload


def dam_with_report_facts(dam_id: int) -> dict[str, Any] | None:
    dam = Dam.objects.filter(pk=dam_id).first()
    if dam is None:
        return None
    return facts_payload(
        entity_type=ENTITY_DAM,
        entity_id=dam_id,
        master={
            'dam_id': dam.id,
            'name': dam.name,
            'governorate': dam.governorate,
            'max_storage_mcm': (
                float(dam.max_storage_mcm) if dam.max_storage_mcm is not None else None
            ),
        },
    )


def rainfall_station_with_report_facts(station_id: int) -> dict[str, Any] | None:
    station = RainfallStation.objects.filter(pk=station_id).first()
    if station is None:
        return None
    return facts_payload(
        entity_type=ENTITY_RAINFALL_STATION,
        entity_id=station_id,
        master={
            'station_id': station.id,
            'name': station.name,
            'governorate': station.governorate,
            'basin_id': station.basin_id,
        },
    )


def rainfall_basin_with_report_facts(basin_id: int) -> dict[str, Any] | None:
    basin = RainfallBasin.objects.filter(pk=basin_id).first()
    if basin is None:
        return None
    return facts_payload(
        entity_type=ENTITY_RAINFALL_BASIN,
        entity_id=basin_id,
        master={
            'basin_id': basin.id,
            'name_ar': basin.name_ar,
            'name_en': basin.name_en,
        },
    )


def _gis_water_feature_master(feature_id: int, layer_id: str) -> dict[str, Any] | None:
    sql = """
        SELECT f.id, f.name, f.layer_id
        FROM gis_water_feature f
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


def gis_water_feature_with_report_facts(
    *,
    entity_type: str,
    feature_id: int,
) -> dict[str, Any] | None:
    layer_id = _GIS_LAYER_BY_ENTITY.get(entity_type)
    if not layer_id:
        return None
    master = _gis_water_feature_master(feature_id, layer_id)
    if master is None:
        return None
    return facts_payload(
        entity_type=entity_type,
        entity_id=feature_id,
        master=master,
    )


def spring_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_water_feature_with_report_facts(
        entity_type=ENTITY_SPRING,
        feature_id=feature_id,
    )


def lake_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_water_feature_with_report_facts(
        entity_type=ENTITY_LAKE,
        feature_id=feature_id,
    )


def river_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_water_feature_with_report_facts(
        entity_type=ENTITY_RIVER,
        feature_id=feature_id,
    )


def stream_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_water_feature_with_report_facts(
        entity_type=ENTITY_STREAM,
        feature_id=feature_id,
    )


def geology_unit_with_report_facts(feature_id: int) -> dict[str, Any] | None:
    return gis_water_feature_with_report_facts(
        entity_type=ENTITY_GEOLOGY_UNIT,
        feature_id=feature_id,
    )


def map_report_facts_by_station_ids(
    station_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for station_id in station_ids:
        facts = latest_accepted_facts_for_entity(
            entity_type=ENTITY_DRINKING_STATION,
            entity_id=int(station_id),
        )
        if facts:
            out[int(station_id)] = facts
    return out
