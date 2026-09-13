from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricSpec:
    key: str
    label_en: str
    label_ar: str
    unit: str
    category: str
    kpi_order: int | None = None
    kpi_status_rule: str | None = None


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec('peak_generation_mw', 'Peak generation',
               'ذروة التوليد', 'MW', 'generation', 1),
    MetricSpec('net_generation_mwh', 'Net generation',
               'التوليد الصافي', 'MW', 'generation', 2),
    MetricSpec('available_generated_power', 'Available generated power (with solar)',
               'الاستطاعة المتاحة المولدة مع الشمسي', 'MW', 'generation', 3),
    MetricSpec('self_use_losses_mw', 'Self-use & losses',
               'استهلاك ذاتي و ضياع', 'MW', 'generation'),
    MetricSpec('generation_without_industrial_mw', 'Generation without industrial',
               'الاستطاعة المولدة بدون صناعي', 'MW', 'generation'),
    MetricSpec('hydro_output_mw', 'Hydro output (instant)',
               'السدود', 'MW', 'generation'),
    MetricSpec('rotary_reserve_mw', 'Rotary reserve',
               'احتياط دوار', 'MW', 'generation'),
    MetricSpec('gas_groups_mw', 'Gas groups capacity',
               'استطاعة المجموعات الغازية', 'MW', 'generation', 4),
    MetricSpec('steam_groups_mw', 'Steam groups capacity',
               'استطاعة المجموعات البخارية', 'MW', 'generation', 5),
    MetricSpec('hydro_dams_capacity_mw', 'Hydro dams capacity at 9:00',
               'الاستطاعة المتاحة  للسدود المائية (الفرات و تشرين)', 'MW', 'renewable'),
    MetricSpec('solar_capacity_mw', 'Solar capacity at 9:00',
               'الاستطاعة المتاحة للعنافات الشمسية', 'MW', 'renewable'),
    MetricSpec('wind_capacity_mw', 'Wind capacity at 9:00',
               'الاستطاعة المتاحة للعنافات الريحية', 'MW', 'renewable'),
    MetricSpec('nominal_capacity_mwh', 'Nominal available capacity',
               'مجموع الاستطاعة الاسمية المتاحة', 'MWh', 'generation'),
    MetricSpec('total_generation_mwh_24h', 'Total 24h generation',
               'المجموع الكلي لإنتاج المجموعات', 'MWh', 'generation'),
    MetricSpec('gas_generation_mwh_24h', 'Gas generation (24h)',
               'مجموع التوليد الغازي', 'MWh', 'generation'),
    MetricSpec('steam_generation_mwh', 'Steam generation',
               'التوليد البخاري', 'MWh', 'generation'),
    MetricSpec('steam_fuel_demand_tpd', 'Steam fuel demand',
               'مجموع التوليد البخاري على الفيول', 't/d', 'fuel'),
    MetricSpec('available_fuel_quantity', 'Available fuel quantity',
               'كمية الفيول المتاحة', 't', 'fuel'),
    MetricSpec('grid_frequency_hz', 'Grid frequency',
               'التردد', 'Hz', 'grid', 6),
    MetricSpec('fuel_reserve_tons', 'Consumable fuel reserve',
               'المخزون القابل للاستهلاك', 't', 'fuel', 7, 'lower_is_bad'),
    MetricSpec('fuel_tank_stock_tons', 'Total fuel stock',
               'مخزون خزانات الوقود', 't', 'fuel'),
    MetricSpec('fuel_tank_max_capacity_tons', 'Fuel tank max capacity',
               'السعة الأعظمية لخزانات الوقود', 't', 'fuel'),
    MetricSpec('fuel_reserve_pct', 'Fuel reserve fill', 'نسبة المخزون',
               '%', 'fuel', kpi_status_rule='pct_lower_is_bad'),
    MetricSpec('fuel_oil_received_tpd', 'Fuel oil received',
               'الفيول الوارد', 't/d', 'fuel'),
    MetricSpec('fuel_flow_consumed_tpd', 'Fuel flow consumed',
               'حركة الفيول المستهلك', 't/d', 'fuel'),
    MetricSpec('fuel_oil_consumed_tpd', 'Fuel oil consumed',
               'الفيول المستهلك', 't/d', 'fuel'),
    MetricSpec('fuel_oil_balance_tpd', 'Fuel oil balance',
               'وفر الفيول', 't/d', 'fuel', kpi_status_rule='negative_is_bad'),
    MetricSpec('total_fuel_demand_tpd', 'Total fuel demand',
               'الطلب الكلي على الفيول', 't/d', 'fuel'),
    MetricSpec('gas_demand_mm3d', 'Gas demand',
               'الطلب على الغاز', 'M m³/d', 'gas'),
    MetricSpec('gas_consumed_mm3d', 'Gas consumed',
               'الكمية المستهلكة من الغاز', 'M m³/d', 'gas'),
    MetricSpec('gas_import_mm3d', 'Gas import',
               'الغاز الوارد', 'M m³/d', 'gas', 8),
    MetricSpec('industrial_self_use_mw', 'Industrial self-use',
               'استهلاك صناعي', 'MW', 'demand'),
    MetricSpec('gov_consumed_mw', 'Consumed capacity',
               'الاستطاعة المستهلكة', 'MW', 'demand', 9),
    MetricSpec('gov_allocated_mw', 'National load allocated',
               'الكمية المخصصة', 'MW', 'demand'),
    MetricSpec('gov_excess_mw', 'Allocation overrun',
               'التجاوز', 'MW', 'demand', 10, 'higher_is_bad'),
    MetricSpec('generation_incidents_count', 'Generation incidents',
               'حوادث التوليد', 'count', 'incidents', kpi_status_rule='count_is_bad'),
    MetricSpec('grid_incidents_count', 'Grid line incidents',
               'حوادث الخطوط', 'count', 'incidents', 11, 'count_is_bad'),
)

