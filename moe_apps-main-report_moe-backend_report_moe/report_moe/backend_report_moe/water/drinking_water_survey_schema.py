from __future__ import annotations

from typing import Any

# Portal export/import columns (editable TEI survey fields + identity reference).
SURVEY_PORTAL_COLUMNS: list[tuple[str, str, str]] = [
    ('tei_id', 'TEI Id', 'معرف TEI'),
    ('station_code', 'Station Code', 'رمز المحطة'),
    ('name', 'Name', 'اسم المحطة'),
    ('governorate', 'Governorate', 'المحافظة'),
    ('enrollment_date', 'Enrollment Date', 'تاريخ التسجيل'),
    ('org_unit', 'Org Unit', 'الوحدة التنظيمية'),
    ('building_condition', 'Building Condition (1/2/3)', 'حالة المبنى (1/2/3)'),
    ('is_operational', 'Is Operational (yes/no)', 'تعمل؟ (yes/no)'),
    ('non_operational_reason', 'Non Operational Reason', 'سبب عدم التشغيل'),
    ('previously_rehabilitated', 'Previously Rehabilitated (yes/no)', 'تأهيل سابق (yes/no)'),
    ('rehabilitation_type', 'Rehabilitation Type (partial/complete)', 'نوع التأهيل'),
    ('has_water_hammer_protection', 'Water Hammer Protection (yes/no)', 'حماية الضربة المائية'),
    ('water_hammer_efficiency', 'Water Hammer Efficiency (1/2/3)', 'كفاءة حماية الضربة المائية'),
    ('needs_solar_installation', 'Needs Solar Installation (yes/no)', 'تحتاج تركيب طاقة شمسية'),
    ('solar_space_available', 'Solar Space Available (yes/no)', 'مساحة متاحة للطاقة الشمسية'),
    ('safety_procedures', 'Safety Procedures (no/partially/yes)', 'إجراءات السلامة'),
    ('has_water_tanks', 'Water Tanks Available (yes/no)', 'خزانات المياه'),
    ('has_public_grid_supply', 'Public Grid Supply (yes/no)', 'إمداد الشبكة العامة'),
    ('grid_connection_working', 'Grid Connection Working (yes/no)', 'اتصال الشبكة يعمل'),
    ('electrical_connection_efficiency', 'Electrical Connection Efficiency (1/2/3)', 'كفاءة التوصيل الكهربائي'),
    ('transformer_efficiency', 'Transformer Efficiency (1/2/3)', 'كفاءة المحول'),
    ('electrical_panel_efficiency', 'Electrical Panel Efficiency (1/2/3)', 'كفاءة اللوحة الكهربائية'),
    ('grid_power_productivity', 'Grid Power Productivity (%)', 'إنتاجية الشبكة (%)'),
    ('solar_power_available', 'Solar Power Available (yes/no)', 'طاقة شمسية متوفرة'),
    ('solar_power_productivity', 'Solar Power Productivity (%)', 'إنتاجية الطاقة الشمسية (%)'),
    ('solar_system_efficiency', 'Solar System Efficiency (1/2/3)', 'كفاءة النظام الشمسي'),
    ('generator_available', 'Generator Available (yes/no)', 'مولد متوفر'),
    ('alternative_power_source', 'Alternative Power Source (yes/no)', 'مصدر طاقة بديل'),
    ('is_well_station', 'Well Station (yes/no)', 'محطة آبار'),
    ('is_filtration_station', 'Filtration Station (yes/no)', 'محطة ترشيح'),
    ('is_boosting_station', 'Boosting Station (yes/no)', 'محطة رفع'),
    ('is_water_analyzed', 'Water Analyzed (yes/no)', 'تحليل المياه'),
    ('lab_equipment_status', 'Lab Equipment (no/partially/yes)', 'معدات المختبر'),
]

SURVEY_UPDATE_FIELDS = tuple(
    key for key, _, _ in SURVEY_PORTAL_COLUMNS if key not in {'tei_id', 'station_code', 'name', 'governorate'}
)

PORTAL_HEADER_ALIASES: dict[str, str] = {}
for key, header_en, header_ar in SURVEY_PORTAL_COLUMNS:
    PORTAL_HEADER_ALIASES[header_en.lower()] = key
    PORTAL_HEADER_ALIASES[header_ar.lower()] = key
    PORTAL_HEADER_ALIASES[key] = key

NON_OPERATIONAL_REASON_EXPORT: dict[str, str] = {
    'other': 'Other reasons',
    'theft_vandalism': 'Due to theft and vandalism',
    'completely_destroyed': 'Completely destroyed',
    'emergency_maintenance': 'Requires emergency maintenance',
    'administrative': 'Administrative reasons',
    'routine_maintenance': 'Requires routine maintenance',
    'ongoing_maintenance': 'Ongoing maintenance',
}

PRODUCTIVITY_EXPORT: dict[str, str] = {
    '0': '0',
    '1_25': '1-25',
    '26_50': '26-50',
    '51_75': '51-75',
    '76_99': '76-99',
    '100': '100',
}


def portal_header_row() -> list[str]:
    return [header_en for _, header_en, _ in SURVEY_PORTAL_COLUMNS]


def is_portal_survey_header(row: tuple[Any, ...]) -> bool:
    normalized = {_normalize_header(cell) for cell in row if _normalize_header(cell)}
    if 'tei id' in normalized or 'معرف tei' in normalized:
        return 'station code' in normalized or 'رمز المحطة' in normalized or 'name' in normalized
    return False


def build_portal_column_map(header_row: tuple[Any, ...]) -> dict[str, int]:
    column_map: dict[str, int] = {}
    for index, cell in enumerate(header_row):
        key = PORTAL_HEADER_ALIASES.get(_normalize_header(cell))
        if key:
            column_map[key] = index
    return column_map


def _normalize_header(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip().lower()
