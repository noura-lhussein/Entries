from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TargetMetricSpec:
    key: str
    label_en: str
    label_ar: str
    unit: str
    higher_is_better: bool = True


TARGET_METRICS: tuple[TargetMetricSpec, ...] = (
    TargetMetricSpec('total_generation_mwh', 'Total generation', 'إجمالي التوليد', 'MWh/d'),
    TargetMetricSpec('peak_demand_mw', 'Peak demand', 'ذروة الحمل', 'MW'),
    TargetMetricSpec('plant_availability_percent', 'Plant availability', 'توفر المحطات', '%'),
    TargetMetricSpec('capacity_factor_percent', 'Capacity factor', 'معامل الحمل', '%'),
    TargetMetricSpec('renewable_share_percent', 'Renewable share', 'حصة المتجددة', '%'),
    TargetMetricSpec('supply_demand_gap_mw', 'Supply–demand gap', 'فجوة العرض والطلب', 'MW', higher_is_better=False),
    TargetMetricSpec('generation_mwh', 'Plant generation', 'توليد المحطة', 'MWh/d'),
)

TARGET_METRIC_BY_KEY = {spec.key: spec for spec in TARGET_METRICS}

SNAPSHOT_TARGET_MAP: dict[str, str] = {
    'total_generation_mwh': 'total_generation_mwh',
    'peak_demand_mw': 'peak_demand_mw',
    'plant_availability_percent': 'plant_availability_percent',
    'capacity_factor_percent': 'capacity_factor_percent',
    'renewable_share_percent': 'renewable_share_percent',
    'supply_demand_gap_mw': 'supply_demand_gap_mw',

}
