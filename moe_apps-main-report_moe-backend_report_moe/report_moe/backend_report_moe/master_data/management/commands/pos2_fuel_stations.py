from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from master_data.models import OilFacility as Facility

DEFAULT_POS2_FACILITY_CSV = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'moeds' / 'moe-backend' / 'oil_gas' / 'data' / 'pos2' / 'facility_202605010032.csv'
)

FUEL_STATION_CSV_TYPES = frozenset({'Petrol Station', 'Gas Station'})

GOVERNORATE_AR_TO_EN: dict[str, str] = {
    'دمشق': 'Damascus',
    'ريف دمشق': 'Rif Dimashq',
    'حلب': 'Aleppo',
    'حمص': 'Homs',
    'حماه': 'Hama',
    'حماة': 'Hama',
    'اللاذقية': 'Latakia',
    'طرطوس': 'Tartus',
    'ادلب': 'Idlib',
    'إدلب': 'Idlib',
    'درعا': 'Daraa',
    'السويداء': 'As-Suwayda',
    'دير الزور': 'Deir ez-Zor',
    'الرقة': 'Raqqa',
    'الحسكة': 'Al-Hasakah',
    'القنيطرة': 'Quneitra',
}

SYRIA_LAT_RANGE = (32.0, 37.5)
SYRIA_LNG_RANGE = (35.5, 42.5)


@dataclass(frozen=True)
class Pos2FuelStationRow:
    pos2_id: int
    code: str
    name_ar: str
    name_en: str
    location: str
    governorate: str
    latitude: Decimal | None
    longitude: Decimal | None
    status: str
    station_type: str


def _location_text(address: str = '', station_type: str = '') -> str:
    parts = [p.strip() for p in [station_type, address] if p.strip()]
    return ', '.join(parts) or '—'


def _governorate_from_name(name: str) -> str:
    for ar, en in GOVERNORATE_AR_TO_EN.items():
        if ar in name:
            return en
    return 'Unknown'


def _parse_decimal(value: str | None, min_v: float = -180.0, max_v: float = 180.0) -> Decimal | None:
    if not value or not (val := value.strip()):
        return None
    try:
        dec = Decimal(val)
        if min_v <= dec <= max_v:
            return dec
    except InvalidOperation:
        pass
    return None


def _in_syria(lat: Decimal | None, lng: Decimal | None) -> bool:
    if lat is None or lng is None:
        return False
    return SYRIA_LAT_RANGE[0] <= lat <= SYRIA_LAT_RANGE[1] and SYRIA_LNG_RANGE[0] <= lng <= SYRIA_LNG_RANGE[1]


def parse_pos2_fuel_station_row(row: dict) -> Pos2FuelStationRow | None:
    pos2_id = row.get('id', '').strip()
    station_type = row.get('type', '').strip()

    if not pos2_id or not station_type:
        return None
    if station_type not in FUEL_STATION_CSV_TYPES:
        return None

    try:
        pos2_id = int(pos2_id)
    except ValueError:
        return None

    name_ar = (row.get('name_ar') or '').strip()
    name_en = (row.get('name_en') or '').strip()

    if not name_ar and not name_en:
        return None

    latitude = _parse_decimal(row.get('latitude'), *SYRIA_LAT_RANGE)
    longitude = _parse_decimal(row.get('longitude'), *SYRIA_LNG_RANGE)

    if latitude is None or longitude is None or not _in_syria(latitude, longitude):
        return None

    is_active = (row.get('is_active') or '').strip() == '1'
    status = Facility.Status.ACTIVE if is_active else Facility.Status.INACTIVE

    return Pos2FuelStationRow(
        pos2_id=pos2_id,
        code=f'pos2-{pos2_id}',
        name_ar=name_ar or name_en,
        name_en=name_en or name_ar,
        location=_location_text(address=row.get('address') or '', station_type=station_type),
        governorate=_governorate_from_name(name_ar or name_en),
        latitude=latitude,
        longitude=longitude,
        status=status,
        station_type=station_type,
    )


def iter_pos2_fuel_stations(csv_path: Path) -> list[Pos2FuelStationRow]:
    if not csv_path.is_file():
        raise FileNotFoundError(f'POS2 facility CSV not found: {csv_path}')

    rows: list[Pos2FuelStationRow] = []
    with csv_path.open(encoding='utf-8', newline='') as handle:
        for raw_row in csv.DictReader(handle):
            parsed = parse_pos2_fuel_station_row(raw_row)
            if parsed is not None:
                rows.append(parsed)
    return rows


def pos2_row_to_facility(row: Pos2FuelStationRow) -> Facility:
    return Facility(
        code=row.code,
        name_en=row.name_en,
        name_ar=row.name_ar,
        facility_type=Facility.FacilityType.FUEL_STATION,
        sector=Facility.Sector.OIL_GAS,
        location=row.location,
        governorate=row.governorate,
        latitude=row.latitude,
        longitude=row.longitude,
        status=row.status,
    )
