"""Daily electricity report layout — sheet tabs from the coordination-room master workbook."""
from __future__ import annotations

from dataclasses import dataclass

SHEET_REPORT_INFO = 'معلومات التقرير'
SHEET_GENERATION_STATUS = 'وضع مجموعات التوليد'
SHEET_FUEL_MOVEMENT = 'حركة الفيول'
SHEET_FUEL_TANKS = 'معلومات خزانات الوقود'
SHEET_GENERATION_UNITS = 'انتاج و استهلاك الوقود لمجموعات'
SHEET_HYDRO = 'معلومات السدود'
SHEET_GENERATION_REPORT = 'تقرير التوليد'
SHEET_MAINTENANCE = 'المجموعات تحت أعمال الصيانة'
SHEET_GRID_INCIDENTS = 'مجموعات التوليد'
SHEET_GENERATION_INCIDENTS = 'الخطوط'

# Legacy sheet tab names from older master workbooks.
LEGACY_SHEET_GRID_INCIDENTS = 'حوادث الشبكة الكهربائية_حوادث ا'
LEGACY_SHEET_GENERATION_INCIDENTS = 'حوادث الشبكة الكهربائية_حوادث م'

REPORT_SHEET_ORDER: tuple[str, ...] = (
    SHEET_REPORT_INFO,
    SHEET_GENERATION_STATUS,
    SHEET_FUEL_MOVEMENT,
    SHEET_FUEL_TANKS,
    SHEET_GENERATION_UNITS,
    SHEET_HYDRO,
    SHEET_GENERATION_REPORT,
    SHEET_MAINTENANCE,
    SHEET_GENERATION_INCIDENTS,
    SHEET_GRID_INCIDENTS,
)

# Master workbook export order (matches report_01-05-2026.xlsx).
EXPORT_SHEET_ORDER: tuple[str, ...] = (
    SHEET_REPORT_INFO,
    SHEET_GENERATION_STATUS,
    SHEET_FUEL_MOVEMENT,
    SHEET_FUEL_TANKS,
    SHEET_GENERATION_UNITS,
    SHEET_HYDRO,
    SHEET_GENERATION_REPORT,
    SHEET_MAINTENANCE,
    LEGACY_SHEET_GRID_INCIDENTS,
    LEGACY_SHEET_GENERATION_INCIDENTS,
)

# Exact row labels from the coordination-room master template (column A).
GENERATION_STATUS_EXPORT_ROWS: tuple[tuple[str, str], ...] = (
    ('nominal_capacity_mwh', 'مجموع الاستطاعة الاسمية المتاحه لمجموعات التوليد  (م.و.س)'),
    ('total_generation_mwh_24h', 'المجموع الكلي لانتاج المجموعات خلال 24 ساعة (م.و.س)'),
    ('gas_generation_mwh_24h', 'مجموع التوليد الغازي (م.و.س)'),
    ('steam_fuel_demand_tpd', 'مجموع التوليد البخاري على الفيول  (م.و.س)'),
    ('gas_demand_mm3d', 'الطلب على الغاز (مليون م٣ / يوم )'),
    ('total_fuel_demand_tpd', 'الطلب الكلي على الفيول (طن / يوم)'),
    ('gas_consumed_mm3d', 'الكمية المستهلكة اليومية من الغاز (مليون م٣ / يوم ) '),
    ('fuel_oil_consumed_tpd', 'الكمية المستهلكة من الفيول (طن)'),
    ('hydro_dams_capacity_mw',
     'الاستطاعة المتاحة  للسدود المائية (الفرات و تشرين) (م.و)'),
    ('solar_capacity_mw', 'الاستطاعة المتاحة للعنافات الشمسية  (م.و) '),
    ('wind_capacity_mw', 'الاستطاعة المتاحة للعنافات الريحية  (م.و) '),
)

FUEL_MOVEMENT_EXPORT_ROWS: tuple[tuple[str, str], ...] = (
    ('fuel_oil_received_tpd', 'الفيول الوارد (طن)'),
    ('fuel_flow_consumed_tpd', 'الفيول المستهلك (طن)'),
    ('fuel_oil_balance_tpd', 'وفر الفيول (طن)'),
)

