from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASINS_SHAPEFILE = BACKEND_ROOT / 'temp' / 'basins_map' / 'basins.shp'
BASINS_GEOJSON_PATH = Path(__file__).resolve().parent / 'data' / 'syria_hydro_basins.geojson'


@dataclass(frozen=True, slots=True)
class BasinSpec:
    slug: str
    folder_key: str
    name_en: str
    name_ar: str
    shapefile_name: str


BASIN_SPECS: tuple[BasinSpec, ...] = (
    BasinSpec('badia', 'البادية', 'Badia', 'البادية', 'البادية'),
    BasinSpec('khabur', 'الخابور', 'Tigris & Khabur', 'دجلة والخابور', 'دجلة والخابور'),
    BasinSpec('coastal', 'الساحل', 'Coastal', 'الساحل', 'الساحل'),
    BasinSpec('orontes', 'العاصي', 'Orontes (Assi)', 'العاصي', 'العاصي'),
    BasinSpec('euphrates', 'الفرات', 'Euphrates & Aleppo', 'الفرات وحلب', 'الفرات وحلب'),
    BasinSpec('yarmouk', 'اليرموك', 'Yarmouk', 'اليرموك', 'اليرموك'),
    BasinSpec('barada', 'بردى', 'Barada & Aouaj', 'بردى والأعوج', 'بردى والأعوج'),
)

BASIN_SPEC_BY_SLUG = {spec.slug: spec for spec in BASIN_SPECS}
BASIN_SPEC_BY_SHAPEFILE_NAME = {spec.shapefile_name: spec for spec in BASIN_SPECS}
