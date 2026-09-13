from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import shapefile
from map_layers.shapefile_utils import _shapefile_has_dbf


class ImportMode(str, Enum):
    FEATURES = 'features'
    POINT_SERIES_LINE = 'point_series_line'
    SPLIT_BY_VOLTAGE = 'split_by_voltage'


@dataclass(frozen=True, slots=True)
class GisImportSource:
    layer_id: str
    shp_path: Path
    mode: ImportMode = ImportMode.FEATURES


# English / legacy 400 kV segment stems (point series → LineString).
_400KV_SEGMENT_STEMS = frozenset({
    'adra_der_2',
    'alnasrya_adra',
    'alteem_araq',
    'dier_ali_adra_2__2',
    'dirali_demas_1',
    'jandar-tadamar',
    'jandar_tadamar',
    'jander-adra',
    'jander_dimas',
    'jander-dimas',
    '400_kv_voltage_line_aleppo___f_subst._to_turkish_border.',
    'aleppo___f_hama2',
    'aleppo_f_hama2',
    'deir_ali_-_north_ammant',
    'hama-zaizoun_',
    'jander-hama2',
    'jander-hama2_2',
    'team-tadmou',
    'team__hasakeh',
    'zezoun-latakia_',
    'aleppo_f-zerba_zezoun__',
    'demas_alnasrya',
    'dier_ali_demas_',
    'dier_ali_demas',
    'dimas_lebanon',
})


def _normalize_stem(path: Path) -> str:
    return path.stem.lstrip("'").strip().lower()


def _shapefile_geom_kind(shp_path: Path) -> str:
    if not _shapefile_has_dbf(shp_path):
        try:
            reader = shapefile.Reader(str(shp_path))
        except Exception:
            return 'empty'
        if not len(reader):
            return 'empty'
        types = {reader.shape(i).shapeType for i in range(len(reader))}
        point_types = {shapefile.POINT, shapefile.POINTZ, shapefile.POINTM, shapefile.MULTIPOINT}
        line_types = {shapefile.POLYLINE, shapefile.POLYLINEZ, shapefile.POLYLINEM}
        poly_types = {shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM}
        if types <= point_types:
            return 'point'
        if types <= line_types:
            return 'line'
        if types <= poly_types:
            return 'polygon'
        return 'mixed'

    for encoding in ('utf-8', 'cp1256', 'latin-1'):
        try:
            reader = shapefile.Reader(str(shp_path), encoding=encoding)
            break
        except UnicodeDecodeError:
            reader = None
    if reader is None:
        reader = shapefile.Reader(str(shp_path), encoding='utf-8', encodingErrors='replace')
    if not len(reader):
        return 'empty'
    point_types = {shapefile.POINT, shapefile.POINTZ, shapefile.POINTM, shapefile.MULTIPOINT}
    line_types = {shapefile.POLYLINE, shapefile.POLYLINEZ, shapefile.POLYLINEM}
    poly_types = {shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM}
    types = {reader.shape(i).shapeType for i in range(len(reader))}
    if types <= point_types:
        return 'point'
    if types <= line_types:
        return 'line'
    if types <= poly_types:
        return 'polygon'
    return 'mixed'


def _is_generation_plant(name: str) -> bool:
    return 'توليد' in name


def _is_renewable(name: str) -> bool:
    return 'متجددة' in name or 'renewable' in name.lower()


def _is_66kv_line_name(name: str) -> bool:
    low = name.lower()
    return (
        'all 66' in low
        or '66 k v' in low
        or '66k' in low
        or 'خطوط 66' in name
        or low.startswith('خطي ')
        or 'خطي ' in name
    )


def _is_230kv_line_name(name: str) -> bool:
    return (
        '230' in name
        or 'all230' in name.lower()
        or name.endswith('230.shp')
    )


def _is_400kv_line_polyline(name: str) -> bool:
    low = name.lower()
    return low == 'line_400' or ('400' in low and 'substation' not in low and _shapefile_geom_kind(Path(name)) == 'line')


