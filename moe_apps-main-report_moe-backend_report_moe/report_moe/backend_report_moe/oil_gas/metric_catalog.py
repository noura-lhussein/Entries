from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class MetricSpec:
    key: str
    label_en: str
    label_ar: str
    unit: str
    category: str
    kpi_order: int | None = None
    kpi_status_rule: str | None = None  # lower_is_bad | higher_is_bad | zero_is_bad


EXECUTIVE_METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec('total_oil_production_bbl', 'Total oil production',
               'إجمالي إنتاج النفط', 'bbl', 'oil', 1),
    MetricSpec('total_crude_transferred_bbl', 'Total crude oil transferred',
               'إجمالي النفط الخام المرحل', 'bbl', 'oil', 2),
    MetricSpec('local_clean_gas_mm3', 'Local clean gas production',
               'الإنتاج المحلي من الغاز النظيف', 'M m³', 'gas', 3),
    MetricSpec(
        'clean_gas_import_azerbaijan_mm3',
        'Clean gas imported from Azerbaijan',
        'الغاز النظيف المستورد من أذربيجان',
        'M m³',
        'gas',
        4,
    ),
    MetricSpec(
        'clean_gas_import_jordan_mm3',
        'Clean gas imported from Jordan',
        'الغاز النظيف المستورد من الأردن',
        'M m³',
        'gas',
        5,
    ),
    MetricSpec(
        'total_clean_gas_mm3',
        'Total clean gas (local + imported)',
        'إجمالي الغاز النظيف (الإنتاج المحلي + المستورد)',
        'M m³',
        'gas',
        6,
    ),
    MetricSpec(
        'clean_gas_distributed_mm3',
        'Clean gas distributed to consumers',
        'مجموع كميات الغاز النظيف الموزعة للمستهلكين',
        'M m³',
        'gas',
        7,
    ),
    MetricSpec(
        'electricity_clean_gas_consumption_mm3',
        'Electricity sector clean gas consumption',
        'استهلاك قطاع الكهرباء من الغاز النظيف',
        'M m³',
        'gas',
        8,
    ),
    MetricSpec(
        'mazut_sold_thu_fri_m3',
        'Mazut sold (Thu–Fri)',
        'كميات المازوت المباعة ليومي الخميس والجمعة',
        'm³',
        'fuel_sales',
        9,
    ),
    MetricSpec(
        'gasoline_90_95_sold_thu_fri_m3',
        'Gasoline 90+95 sold (Thu–Fri)',
        'كميات البنزين (90+95) المباعة ليومي الخميس والجمعة',
        'm³',
        'fuel_sales',
        10,
    ),
    MetricSpec(
        'domestic_lpg_sold_m3',
        'Domestic LPG sold',
        'كميات الغاز المسال (المنزلي LPG) المباعة',
        'm³',
        'fuel_sales',
        11,
    ),
    MetricSpec('fuel_oil_sold_m3', 'Fuel oil sold',
               'كميات الفيول المباعة', 'm³', 'fuel_sales', 12),
    MetricSpec(
        'brent_crude_price_usd_bbl',
        'Brent crude oil price',
        'سعر النفط كخام برنت',
        'USD/bbl',
        'prices',
        13,
    ),
    MetricSpec(
        'gas_price_usd_mmbtu',
        'Gas price',
        'سعر الغاز (مليون وحدة حرارية بريطانية)',
        'USD/MMBtu',
        'prices',
        14,
    ),
)

EXECUTIVE_KPI_GROUPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        'oil_production',
        'Oil production',
        'إنتاج النفط',
        ('total_oil_production_bbl', 'total_crude_transferred_bbl'),
    ),
    (
        'clean_gas',
        'Clean gas',
        'الغاز النظيف',
        (
            'local_clean_gas_mm3',
            'clean_gas_import_azerbaijan_mm3',
            'clean_gas_import_jordan_mm3',
            'total_clean_gas_mm3',
            'clean_gas_distributed_mm3',
            'electricity_clean_gas_consumption_mm3',
        ),
    ),
    (
        'fuel_sales',
        'Fuel product sales',
        'مبيعات المشتقات',
        (
            'mazut_sold_thu_fri_m3',
            'gasoline_90_95_sold_thu_fri_m3',
            'domestic_lpg_sold_m3',
            'fuel_oil_sold_m3',
        ),
    ),
    (
        'commodity_prices',
        'Commodity prices',
        'أسعار السلع',
        (
            'brent_crude_price_usd_bbl',
            'gas_price_usd_mmbtu',
        ),
    ),
)

EXECUTIVE_TREND_METRICS = (
    'total_oil_production_bbl',
    'total_clean_gas_mm3',
    'clean_gas_distributed_mm3',
    'electricity_clean_gas_consumption_mm3',
)

EXECUTIVE_METRIC_KEYS = frozenset(spec.key for spec in EXECUTIVE_METRIC_SPECS)
EXECUTIVE_OPTIONAL_METRIC_KEYS = frozenset({
    'total_crude_transferred_bbl',
    'brent_crude_price_usd_bbl',
    'gas_price_usd_mmbtu',
})

THU_FRI_FUEL_SALES_METRIC_KEYS = frozenset({
    'mazut_sold_thu_fri_m3',
    'gasoline_90_95_sold_thu_fri_m3',
})

