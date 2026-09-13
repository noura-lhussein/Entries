from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class AdminLayerSpec:
    id: str
    file: str
    name_en: str
    name_ar: str
    geometry_type: str
    admin_level: int | None
    default_visible: bool
    sort_order: int
    filter_key: str | None = None


DEFAULT_BOUNDARIES_DIR = Path(__file__).resolve().parents[2] / 'syr_admin_boundaries.geojson'

ADMIN_LAYER_SPECS: tuple[AdminLayerSpec, ...] = (
    AdminLayerSpec(
        id='admin0',
        file='syr_admin0.geojson',
        name_en='Country boundary',
        name_ar='حدود الدولة',
        geometry_type='polygon',
        admin_level=0,
        default_visible=False,
        sort_order=10,
    ),
    AdminLayerSpec(
        id='governorate',
        file='syr_admin1.geojson',
        name_en='Governorates',
        name_ar='المحافظات',
        geometry_type='polygon',
        admin_level=1,
        default_visible=True,
        sort_order=20,
        filter_key='governorate',
    ),
    AdminLayerSpec(
        id='district',
        file='syr_admin2.geojson',
        name_en='Districts',
        name_ar='المناطق',
        geometry_type='polygon',
        admin_level=2,
        default_visible=False,
        sort_order=30,
        filter_key='district',
    ),
    AdminLayerSpec(
        id='subdistrict',
        file='syr_admin3.geojson',
        name_en='Sub-districts',
        name_ar='النواحي',
        geometry_type='polygon',
        admin_level=3,
        default_visible=False,
        sort_order=40,
        filter_key='subdistrict',
    ),
    AdminLayerSpec(
        id='admin-lines',
        file='syr_adminlines.geojson',
        name_en='Administrative lines',
        name_ar='خطوط إدارية',
        geometry_type='line',
        admin_level=None,
        default_visible=False,
        sort_order=50,
    ),
    AdminLayerSpec(
        id='admin-points',
        file='syr_adminpoints.geojson',
        name_en='Administrative points',
        name_ar='نقاط إدارية',
        geometry_type='point',
        admin_level=None,
        default_visible=False,
        sort_order=60,
    ),
    AdminLayerSpec(
        id='admin-capitals',
        file='syr_admincapitals.geojson',
        name_en='Admin capitals',
        name_ar='مراكز إدارية',
        geometry_type='point',
        admin_level=None,
        default_visible=False,
        sort_order=70,
    ),
    AdminLayerSpec(
        id='neighborhoods',
        file='syr_neighborhoods.geojson',
        name_en='Neighborhoods',
        name_ar='الأحياء',
        geometry_type='polygon',
        admin_level=4,
        default_visible=False,
        sort_order=80,
    ),
    AdminLayerSpec(
        id='populated-places',
        file='syr_populatedplaces.geojson',
        name_en='Populated places',
        name_ar='الأماكن المأهولة',
        geometry_type='point',
        admin_level=None,
        default_visible=False,
        sort_order=90,
    ),
)

ADMIN_LAYER_BY_ID = {layer.id: layer for layer in ADMIN_LAYER_SPECS}


def _pick(props: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = props.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def extract_feature_fields(layer_id: str, props: dict[str, Any]) -> dict[str, Any]:
    pcode = _pick(
        props,
        'adm3_pcode',
        'adm2_pcode',
        'adm1_pcode',
        'adm0_pcode',
        'neighborhoodpcode',
        'areapcode',
        'loc_pcode',
        'pcode',
        'left_pcod',
    )

    if layer_id == 'admin-lines':
        pcode = _pick(props, 'left_pcod', 'right_pcod', 'name')

    name_en = _pick(
        props,
        'adm3_name',
        'adm2_name',
        'adm1_name',
        'adm0_name',
        'neighborhoodname_en',
        'areaname_en',
        'featurename_en',
        'name',
        'adm4_name',
    )
    name_ar = _pick(
        props,
        'adm3_name1',
        'adm2_name1',
        'adm1_name1',
        'adm0_name1',
        'neighborhoodname_ar',
        'areaname_ar',
        'featurename_ar',
        'name_1',
        'name1',
        'adm4_name1',
    )

    return {
        'pcode': pcode,
        'name_en': name_en,
        'name_ar': name_ar,
        'adm0_pcode': _pick(props, 'adm0_pcode'),
        'adm1_pcode': _pick(props, 'adm1_pcode'),
        'adm2_pcode': _pick(props, 'adm2_pcode'),
        'adm3_pcode': _pick(props, 'adm3_pcode'),
    }
