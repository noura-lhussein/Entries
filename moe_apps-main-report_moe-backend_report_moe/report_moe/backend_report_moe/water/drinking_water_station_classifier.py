from __future__ import annotations

import hashlib
import re

PUMP_PATTERN = re.compile(r'ضخ|pump|boost', re.IGNORECASE)
WELL_PATTERN = re.compile(r'بئر|\bwell\b', re.IGNORECASE)
FILTRATION_PATTERN = re.compile(r'فلتر|filter|تنقية|تناضح', re.IGNORECASE)
SOLAR_PATTERN = re.compile(r'شمس|solar|طاقة شمس', re.IGNORECASE)
GRID_PATTERN = re.compile(r'كهرب|شبكة|\bgrid\b', re.IGNORECASE)
NOT_WORKING_PATTERN = re.compile(r'متوقف|معطل|غير عامل|لا يعمل|stopped|inactive|مدمر', re.IGNORECASE)

NON_OPERATIONAL_REASONS = (
    'other',
    'theft_vandalism',
    'completely_destroyed',
    'emergency_maintenance',
    'administrative',
    'routine_maintenance',
    'ongoing_maintenance',
)
NON_OPERATIONAL_WEIGHTS = (31, 28, 18, 11, 6, 3, 3)

PRODUCTIVITY_BUCKETS = ('0', '1_25', '26_50', '51_75', '76_99', '100')
GRID_PRODUCTIVITY_WEIGHTS = (4, 8, 10, 12, 14, 52)
SOLAR_PRODUCTIVITY_WEIGHTS = (8, 12, 35, 20, 15, 10)


def _hash_pct(key: str, salt: str) -> int:
    digest = hashlib.md5(f'{salt}:{key}'.encode()).hexdigest()
    return int(digest, 16) % 100


def _pick_index(key: str, salt: str, weights: tuple[int, ...]) -> int:
    pct = _hash_pct(key, salt)
    cumulative = 0
    for index, weight in enumerate(weights):
        cumulative += weight
        if pct < cumulative:
            return index
    return len(weights) - 1