DAILY_FUEL_SALES_LABELS: dict[str, tuple[str, str]] = {
    'mazut_sold_thu_fri_m3': ('Mazut sold', 'كميات المازوت المباعة'),
    'gasoline_90_95_sold_thu_fri_m3': ('Gasoline 90+95 sold', 'كميات البنزين (90+95) المباعة'),
}


def is_thu_fri_report(report_date: date) -> bool:
    return report_date.weekday() in (3, 4)


def resolve_metric_labels(spec: MetricSpec, report_date: date) -> tuple[str, str]:
    if spec.key in THU_FRI_FUEL_SALES_METRIC_KEYS and not is_thu_fri_report(report_date):
        return DAILY_FUEL_SALES_LABELS[spec.key]
    return spec.label_en, spec.label_ar


METRIC_SPECS: tuple[MetricSpec, ...] = EXECUTIVE_METRIC_SPECS + (
    MetricSpec('crude_cumulative_bbl', 'Cumulative crude received',
               'الخام التراكمي المستلم', 'bbl', 'logistics'),
    MetricSpec('crude_transfer_daily_bbl', 'Crude transfer (Banias→Homs)',
               'نقل الخام (بانياس→حمص)', 'bbl', 'logistics'),
    MetricSpec('crude_transfer_mtd_bbl', 'Crude transfer MTD',
               'نقل الخام تراكمي شهري', 'bbl', 'logistics'),
    MetricSpec('catalytic_load_homs_t', 'Catalytic load — Homs',
               'الحمل التكريري — حمص', 't', 'refinery'),
    MetricSpec('catalytic_load_banias_t', 'Catalytic load — Banias',
               'الحمل التكريري — بانياس', 't', 'refinery'),
    MetricSpec('domestic_gas_index', 'Domestic gas index',
               'مؤشر الغاز المنزلي', '', 'gas'),
    MetricSpec('gas_import_azerbaijan_k_m3d', 'Azerbaijan gas import',
               'استيراد الغاز الأذربيجاني', '10³ m³/d', 'gas'),
    MetricSpec('reserve_days_network', 'Network reserve days',
               'كفاية أيام الشبكة', 'days', 'supply'),
    MetricSpec('units_operating', 'Units operating',
               'وحدات عاملة', 'units', 'refinery'),
    MetricSpec('units_under_repair', 'Units under repair',
               'وحدات قيد الإصلاح', 'units', 'refinery'),
    MetricSpec('product_gasoline_t', 'Gasoline', 'بنزين', 't', 'product'),
    MetricSpec('product_mazut_t', 'Mazut', 'مازوت', 't', 'product'),
    MetricSpec('product_fuel_oil_t', 'Fuel oil', 'فيول', 't', 'product'),
    MetricSpec('product_vgo_t', 'VGO', 'VGO', 't', 'product'),
    MetricSpec('product_residue_t', 'Residue', 'رصيد', 't', 'product'),
    MetricSpec('product_crude_adequacy_t', 'Crude adequacy',
               'كفاية خام', 't', 'product'),
    MetricSpec('dist_tonnes', 'Distribution volume',
               'كمية التوزيع', 't', 'distribution'),
    MetricSpec('dist_reserve_days', 'Reserve days',
               'كفاية أيام', 'days', 'distribution'),
    MetricSpec('gas_production_k_m3', 'Gas production',
               'إنتاج الغاز', '10³ m³', 'gas'),
)

METRIC_BY_KEY = {spec.key: spec for spec in METRIC_SPECS}
KPI_METRICS = tuple(
    spec for spec in EXECUTIVE_METRIC_SPECS if spec.kpi_order is not None)
LEGACY_KPI_METRICS = tuple(
    spec for spec in METRIC_SPECS if spec.kpi_order is not None and spec.key not in EXECUTIVE_METRIC_KEYS
)

REFINERIES = ('homs', 'banias')
PRODUCTS = (
    'product_gasoline_t',
    'product_mazut_t',
    'product_fuel_oil_t',
    'product_vgo_t',
    'product_residue_t',
    'product_crude_adequacy_t',
)

DISTRIBUTION_REGIONS = (
    ('jinder', 'Jinder + expansion', 'جندر + توسعة'),
    ('tartous', 'Tartous', 'طرطوس'),
    ('aleppo', 'Aleppo', 'حلب'),
    ('banias', 'Banias', 'بانياس'),
    ('homs', 'Homs', 'حمص'),
    ('damascus', 'Damascus', 'دمشق'),
)

# Monthly rollup rule per executive scalar metric (dimension='').
MONTHLY_AGGREGATION: dict[str, str] = {
    'total_oil_production_bbl': 'sum',
    'total_crude_transferred_bbl': 'sum',
    'local_clean_gas_mm3': 'sum',
    'clean_gas_import_azerbaijan_mm3': 'sum',
    'clean_gas_import_jordan_mm3': 'sum',
    'total_clean_gas_mm3': 'sum',
    'clean_gas_distributed_mm3': 'sum',
    'electricity_clean_gas_consumption_mm3': 'sum',
    'mazut_sold_thu_fri_m3': 'sum',
    'gasoline_90_95_sold_thu_fri_m3': 'sum',
    'domestic_lpg_sold_m3': 'sum',
    'fuel_oil_sold_m3': 'sum',
    'brent_crude_price_usd_bbl': 'avg',
    'gas_price_usd_mmbtu': 'avg',
}