def _is_400kv_segment(stem: str) -> bool:
    if stem in _400KV_SEGMENT_STEMS:
        return True
    if stem.startswith("'"):
        return True
    low = stem.lower()
    return any(
        token in low
        for token in (
            'adra',
            'demas',
            'jander',
            'jandar',
            'aleppo',
            'dier_ali',
            'dirali',
            'team',
            'hama',
            'zezoun',
            'zezoun',
            'deir_ali',
            'dimas',
            'nasrya',
            'tadmou',
            'araq',
            'ammant',
            'latakia',
            'border',
            'hasakeh',
        )
    ) and '230' not in stem and 'خط' not in stem


def _is_substation_file(name: str) -> bool:
    low = name.lower()
    return (
        'substation' in low
        or low.startswith('substations')
        or low == 'ss400-230.shp'
    )


def discover_gis_sources(source_dir: Path) -> list[GisImportSource]:
    """Classify loose shapefiles in a flat directory for electricity GIS import."""
    if not source_dir.is_dir():
        raise FileNotFoundError(f'GIS source directory not found: {source_dir}')

    sources: list[GisImportSource] = []
    assigned: set[str] = set()

    def add(layer_id: str, shp: Path, mode: ImportMode = ImportMode.FEATURES) -> None:
        key = shp.name
        if key in assigned:
            return
        if _shapefile_geom_kind(shp) == 'empty':
            return
        if mode == ImportMode.FEATURES and not _shapefile_has_dbf(shp):
            return
        assigned.add(key)
        sources.append(GisImportSource(layer_id=layer_id, shp_path=shp, mode=mode))

    shp_files = sorted(source_dir.glob('*.shp'), key=lambda p: p.name)

    for shp in shp_files:
        name = shp.name
        stem = _normalize_stem(shp)
        geom = _shapefile_geom_kind(shp)

        if _is_renewable(name):
            add('power-gis-renewable-sites', shp)
            continue

        if _is_generation_plant(name):
            continue

        if name == 'ss400-230.shp':
            add('power-gis-substations-230', shp, ImportMode.SPLIT_BY_VOLTAGE)
            continue

        if _is_substation_file(name):
            low = name.lower()
            if '66' in low or '66t' in low:
                add('power-gis-substations-66', shp)
            elif '400' in low:
                add('power-gis-substations-400', shp)
            elif '230' in low or low == 'substations.shp':
                add('power-gis-substations-230', shp)
            continue

        if geom == 'line' and _is_66kv_line_name(name):
            add('power-gis-lines-66', shp)
            continue

        if geom == 'line' and ('all230' in stem or (stem == 'all230 k v')):
            add('power-gis-lines-230', shp)
            continue

        if geom == 'line' and stem == 'line_400':
            add('power-gis-lines-400', shp)
            continue

        if geom == 'point' and _is_230kv_line_name(name):
            add('power-gis-lines-230', shp, ImportMode.POINT_SERIES_LINE)
            continue

        if geom == 'point' and _is_400kv_segment(stem):
            add('power-gis-lines-400', shp, ImportMode.POINT_SERIES_LINE)
            continue

    # Remaining point series without explicit voltage → 230 kV network segments.
    for shp in shp_files:
        if shp.name in assigned:
            continue
        if _is_generation_plant(shp.name):
            continue
        if _shapefile_geom_kind(shp) != 'point':
            continue
        add('power-gis-lines-230', shp, ImportMode.POINT_SERIES_LINE)

    return sources


def layer_ids_from_sources(sources: list[GisImportSource]) -> list[str]:
    order = [
        'power-gis-substations-66',
        'power-gis-substations-230',
        'power-gis-substations-400',
        'power-gis-lines-66',
        'power-gis-lines-230',
        'power-gis-lines-400',
        'power-gis-renewable-sites',
    ]
    present = {source.layer_id for source in sources}
    return [layer_id for layer_id in order if layer_id in present]


def voltage_from_classification(raw: str) -> int | None:
    text = str(raw or '').strip().lower()
    if not text:
        return None
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    if not match:
        return None
    value = int(float(match.group(1)))
    if value in (66, 230, 400):
        return value
    return None