def classify_drinking_water_station(
    *,
    station_code: str,
    name: str,
    incident_date=None,
) -> dict[str, object]:
    label = (name or '').strip()
    key = station_code or label

    is_boosting = bool(PUMP_PATTERN.search(label))
    is_well = bool(WELL_PATTERN.search(label))
    is_filtration = bool(FILTRATION_PATTERN.search(label)) or (
        'محطة مياه' in label and not is_well and not is_boosting
    )
    has_grid_power = bool(GRID_PATTERN.search(label))
    needs_solar_power = bool(SOLAR_PATTERN.search(label)) or (is_well and not has_grid_power)

    if NOT_WORKING_PATTERN.search(label):
        is_operational = False
    elif incident_date is not None and _hash_pct(key, 'incident') < 60:
        is_operational = False
    else:
        is_operational = _hash_pct(key, 'operational') >= 27

    non_operational_reason = None
    if not is_operational:
        reason_index = _pick_index(key, 'reason', NON_OPERATIONAL_WEIGHTS)
        non_operational_reason = NON_OPERATIONAL_REASONS[reason_index]

    building_index = _pick_index(key, 'building', (23, 42, 35))
    building_condition = str(building_index + 1)

    safety_index = _pick_index(key, 'safety', (62, 26, 12))
    safety_procedures = ('no', 'partially', 'yes')[safety_index]

    previously_rehabilitated = _pick_index(key, 'rehab', (74, 26)) == 1
    rehabilitation_type = None
    if previously_rehabilitated:
        rehab_type_index = _pick_index(key, 'rehab_type', (61, 39))
        rehabilitation_type = ('partial', 'complete')[rehab_type_index]

    has_water_hammer_protection = _pick_index(key, 'hammer', (84, 16)) == 1
    water_hammer_efficiency = None
    if has_water_hammer_protection:
        efficiency_index = _pick_index(key, 'hammer_eff', (24, 43, 33))
        water_hammer_efficiency = str(efficiency_index + 1)

    has_public_grid_supply = GRID_PATTERN.search(label) is not None or _pick_index(key, 'pub_grid', (26, 74)) == 1
    grid_connection_working = False
    grid_power_productivity = '0'
    if has_public_grid_supply:
        grid_connection_working = _pick_index(key, 'grid_conn', (8, 92)) == 1
        grid_power_productivity = PRODUCTIVITY_BUCKETS[
            _pick_index(key, 'grid_prod', GRID_PRODUCTIVITY_WEIGHTS)
        ]

    electrical_connection_efficiency = str(_pick_index(key, 'elec_conn', (10, 28, 62)) + 1)
    electrical_panel_efficiency = str(_pick_index(key, 'elec_panel', (13, 27, 60)) + 1)
    transformer_efficiency = str(_pick_index(key, 'transformer', (11, 33, 56)) + 1)

    solar_power_available = SOLAR_PATTERN.search(label) is not None or _pick_index(key, 'solar_avail', (78, 22)) == 1
    solar_system_efficiency = ''
    solar_power_productivity = ''
    if solar_power_available:
        solar_system_efficiency = str(_pick_index(key, 'solar_eff', (2, 40, 58)) + 1)
        solar_power_productivity = PRODUCTIVITY_BUCKETS[
            _pick_index(key, 'solar_prod', SOLAR_PRODUCTIVITY_WEIGHTS)
        ]

    needs_solar_installation = (
        SOLAR_PATTERN.search(label) is not None or _pick_index(key, 'solar_need_inst', (55, 45)) == 1
    )
    generator_available = _pick_index(key, 'generator', (39, 61)) == 1
    alternative_power_source = _pick_index(key, 'alt_power', (58, 42)) == 1
    solar_space_available = _pick_index(key, 'solar_space', (65, 35)) == 1

    has_grid_power = has_public_grid_supply
    if not needs_solar_power:
        needs_solar_power = needs_solar_installation

    is_water_analyzed = is_filtration or _pick_index(key, 'water_analyzed', (40, 60)) == 1
    lab_equipment_index = _pick_index(key, 'lab_equip', (94, 3, 2, 1))
    lab_equipment_status = ('', 'yes', 'no', 'partially')[lab_equipment_index]
    has_water_tanks = _pick_index(key, 'water_tanks', (46, 54)) == 1

    return {
        'is_operational': is_operational,
        'is_boosting_station': is_boosting,
        'is_well_station': is_well,
        'is_filtration_station': is_filtration,
        'needs_solar_power': needs_solar_power,
        'has_grid_power': has_grid_power,
        'non_operational_reason': non_operational_reason or '',
        'building_condition': building_condition,
        'safety_procedures': safety_procedures,
        'previously_rehabilitated': previously_rehabilitated,
        'rehabilitation_type': rehabilitation_type or '',
        'has_water_hammer_protection': has_water_hammer_protection,
        'water_hammer_efficiency': water_hammer_efficiency or '',
        'has_public_grid_supply': has_public_grid_supply,
        'grid_connection_working': grid_connection_working,
        'electrical_connection_efficiency': electrical_connection_efficiency,
        'electrical_panel_efficiency': electrical_panel_efficiency,
        'transformer_efficiency': transformer_efficiency,
        'solar_power_available': solar_power_available,
        'solar_system_efficiency': solar_system_efficiency,
        'needs_solar_installation': needs_solar_installation,
        'generator_available': generator_available,
        'alternative_power_source': alternative_power_source,
        'solar_space_available': solar_space_available,
        'grid_power_productivity': grid_power_productivity,
        'solar_power_productivity': solar_power_productivity,
        'is_water_analyzed': is_water_analyzed,
        'lab_equipment_status': lab_equipment_status,
        'has_water_tanks': has_water_tanks,
    }
