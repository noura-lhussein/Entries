// ── Oil fields production ─────────────────────────────────────────────────────
class OilField {
  final String nameAr;
  final String code;
  const OilField(this.nameAr, this.code);
}

// ── Fuel depots ───────────────────────────────────────────────────────────────
const List<String> kFuelDepots = [
  'مستودع حمص الاستراتيجي',
  'مستودع دمشق',
  'مستودع حلب',
  'مستودع درعا',
  'مستودع طرطوس',
];

const List<String> kFuelTypes = ['بنزين', 'ديزل', 'فيول', 'غاز مسال'];

// ── Gas-to-electricity stations ───────────────────────────────────────────────
const List<String> kGasStations = [
  'محطة تشرين',
  'محطة الفرات',
  'محطة كديران',
  'محطة محردة',
  'محطة حلب',
];

// ── Production loss types ─────────────────────────────────────────────────────
const List<String> kLossTypes = ['توقف مجدول', 'عطل فني', 'قوة قاهرة', 'صيانة'];

// ── SPC daily report rows (keys = moe-portal EXECUTIVE_METRIC_KEYS) ────────────
class SpcRow {
  final String label;
  final String key;
  final String unit;
  final int colorIndex; // 0=green, 1=blue, 2=yellow
  const SpcRow(this.label, this.key, this.unit, this.colorIndex);
}

class OilMetricSection {
  final String id;
  final String titleAr;
  final List<SpcRow> fields;
  const OilMetricSection({
    required this.id,
    required this.titleAr,
    required this.fields,
  });
}

const List<OilMetricSection> kOilMetricSections = [
  OilMetricSection(
    id: 'oil_production',
    titleAr: 'إنتاج النفط',
    fields: [
      SpcRow('إجمالي إنتاج النفط', 'total_oil_production_bbl', 'برميل', 0),
      SpcRow('إجمالي النفط الخام المرحل', 'total_crude_transferred_bbl', 'برميل', 0),
    ],
  ),
  OilMetricSection(
    id: 'clean_gas',
    titleAr: 'الغاز النظيف',
    fields: [
      SpcRow('الإنتاج المحلي من الغاز النظيف', 'local_clean_gas_mm3', 'مليون م3', 1),
      SpcRow('الغاز النظيف المستورد من أذربيجان', 'clean_gas_import_azerbaijan_mm3',
          'مليون م3', 1),
      SpcRow('الغاز النظيف المستورد من الأردن', 'clean_gas_import_jordan_mm3',
          'مليون م3', 1),
      SpcRow('إجمالي الغاز النظيف (محلي + مستورد)', 'total_clean_gas_mm3',
          'مليون م3', 1),
      SpcRow('الغاز النظيف الموزّع للمستهلكين', 'clean_gas_distributed_mm3',
          'مليون م3', 1),
      SpcRow('استهلاك قطاع الكهرباء من الغاز النظيف',
          'electricity_clean_gas_consumption_mm3', 'مليون م3', 1),
    ],
  ),
  OilMetricSection(
    id: 'fuel_sales',
    titleAr: 'مبيعات المشتقات',
    fields: [
      SpcRow('كميات المازوت المباعة', 'mazut_sold_thu_fri_m3', 'م3', 2),
      SpcRow('كميات البنزين (90+95) المباعة', 'gasoline_90_95_sold_thu_fri_m3',
          'م3', 2),
      SpcRow('كميات الغاز المسال المنزلي المباعة', 'domestic_lpg_sold_m3', 'م3', 2),
      SpcRow('كميات الفيول المباعة', 'fuel_oil_sold_m3', 'م3', 2),
    ],
  ),
  OilMetricSection(
    id: 'commodity_prices',
    titleAr: 'أسعار السلع',
    fields: [
      SpcRow('سعر النفط كخام برنت', 'brent_crude_price_usd_bbl', 'برميل', 0),
      SpcRow('سعر الغاز (مليون وحدة حرارية بريطانية)', 'gas_price_usd_mmbtu',
          'مليون وحدة حرارية بريطانية', 0),
    ],
  ),
];

List<SpcRow> get kSpcRows => [
      for (final s in kOilMetricSections) ...s.fields,
    ];

bool isThuFriReportDate(DateTime date) =>
    date.weekday == DateTime.thursday || date.weekday == DateTime.friday;

String fuelSalesLabel(SpcRow row, DateTime date) {
  if (row.key == 'mazut_sold_thu_fri_m3' && isThuFriReportDate(date)) {
    return 'كميات المازوت المباعة ليومي الخميس والجمعة';
  }
  if (row.key == 'gasoline_90_95_sold_thu_fri_m3' && isThuFriReportDate(date)) {
    return 'كميات البنزين (90+95) المباعة ليومي الخميس والجمعة';
  }
  return row.label;
}
