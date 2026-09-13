from __future__ import annotations

from dataclasses import dataclass

NATIONAL_FUEL_RESERVE_CAPACITY_TONS = 336_000


@dataclass(frozen=True, slots=True)
class FuelTankStation:
    code: str
    label_en: str
    label_ar: str
    max_capacity_tons: int


@dataclass(frozen=True, slots=True)
class GenerationPlant:
    code: str
    label_en: str
    label_ar: str
    pattern: str


FUEL_TANK_STATIONS: tuple[FuelTankStation, ...] = (
    FuelTankStation('zara', 'Zara', 'الزارة', 72_000),
    FuelTankStation('banias', 'Banias', 'بانياس', 84_000),
    FuelTankStation('tishreen', 'Tishreen', 'تشرين', 48_000),
    FuelTankStation('maharda', 'Maharda', 'محردة', 36_000),
    FuelTankStation('aleppo', 'Aleppo', 'حلب', 56_000),
)

FUEL_TANK_BY_CODE = {station.code: station for station in FUEL_TANK_STATIONS}

GENERATION_PLANTS: tuple[GenerationPlant, ...] = (
    GenerationPlant('deir_ali', 'Deir Ali', 'دير علي', r'دير\s*علي'),
    GenerationPlant('tishreen_steam', 'Tishreen steam', 'تشرين بخاري', r'تشرين\s*بخاري|بخاري\s*تشرين'),
    GenerationPlant('jandar', 'Jandar', 'جندر', r'جندر'),
    GenerationPlant('zara', 'Zara', 'الزارة', r'الزارة|زارة'),
    GenerationPlant('banias', 'Banias', 'بانياس', r'بانياس'),
    GenerationPlant('maharda', 'Maharda', 'محردة', r'محردة|محرده'),
    GenerationPlant('aleppo', 'Aleppo', 'حلب', r'حلب'),
    GenerationPlant('nasser', 'Nasser', 'الناصر', r'الناصر|ناصر'),
    GenerationPlant('sweida', 'Al-Swediya', 'السويدية', r'السويدية|سويدية'),
    GenerationPlant('euphrates_dam', 'Euphrates dam', 'سد الفرات', r'الفرات|كديران'),
    GenerationPlant('tishreen_dam', 'Tishreen dam', 'سد تشرين', r'سد تشرين'),
    GenerationPlant('maintenance', 'Maintenance', 'صيانة', r'صيانة'),
)

GENERATION_PLANT_BY_CODE = {plant.code: plant for plant in GENERATION_PLANTS}