GENERATION_REPORT_EXPORT_ROWS: tuple[tuple[str, str], ...] = (
    ('available_generated_power', 'الاستطاعة المتاحة المولدة مع الشمسي\u00a0(م.و)'),
    ('self_use_losses_mw', 'استهلاك ذاتي و ضياع\u00a0(م.و)'),
    ('net_generation_mwh', 'التوليد الصافي\u00a0(م.و)'),
    ('industrial_self_use_mw', 'استهلاك صناعي\u00a0(م.و)'),
    ('generation_without_industrial_mw', 'الاستطاعة المولدة بدون صناعي\u00a0(م.و)'),
    ('hydro_output_mw', 'السدود (م.و)'),
    ('rotary_reserve_mw', 'احتياط دوار\u00a0(م.و)'),
    ('gov_consumed_mw', 'الاستطاعة المستهلكة\u00a0(م.و)'),
    ('gas_groups_mw', ' استطاعة المجموعات الغازية (م.و)'),
    ('steam_groups_mw', 'استطاعة المجموعات البخارية (م.و)'),
    ('gas_import_mm3d', 'الغاز الوارد (مليون م3)'),
    ('fuel_reserve_tons', 'المخزون الاحتياطي من الفيول\u00a0(طن)'),
)

GENERATION_UNIT_EXPORT_ROWS: tuple[tuple[str, str], ...] = (
    ('عنفات السويدية', 'sweida'),
    ('عنفات سد الفرات و كديران', 'euphrates_dam'),
    ('عنفات سد تشرين', 'tishreen_dam'),
    ('استجرار محطات الضخ بحلب', 'aleppo'),
    ('محولة 66/20 سد تشرين', 'tishreen_transformer'),
)

GOVERNORATE_EXPORT_ORDER: tuple[str, ...] = (
    'damascus',
    'rif_damascus',
    'sweida',
    'daraa',
    'quneitra',
    'homs',
    'hama',
    'tartous',
    'latakia',
    'aleppo',
    'deir_ez_zor',
    'raqqa',
    'hasakah',
)

HYDRO_EXPORT_DAMS: tuple[tuple[str, str], ...] = (
    ('سد الفرات', 'euphrates'),
    ('سد تشرين', 'tishreen'),
)

# Map DailyMetric keys to pdf_extract row dict keys.
METRIC_TO_EXTRACT_KEY: dict[str, str] = {
    'peak_generation_mw': 'peak_mw',
    'net_generation_mwh': 'net_mwh_24h',
    'fuel_oil_received_tpd': 'fuel_oil_received_t',
    'fuel_oil_consumed_tpd': 'generation_status_fuel_oil_consumed_t',
    'fuel_oil_balance_tpd': 'fuel_oil_balance_t',
    'fuel_reserve_tons': 'fuel_reserve_t',
    'industrial_self_use_mw': 'industrial_mw',
    'steam_generation_mwh': 'steam_mwh',
}


def national_scalar_metrics(row: dict) -> dict[str, float | None]:
    """extract_xlsx / import row → {electricity.national Attribute.key: value}.

    Single source of truth for national scalar metrics written to DailyMetric and
    Form Builder Info. Attribute keys come from the DB seed; this only bridges
    extract field names that differ from those keys.
    """
    return {
        'peak_generation_mw': row.get('peak_mw'),
        'net_generation_mwh': row.get('net_mwh_24h'),
        'available_fuel_quantity': row.get('available_fuel_quantity'),
        'grid_frequency_hz': row.get('grid_frequency_hz'),
        'fuel_reserve_tons': row.get('fuel_reserve_t'),
        'fuel_tank_stock_tons': row.get('fuel_tank_stock_tons'),
        'fuel_tank_max_capacity_tons': row.get('fuel_tank_max_capacity_tons'),
        'fuel_reserve_pct': row.get('fuel_reserve_pct'),
        'fuel_oil_received_tpd': row.get('fuel_oil_received_t'),
        'fuel_flow_consumed_tpd': row.get('fuel_flow_consumed_tpd'),
        'fuel_oil_consumed_tpd': (
            row.get('generation_status_fuel_oil_consumed_t')
            or row.get('fuel_oil_consumed_t')
        ),
        'fuel_oil_balance_tpd': row.get('fuel_oil_balance_t'),
        'gas_import_mm3d': row.get('gas_import_mm3d'),
        'gas_consumed_mm3d': row.get('gas_consumed_mm3d'),
        'gas_demand_mm3d': row.get('gas_demand_mm3d'),
        'available_generated_power': row.get('available_generated_power'),
        'steam_generation_mwh': row.get('steam_mwh'),
        'steam_fuel_demand_tpd': row.get('steam_fuel_demand_tpd'),
        'gas_groups_mw': row.get('gas_groups_mw'),
        'steam_groups_mw': row.get('steam_groups_mw'),
        'industrial_self_use_mw': row.get('industrial_mw'),
        'self_use_losses_mw': row.get('self_use_losses_mw'),
        'generation_without_industrial_mw': row.get('generation_without_industrial_mw'),
        'hydro_output_mw': row.get('hydro_output_mw'),
        'rotary_reserve_mw': row.get('rotary_reserve_mw'),
        'hydro_dams_capacity_mw': row.get('hydro_dams_capacity_mw'),
        'nominal_capacity_mwh': row.get('nominal_capacity_mwh'),
        'total_generation_mwh_24h': row.get('total_generation_mwh_24h'),
        'gas_generation_mwh_24h': row.get('gas_generation_mwh_24h'),
        'total_fuel_demand_tpd': row.get('total_fuel_demand_tpd'),
        'gov_consumed_mw': row.get('gov_consumed_mw'),
        'gov_allocated_mw': row.get('gov_allocated_mw'),
        'gov_excess_mw': row.get('gov_excess_mw'),
        'solar_capacity_mw': row.get('solar_capacity_mw'),
        'wind_capacity_mw': row.get('wind_capacity_mw'),
        'generation_incidents_count': row.get('generation_incidents_count'),
        'grid_incidents_count': row.get('grid_incidents_count'),
    }


