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
    TargetMetricSpec('crude_oil_bbl', 'Crude oil production', 'إنتاج النفط الخام', 'bbl/d'),
    TargetMetricSpec('natural_gas_mmscf', 'Natural gas production', 'إنتاج الغاز الطبيعي', 'MMscf/d'),
    TargetMetricSpec('condensate_bbl', 'Condensate production', 'إنتاج المتكاثفات', 'bbl/d'),
    TargetMetricSpec('total_export_bbl', 'Export volume', 'حجم الصادرات', 'bbl'),
    TargetMetricSpec('export_revenue_usd', 'Export revenue', 'إيرادات التصدير', 'USD'),
    TargetMetricSpec('gasoline_ton', 'Gasoline output', 'إنتاج البنزين', 't'),
    TargetMetricSpec('diesel_ton', 'Diesel output', 'إنتاج الديزل', 't'),
    TargetMetricSpec('fuel_oil_ton', 'Fuel oil output', 'إنتاج الفيول', 't'),
    TargetMetricSpec('gasoline_stock_days', 'Gasoline stock coverage', 'كفاية مخزون البنزين', 'days'),
    TargetMetricSpec('diesel_stock_days', 'Diesel stock coverage', 'كفاية مخزون الديزل', 'days'),
    TargetMetricSpec('gas_supply_to_power_percent', 'Gas supply to power', 'إمداد الغاز للكهرباء', '%'),
    TargetMetricSpec('supplied_mmscf', 'Gas supplied to power', 'الغاز المورد للكهرباء', 'MMscf/d'),
    TargetMetricSpec('required_mmscf', 'Gas required by power', 'الغاز المطلوب للكهرباء', 'MMscf/d'),
    TargetMetricSpec('refinery_utilization_percent', 'Refinery utilization', 'استغلال المصافي', '%'),
    TargetMetricSpec('total_losses_bbl', 'Production losses', 'فاقد الإنتاج', 'bbl/d', higher_is_better=False),
    TargetMetricSpec('dist_tonnes', 'Distribution volume', 'كمية التوزيع', 't'),
)

TARGET_METRIC_BY_KEY = {spec.key: spec for spec in TARGET_METRICS}

# National snapshot KPI field → target metric_key
SNAPSHOT_TARGET_MAP: dict[str, str] = {
    'total_oil_production_bpd': 'crude_oil_bbl',
    'total_gas_production_mmscf': 'natural_gas_mmscf',
    'total_export_bbl': 'total_export_bbl',
    'export_revenue_usd': 'export_revenue_usd',
    'gasoline_stock_days': 'gasoline_stock_days',
    'diesel_stock_days': 'diesel_stock_days',
    'gas_supply_to_power_percent': 'gas_supply_to_power_percent',
    'refinery_utilization_percent': 'refinery_utilization_percent',
    'total_losses_bbl': 'total_losses_bbl',
}
