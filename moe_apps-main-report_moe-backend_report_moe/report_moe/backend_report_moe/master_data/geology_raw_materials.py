"""Layer specs + property normalizers for the MOE "ملفات الخامات" raw-materials
package (mineral deposits, Geomillion geological map, faults, extinct volcanoes).

Self-contained subset of moeds's gis/geology_layer_catalog.py — kept in sync by
hand since report_moe and moeds are separate deployments. report_moe owns these
GIS tables (see enforce_single_writer.sql), so the importer lives here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RawMaterialLayerSpec:
    id: str
    name_en: str
    name_ar: str
    default_visible: bool
    sort_order: int
    geometry_type: str


RAW_MATERIAL_LAYER_SPECS: tuple[RawMaterialLayerSpec, ...] = (
    RawMaterialLayerSpec(
        id='geology-minerals',
        name_en='Mineral deposits',
        name_ar='مواقع الخامات المعدنية',
        default_visible=True,
        sort_order=40,
        geometry_type='point',
    ),
    RawMaterialLayerSpec(
        id='geology-geomillion',
        name_en='Geomillion geological map',
        name_ar='الخريطة الجيولوجية (Geomillion)',
        default_visible=False,
        sort_order=50,
        geometry_type='polygon',
    ),
    RawMaterialLayerSpec(
        id='geology-faults',
        name_en='Geological faults',
        name_ar='الفوالق الجيولوجية',
        default_visible=False,
        sort_order=140,
        geometry_type='line',
    ),
    RawMaterialLayerSpec(
        id='geology-extinct-volcanoes',
        name_en='Extinct volcanoes',
        name_ar='البراكين الخامدة',
        default_visible=False,
        sort_order=150,
        geometry_type='point',
    ),
)

RAW_MATERIAL_LAYER_BY_ID = {layer.id: layer for layer in RAW_MATERIAL_LAYER_SPECS}


def _clean(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


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
