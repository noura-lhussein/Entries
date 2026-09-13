from __future__ import annotations

from decimal import Decimal
from typing import Any

from map_layers.water_layer_catalog import WATER_DB_SYNC_LAYER_IDS
from map_layers.water_services import (
    clear_water_layer_features,
    insert_water_feature,
    upsert_water_layer_catalog,
)

from .drinking_water_dashboard import (
    GOVERNORATE_AR,
    NON_OPERATIONAL_REASON_LABELS,
    _admin_name_ar_map,
)
from .models import DrinkingWaterStation

DRINKING_WATER_MAP_LAYER_ID = 'water-drinking-stations'

# Approximate Syria bounds (aligned with portal map SYRIA_BOUNDS).
_SYRIA_LAT = (32.0, 37.5)
_SYRIA_LNG = (35.5, 42.5)


def _float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _in_syria(lat: float, lng: float) -> bool:
    return _SYRIA_LAT[0] <= lat <= _SYRIA_LAT[1] and _SYRIA_LNG[0] <= lng <= _SYRIA_LNG[1]


def _bool_label(value: bool | None) -> dict[str, str | None]:
    if value is True:
        return {'en': 'Yes', 'ar': 'نعم'}
    if value is False:
        return {'en': 'No', 'ar': 'لا'}
    return {'en': None, 'ar': None}


def _reason_labels(slug: str) -> dict[str, str]:
    labels = NON_OPERATIONAL_REASON_LABELS.get(slug.strip().lower())
    if not labels:
        return {'en': slug, 'ar': slug}
    return {'en': labels[0], 'ar': labels[1]}


def station_map_properties(
    station: DrinkingWaterStation,
    *,
    district_ar_map: dict[str, str] | None = None,
    subdistrict_ar_map: dict[str, str] | None = None,
    community_ar_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    reason_slug = (station.non_operational_reason or '').strip().lower()
    reason_labels = _reason_labels(reason_slug) if reason_slug else {'en': '', 'ar': ''}
    operational = _bool_label(station.is_operational)
    district = (station.district or '').strip()
    subdistrict = (station.subdistrict or '').strip()
    community = (station.community or '').strip()
    district_labels = district_ar_map or {}
    subdistrict_labels = subdistrict_ar_map or {}
    community_labels = community_ar_map or {}
    return {
        'station_id': station.id,
        'station_code': station.station_code,
        'governorate': station.governorate,
        'governorate_ar': GOVERNORATE_AR.get(station.governorate, station.governorate),
        'governorate_name': station.governorate,
        'district': district,
        'district_ar': district_labels.get(district, district) if district else '',
        'subdistrict': subdistrict,
        'subdistrict_ar': subdistrict_labels.get(subdistrict, subdistrict) if subdistrict else '',
        'community': community,
        'community_ar': community_labels.get(community, community) if community else '',
        'address': station.address,
        'org_unit': station.org_unit,
        'enrollment_date': station.enrollment_date.isoformat() if station.enrollment_date else None,
        'is_operational': station.is_operational,
        'is_operational_en': operational['en'],
        'is_operational_ar': operational['ar'],
        'non_operational_reason': reason_slug,
        'non_operational_reason_en': reason_labels['en'],
        'non_operational_reason_ar': reason_labels['ar'],
        'is_boosting_station': station.is_boosting_station,
        'is_well_station': station.is_well_station,
        'is_filtration_station': station.is_filtration_station,
        'has_grid_power': station.has_grid_power,
        'needs_solar_power': station.needs_solar_power,
    }


def sync_drinking_water_map_layer() -> dict[str, int]:
    """Sync DrinkingWaterStation rows into gis_water_feature (layer water-drinking-stations)."""
    if DRINKING_WATER_MAP_LAYER_ID not in WATER_DB_SYNC_LAYER_IDS:
        raise RuntimeError(f'Layer {DRINKING_WATER_MAP_LAYER_ID} is not configured for DB sync')

    upsert_water_layer_catalog()
    clear_water_layer_features(DRINKING_WATER_MAP_LAYER_ID)

    imported = 0
    qs = (
        DrinkingWaterStation.objects.exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .order_by('governorate', 'name', 'id')
    )
    district_ar_map = _admin_name_ar_map(
        'district',
        set(qs.exclude(district='').values_list('district', flat=True)),
    )
    subdistrict_ar_map = _admin_name_ar_map(
        'subdistrict',
        set(qs.exclude(subdistrict='').values_list('subdistrict', flat=True)),
    )
    community_ar_map = _admin_name_ar_map(
        'populated-places',
        set(qs.exclude(community='').values_list('community', flat=True)),
    )
    for station in qs:
        lat = _float(station.latitude)
        lng = _float(station.longitude)
        if lat is None or lng is None or not _in_syria(lat, lng):
            continue
        geometry = {'type': 'Point', 'coordinates': [lng, lat]}
        insert_water_feature(
            DRINKING_WATER_MAP_LAYER_ID,
            station.name,
            station_map_properties(
                station,
                district_ar_map=district_ar_map,
                subdistrict_ar_map=subdistrict_ar_map,
                community_ar_map=community_ar_map,
            ),
            geometry,
        )
        imported += 1

    return {'imported': imported}