@dataclass(frozen=True, slots=True)
class ReportSectionSpec:
    id: str
    sheet_name: str
    label_en: str


REPORT_SECTIONS: tuple[ReportSectionSpec, ...] = (
    ReportSectionSpec('report_info', SHEET_REPORT_INFO, 'Report information'),
    ReportSectionSpec('generation_status',
                      SHEET_GENERATION_STATUS, 'Generation groups status'),
    ReportSectionSpec('fuel_movement', SHEET_FUEL_MOVEMENT,
                      'Fuel oil movement'),
    ReportSectionSpec('fuel_tanks', SHEET_FUEL_TANKS, 'Fuel tank information'),
    ReportSectionSpec('generation_units', SHEET_GENERATION_UNITS,
                      'Group production & fuel use'),
    ReportSectionSpec('hydro', SHEET_HYDRO, 'Dam information'),
    ReportSectionSpec('generation_report',
                      SHEET_GENERATION_REPORT, 'Generation report'),
    ReportSectionSpec('maintenance', SHEET_MAINTENANCE,
                      'Groups under maintenance'),
    ReportSectionSpec('generation_incidents',
                      SHEET_GENERATION_INCIDENTS, 'Generation incidents'),
    ReportSectionSpec('grid_incidents', SHEET_GRID_INCIDENTS,
                      'Grid line incidents'),
)

SECTION_BY_ID = {section.id: section for section in REPORT_SECTIONS}

GENERATION_STATUS_METRICS: tuple[str, ...] = tuple(
    key for key, _ in GENERATION_STATUS_EXPORT_ROWS
)

FUEL_MOVEMENT_METRICS: tuple[str, ...] = (
    'fuel_oil_received_tpd',
    'fuel_flow_consumed_tpd',
    'fuel_oil_balance_tpd',
)

FUEL_TANKS_METRICS: tuple[str, ...] = (
    'fuel_tank_max_capacity_tons',
    'fuel_reserve_tons',
    'grid_frequency_hz',
    'fuel_tank_stock_tons',
)

GENERATION_REPORT_METRICS: tuple[str, ...] = (
    'available_generated_power',
    'self_use_losses_mw',
    'net_generation_mwh',
    'industrial_self_use_mw',
    'generation_without_industrial_mw',
    'hydro_output_mw',
    'rotary_reserve_mw',
    'gov_consumed_mw',
    'gas_groups_mw',
    'steam_groups_mw',
    'gas_import_mm3d',
    'fuel_reserve_tons',
)

GOVERNORATE_AR_TO_CODE: dict[str, str] = {
    'دمشق': 'damascus',
    'ريف دمشق': 'rif_damascus',
    'السويداء': 'sweida',
    'درعا': 'daraa',
    'القنيطرة': 'quneitra',
    'حمص': 'homs',
    'حماه': 'hama',
    'طرطوس': 'tartous',
    'اللاذقية': 'latakia',
    'حلب': 'aleppo',
    'دير الزور': 'deir_ez_zor',
    'الرقة': 'raqqa',
    'الحسكة': 'hasakah',
    'المجموع': 'national_total',
}

CODE_TO_GOVERNORATE_AR: dict[str, str] = {
    code: label for label, code in GOVERNORATE_AR_TO_CODE.items() if code != 'national_total'
}

GENERATION_GROUP_AR_TO_PLANT: tuple[tuple[str, str], ...] = (
    (r'السويدية', 'sweida'),
    (r'الفرات|كديران', 'euphrates_dam'),
    (r'سد تشرين', 'tishreen_dam'),
    (r'الضخ بحلب|استجرار', 'aleppo'),
    (r'محولة', 'tishreen_dam'),
)

HYDRO_DAM_AR_TO_CODE: dict[str, str] = {
    'سد الفرات': 'euphrates',
    'سد تشرين': 'tishreen',
    'الثورة': 'thawra',
}
