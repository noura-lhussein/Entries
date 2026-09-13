from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ElectricityGisLayerSpec:
    id: str
    file: str
    name_en: str
    name_ar: str
    geometry_type: str
    voltage_kv: int
    default_visible: bool
    sort_order: int


DEFAULT_ELECTRICITY_GIS_DIR = Path(__file__).resolve().parent / 'data' / 'gis'

ELECTRICITY_400KV_SEGMENT_FILES: tuple[str, ...] = (
    'lines/segments_400kv/adra_der_2.shp',
    'lines/segments_400kv/alnasrya_adra.shp',
    'lines/segments_400kv/dirali_demas_1.shp',
    'lines/segments_400kv/jandar_tadamar.shp',
    'lines/segments_400kv/aleppo_f_hama2.shp',
    'lines/segments_400kv/demas_alnasrya.shp',
    'lines/segments_400kv/dier_ali_demas.shp',
    'lines/segments_400kv/jander_dimas.shp',
    'lines/segments_400kv/jander_hama2.shp',
    'lines/segments_400kv/jander_hama2_2.shp',
)

ELECTRICITY_GIS_LAYER_SPECS: tuple[ElectricityGisLayerSpec, ...] = (
    ElectricityGisLayerSpec(
        id='power-gis-substations-66',
        file='substations/substations_66kv.shp',
        name_en='66 kV substations',
        name_ar='محطات 66 ك.ف',
        geometry_type='point',
        voltage_kv=66,
        default_visible=False,
        sort_order=10,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-substations-230',
        file='substations/substations_230kv.shp',
        name_en='230 kV substations',
        name_ar='محطات 230 ك.ف',
        geometry_type='polygon',
        voltage_kv=230,
        default_visible=True,
        sort_order=20,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-substations-400',
        file='substations/substations_400kv.shp',
        name_en='400 kV substations',
        name_ar='محطات 400 ك.ف',
        geometry_type='polygon',
        voltage_kv=400,
        default_visible=True,
        sort_order=30,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-lines-66',
        file='lines/lines_66kv.shp',
        name_en='66 kV lines',
        name_ar='خطوط 66 ك.ف',
        geometry_type='line',
        voltage_kv=66,
        default_visible=False,
        sort_order=40,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-lines-230',
        file='lines/lines_230kv.shp',
        name_en='230 kV lines',
        name_ar='خطوط 230 ك.ف',
        geometry_type='line',
        voltage_kv=230,
        default_visible=True,
        sort_order=50,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-lines-400',
        file='lines/lines_400kv.shp',
        name_en='400 kV lines',
        name_ar='خطوط 400 ك.ف',
        geometry_type='line',
        voltage_kv=400,
        default_visible=True,
        sort_order=60,
    ),
    ElectricityGisLayerSpec(
        id='power-gis-renewable-sites',
        file='renewable/renewable_sites.shp',
        name_en='Proposed renewable energy sites',
        name_ar='مواقع الطاقات المتجددة المقترحة',
        geometry_type='polygon',
        voltage_kv=0,
        default_visible=True,
        sort_order=70,
    ),
)

ELECTRICITY_GIS_LAYER_BY_ID = {layer.id: layer for layer in ELECTRICITY_GIS_LAYER_SPECS}
ELECTRICITY_GIS_LAYER_IDS = frozenset(ELECTRICITY_GIS_LAYER_BY_ID)


def _clean(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def is_mojibake_arabic(text: str) -> bool:
    """Detect UTF-8 Arabic that was mis-decoded as Windows-1256 (e.g. ط³ط±ط§ظ‚ط¨)."""
    if not text or len(text) < 3:
        return False
    try:
        fixed = text.encode('cp1256').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    if fixed == text:
        return False
    arabic = sum(1 for ch in fixed if '\u0600' <= ch <= '\u06FF')
    return arabic >= 2


def sanitize_electricity_feature_name(value: Any) -> str:
    """Return a clean display name, or empty when missing / corrupted encoding."""
    name = _clean(value)
    if not name or is_mojibake_arabic(name):
        return ''
    return name


def normalize_electricity_gis_properties(layer_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    spec = ELECTRICITY_GIS_LAYER_BY_ID[layer_id]
    props = dict(raw)

    if layer_id == 'power-gis-renewable-sites':
        name = sanitize_electricity_feature_name(
            raw.get('NAME') or raw.get('namesite') or raw.get('SITE')
        )
        props['name'] = name
        props['name_en'] = name
        props['name_ar'] = name
        props['site_type'] = _clean(raw.get('LAYER') or raw.get('GM_TYPE'))
        props['description'] = props['site_type']
        props['source'] = 'electricity_gis'
        return props

    name = sanitize_electricity_feature_name(
        raw.get('name')
        or raw.get('Name')
        or raw.get('NAME')
        or raw.get('Descriptio')
        or raw.get('descriptio')
    )
    props['name'] = name
    props['name_en'] = name
    props['name_ar'] = name
    props['voltage_kv'] = spec.voltage_kv
    props['status'] = _clean(raw.get('التوص') or raw.get('status'))
    props['description'] = _clean(raw.get('descriptio') or raw.get('Descriptio') or raw.get('تصنيف'))
    props['source'] = 'electricity_gis'
    return props


def electricity_gis_feature_name(layer_id: str, props: dict[str, Any]) -> str:
    name = sanitize_electricity_feature_name(props.get('name'))
    if name:
        return name
    return ''
