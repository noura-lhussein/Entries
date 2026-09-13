from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WaterLayerSpec:
    id: str
    file: str
    name_en: str
    name_ar: str
    geometry_type: str
    default_visible: bool
    sort_order: int


DEFAULT_WATER_DIR = Path(__file__).resolve().parents[2] / 'Water'

WATER_LAYER_SPECS: tuple[WaterLayerSpec, ...] = (
    WaterLayerSpec(
        id='water-lakes',
        file='lakes/lakes.shp',
        name_en='Lakes',
        name_ar='البحيرات',
        geometry_type='polygon',
        default_visible=True,
        sort_order=10,
    ),
    WaterLayerSpec(
        id='water-rivers',
        file='rivers/main_river.shp',
        name_en='Main rivers',
        name_ar='الأنهار الرئيسية',
        geometry_type='line',
        default_visible=False,
        sort_order=20,
    ),
    WaterLayerSpec(
        id='water-streams',
        file='streams/streams.shp',
        name_en='Stream network',
        name_ar='شبكة المسيلات المائية',
        geometry_type='line',
        default_visible=False,
        sort_order=30,
    ),
    WaterLayerSpec(
        id='water-dams',
        file='dams/dam_SY.shp',
        name_en='Dams',
        name_ar='السدود',
        geometry_type='point',
        default_visible=False,
        sort_order=40,
    ),
    WaterLayerSpec(
        id='water-springs',
        file='springs/spring_all.shp',
        name_en='Springs',
        name_ar='الينابيع',
        geometry_type='point',
        default_visible=False,
        sort_order=50,
    ),
    WaterLayerSpec(
        id='water-drinking-stations',
        file='',
        name_en='Drinking water stations',
        name_ar='محطات مياه الشرب',
        geometry_type='point',
        default_visible=False,
        sort_order=55,
    ),
)

WATER_DB_SYNC_LAYER_IDS = frozenset({'water-drinking-stations'})

WATER_LAYER_BY_ID = {layer.id: layer for layer in WATER_LAYER_SPECS}


def _clean(value: Any) -> str:
    if value is None:
        return ''
    text = str(value).strip()
    return text


def normalize_water_properties(layer_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize shapefile attrs into canonical keys.

    Prefer already-normalized admin fields (e.g. governorate_name) over legacy
    shapefile columns (e.g. MOHAFAZA) so portal edits are not overwritten.
    """
    props = dict(raw)

    if layer_id == 'water-lakes':
        props['name'] = _clean(raw.get('name') or raw.get('NAME'))
        props['governorate_name'] = _clean(
            raw.get('governorate_name') or raw.get('MOHAFAZA') or raw.get('mohafaza')
        )
        props['NAME'] = props['name']
        props['MOHAFAZA'] = props['governorate_name']
    elif layer_id == 'water-rivers':
        props['name'] = _clean(raw.get('name') or raw.get('NAME'))
        props['river_type'] = _clean(raw.get('river_type') or raw.get('type') or raw.get('TYPE'))
        props['NAME'] = props['name']
        props['type'] = props['river_type']
    elif layer_id == 'water-streams':
        props['arc_id'] = raw.get('arc_id') if raw.get('arc_id') is not None else raw.get('ARCID')
        props['up_cells'] = raw.get('up_cells') if raw.get('up_cells') is not None else raw.get('UP_CELLS')
        if raw.get('name'):
            props['name'] = _clean(raw.get('name'))
    elif layer_id == 'water-dams':
        props['name'] = _clean(raw.get('name') or raw.get('name2') or raw.get('NAME'))
        props['basin_name'] = _clean(raw.get('basin_name') or raw.get('BASIN_NAME'))
        props['governorate_name'] = _clean(raw.get('governorate_name') or raw.get('MOHAFAZA'))
        props['purpose'] = _clean(raw.get('purpose') or raw.get('PURPOSE'))
        props['status'] = _clean(raw.get('status') or raw.get('STATUS'))
        props['dam_year'] = raw.get('dam_year') if raw.get('dam_year') is not None else raw.get('DAM_DATE')
        props['storage_mm'] = raw.get('storage_mm') if raw.get('storage_mm') is not None else raw.get('STORAGE_MM')
        props['dam_height_m'] = (
            raw.get('dam_height_m') if raw.get('dam_height_m') is not None else raw.get('HIGH_DAM')
        )
        props['dam_type'] = _clean(raw.get('dam_type') or raw.get('TYPE_DAM'))
        props['MOHAFAZA'] = props['governorate_name']
    elif layer_id == 'water-springs':
        props['name'] = _clean(raw.get('name') or raw.get('NAME'))
        props['governorate_name'] = _clean(
            raw.get('governorate_name') or raw.get('mohafaza') or raw.get('MOHAFAZA')
        )
        props['elevation_m'] = (
            raw.get('elevation_m') if raw.get('elevation_m') is not None else raw.get('z')
        )
        props['avg_flow_25y'] = (
            raw.get('avg_flow_25y') if raw.get('avg_flow_25y') is not None else raw.get('AVG25y')
        )
        props['MOHAFAZA'] = props['governorate_name']
        props['mohafaza'] = props['governorate_name']

    return props


def water_feature_name(layer_id: str, props: dict[str, Any]) -> str:
    explicit = _clean(props.get('name'))
    if layer_id == 'water-streams':
        if explicit:
            return explicit
        arc = props.get('arc_id')
        return f'Stream {arc}' if arc is not None else 'Stream'
    return explicit or WATER_LAYER_BY_ID[layer_id].name_en