METRIC_BY_KEY = {spec.key: spec for spec in METRIC_SPECS}
KPI_METRICS = tuple(
    spec for spec in METRIC_SPECS if spec.kpi_order is not None)

KPI_GROUPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        'generation_status',
        'Generation groups status',
        'وضع مجموعات التوليد',
        (
            'nominal_capacity_mwh',
            'total_generation_mwh_24h',
            'gas_generation_mwh_24h',
            'steam_fuel_demand_tpd',
            'gas_demand_mm3d',
            'total_fuel_demand_tpd',
            'gas_consumed_mm3d',
            'fuel_oil_consumed_tpd',
            'hydro_dams_capacity_mw',
            'solar_capacity_mw',
            'wind_capacity_mw',
        ),
    ),
    (
        'fuel_movement',
        'Fuel oil movement',
        'حركة الفيول',
        (
            'fuel_oil_received_tpd',
            'fuel_flow_consumed_tpd',
            'fuel_oil_balance_tpd',
        ),
    ),
    (
        'fuel_tanks',
        'Fuel tank information',
        'معلومات خزانات الوقود',
        (
            'fuel_tank_max_capacity_tons',
            'fuel_reserve_tons',
            'fuel_tank_stock_tons',
            'grid_frequency_hz',
            'gov_consumed_mw',
            'gov_allocated_mw',
            'gov_excess_mw',
        ),
    ),
    (
        'generation_report',
        'Generation report',
        'تقرير التوليد',
        (
            'available_generated_power',
            'self_use_losses_mw',
            'net_generation_mwh',
            'industrial_self_use_mw',
            'generation_without_industrial_mw',
            'hydro_output_mw',
            'rotary_reserve_mw',
            'gas_groups_mw',
            'steam_groups_mw',
            'gas_import_mm3d',
            'fuel_reserve_tons',
        ),
    ),
    (
        'incidents_ops',
        'Grid incidents',
        'حوادث الشبكة الكهربائية',
        (
            'generation_incidents_count',
            'grid_incidents_count',
        ),
    ),
)

# Alternate KPI labels when a metric appears in a specific dashboard group.
KPI_GROUP_LABEL_OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    ('fuel_tanks', 'fuel_reserve_tons'): (
        'Consumable fuel reserve',
        'المخزون القابل للاستهلاك',
    ),
    ('generation_report', 'fuel_reserve_tons'): (
        'Fuel oil reserve',
        'المخزون الاحتياطي من الفيول',
    ),
}

TREND_METRICS = (
    'peak_generation_mw',
    'net_generation_mwh',
    'total_generation_mwh_24h',
    'steam_generation_mwh',
    'fuel_reserve_tons',
    'fuel_reserve_pct',
    'gas_import_mm3d',
    'available_generated_power',
    'gov_excess_mw',
)

# Monthly rollup rule per scalar metric (dimension='').
# sum: MTD cumulative; max: peak/worst; avg: daily snapshot average; last: end-of-period.
MONTHLY_AGGREGATION: dict[str, str] = {
    'peak_generation_mw': 'max',
    'net_generation_mwh': 'avg',
    'available_generated_power': 'avg',
    'self_use_losses_mw': 'avg',
    'generation_without_industrial_mw': 'avg',
    'hydro_output_mw': 'avg',
    'rotary_reserve_mw': 'avg',
    'gas_groups_mw': 'avg',
    'steam_groups_mw': 'avg',
    'hydro_dams_capacity_mw': 'avg',
    'solar_capacity_mw': 'avg',
    'wind_capacity_mw': 'avg',
    'nominal_capacity_mwh': 'avg',
    'total_generation_mwh_24h': 'sum',
    'gas_generation_mwh_24h': 'sum',
    'steam_generation_mwh': 'sum',
    'steam_fuel_demand_tpd': 'sum',
    'available_fuel_quantity': 'last',
    'grid_frequency_hz': 'avg',
    'fuel_reserve_tons': 'last',
    'fuel_tank_stock_tons': 'last',
    'fuel_tank_max_capacity_tons': 'last',
    'fuel_reserve_pct': 'last',
    'fuel_oil_received_tpd': 'sum',
    'fuel_flow_consumed_tpd': 'sum',
    'fuel_oil_consumed_tpd': 'sum',
    'fuel_oil_balance_tpd': 'sum',
    'total_fuel_demand_tpd': 'sum',
    'gas_demand_mm3d': 'sum',
    'gas_consumed_mm3d': 'sum',
    'gas_import_mm3d': 'sum',
    'industrial_self_use_mw': 'avg',
    'gov_consumed_mw': 'sum',
    'gov_allocated_mw': 'sum',
    'gov_excess_mw': 'max',
    'generation_incidents_count': 'sum',
    'grid_incidents_count': 'sum',
}

MONTHLY_MIX_AGGREGATION: dict[str, str] = {
    'hydro_dams_capacity_mw': 'avg',
    'gas_generation_mwh_24h': 'sum',
    'steam_groups_mw': 'avg',
    'solar_capacity_mw': 'avg',
    'wind_capacity_mw': 'avg',
}
