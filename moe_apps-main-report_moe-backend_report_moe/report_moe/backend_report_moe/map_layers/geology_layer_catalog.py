from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class GeologyLayerSpec:
    id: str
    name_en: str
    name_ar: str
    default_visible: bool
    sort_order: int
    include_feature: Callable[[dict[str, Any]], bool]
    geometry_type: str = 'polygon'


DEFAULT_GEOLOGY_DIR = Path(__file__).resolve().parents[2] / 'geology'
GEOLOGY_SOURCE_FILE = 'geology_1-500000.shp'


def _clean(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _match_all(_props: dict[str, Any]) -> bool:
    return True


def _match_era(value: str) -> Callable[[dict[str, Any]], bool]:
    return lambda props: _clean(props.get('era')) == value


def _match_litho(value: str) -> Callable[[dict[str, Any]], bool]:
    return lambda props: _clean(props.get('litho_type')) == value


GEOLOGY_LAYER_SPECS: tuple[GeologyLayerSpec, ...] = (
    GeologyLayerSpec(
        id='geology-official',
        name_en='Geology — map colors',
        name_ar='الجيولوجيا — ألوان الخريطة',
        default_visible=False,
        sort_order=60,
        include_feature=_match_all,
    ),
    GeologyLayerSpec(
        id='geology-era',
        name_en='Geology — by geological era',
        name_ar='الجيولوجيا — حسب العصر الجيولوجي',
        default_visible=False,
        sort_order=70,
        include_feature=_match_all,
    ),
    GeologyLayerSpec(
        id='geology-cenozoic',
        name_en='Cenozoic units',
        name_ar='وحدات حقبة الحياة الحديثة',
        default_visible=False,
        sort_order=80,
        include_feature=_match_era('Cenozoic'),
    ),
    GeologyLayerSpec(
        id='geology-quaternary',
        name_en='Quaternary units',
        name_ar='وحدات رباعي',
        default_visible=False,
        sort_order=90,
        include_feature=_match_era('Quaternary'),
    ),
    GeologyLayerSpec(
        id='geology-mesozoic',
        name_en='Mesozoic units',
        name_ar='وحدات حقبة الحياة الوسطى',
        default_visible=False,
        sort_order=100,
        include_feature=_match_era('Mesozoic'),
    ),
    GeologyLayerSpec(
        id='geology-sedimentary',
        name_en='Sedimentary units',
        name_ar='وحدات رسوبية',
        default_visible=False,
        sort_order=120,
        include_feature=_match_litho('sed'),
    ),
    GeologyLayerSpec(
        id='geology-volcanic',
        name_en='Volcanic units',
        name_ar='وحدات بركانية',
        default_visible=False,
        sort_order=130,
        include_feature=_match_litho('volc'),
    ),
    GeologyLayerSpec(
        id='geology-minerals',
        name_en='Mineral deposits',
        name_ar='مواقع الخامات المعدنية',
        default_visible=True,
        sort_order=40,
        include_feature=_match_all,
        geometry_type='point',
    ),
    GeologyLayerSpec(
        id='geology-geomillion',
        name_en='Geomillion geological map',
        name_ar='الخريطة الجيولوجية (Geomillion)',
        default_visible=False,
        sort_order=50,
        include_feature=_match_all,
        geometry_type='polygon',
    ),
    GeologyLayerSpec(
        id='geology-faults',
        name_en='Geological faults',
        name_ar='الفوالق الجيولوجية',
        default_visible=False,
        sort_order=140,
        include_feature=_match_all,
        geometry_type='line',
    ),
    GeologyLayerSpec(
        id='geology-extinct-volcanoes',
        name_en='Extinct volcanoes',
        name_ar='البراكين الخامدة',
        default_visible=False,
        sort_order=150,
        include_feature=_match_all,
        geometry_type='point',
    ),
)

GEOLOGY_LAYER_BY_ID = {layer.id: layer for layer in GEOLOGY_LAYER_SPECS}


def normalize_geology_properties(raw: dict[str, Any]) -> dict[str, Any]:
    lithology_en = _clean(raw.get('lithology_') or raw.get('lithology'))
    name_ar = _clean(raw.get('name'))
    return {
        **raw,
        'lithology_en': lithology_en,
        'name_ar': name_ar,
        'geol_unit_code': raw.get('geol_unit1'),
        'geol_unit_group': raw.get('geol_uni_1'),
        'geol_unit_primary': raw.get('geol_unit_'),
        'geol_polygon_id': raw.get('geol_poli_'),
        'color_code': raw.get('color_code'),
        'era': _clean(raw.get('era')),
        'litho_type': _clean(raw.get('litho_type')),
        'age': _clean(raw.get('age')),
        'name': lithology_en or name_ar or 'Geology unit',
    }


def geology_feature_name(props: dict[str, Any]) -> str:
    return (
        _clean(props.get('name'))
        or _clean(props.get('lithology_en'))
        or _clean(props.get('mineral_type_ar'))
        or _clean(props.get('legend'))
        or _clean(props.get('symbol'))
        or 'Geology unit'
    )


def normalize_mineral_deposit_properties(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize miniral1.shp attributes (Arabic mineral type + DMS coords)."""
    mineral_type = _clean(raw.get('نوع') or raw.get('type') or raw.get('Type'))
    return {
        **raw,
        'mineral_type_ar': mineral_type,
        'name_ar': mineral_type,
        'name': mineral_type or 'Mineral deposit',
        'source_x_dms': _clean(raw.get('x')),
        'source_y_dms': _clean(raw.get('y')),
    }


def normalize_geomillion_properties(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize Geomillion GeologicalBoundaries attributes."""
    symbol = _clean(raw.get('Symbol') or raw.get('SymColor'))
    legend = _clean(raw.get('Legend'))
    return {
        **raw,
        'symbol': symbol,
        'legend': legend,
        'sym_color': _clean(raw.get('SymColor') or symbol),
        'info_path': _clean(raw.get('Path')),
        'name': legend or symbol or 'Geological unit',
        'name_ar': legend or symbol,
        'lithology_en': legend,
        'geol_unit_code': symbol,
    }


def normalize_structure_properties(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize Geomillion structure layers (faults, volcanoes, wells)."""
    class_name = _clean(raw.get('Class') or raw.get('Name'))
    sheet = _clean(raw.get('Sheet'))
    return {
        **raw,
        'class_name': class_name,
        'sheet': sheet,
        'name': class_name or sheet or 'Geological feature',
        'name_ar': class_name,
    }
