import 'electricity_field.dart';

/// Matches moe-portal [ELECTRICITY_METRIC_SECTIONS] exactly.
class ElectricityMetricSection {
  final String id;
  final String titleAr;
  final List<ElectricityField> fields;
  const ElectricityMetricSection({
    required this.id,
    required this.titleAr,
    required this.fields,
  });
}

const List<ElectricityMetricSection> kElectricityMetricSections = [
  ElectricityMetricSection(
    id: 'generation_status',
    titleAr: 'وضع مجموعات التوليد',
    fields: [
      ElectricityField('مجموع الاستطاعة الاسمية المتاحة', 'nominal_capacity_mwh', 'ميغاواط ساعي'),
      ElectricityField('المجموع الكلي لإنتاج المجموعات (24 س)', 'total_generation_mwh_24h', 'ميغاواط ساعي'),
      ElectricityField('مجموع التوليد الغازي', 'gas_generation_mwh_24h', 'ميغاواط ساعي'),
      ElectricityField('التوليد البخاري', 'steam_generation_mwh', 'ميغاواط ساعي'),
      ElectricityField('الطلب على الغاز', 'gas_demand_mm3d', 'مليون م³/يوم'),
      ElectricityField('الطلب الكلي على الفيول', 'total_fuel_demand_tpd', 'طن/يوم'),
      ElectricityField('الكمية المستهلكة من الغاز', 'gas_consumed_mm3d', 'مليون م³/يوم'),
      ElectricityField('الفيول المستهلك', 'fuel_oil_consumed_tpd', 'طن/يوم'),
      ElectricityField('الاستطاعة المتاحة   للسدود المائية (الفرات و تشرين)', 'hydro_dams_capacity_mw', 'ميغاواط'),
      ElectricityField('الاستطاعة المتاحة  للعنافات الشمسية', 'solar_capacity_mw', 'ميغاواط'),
      ElectricityField('الاستطاعة المتاحة  للعنافات الريحية', 'wind_capacity_mw', 'ميغاواط'),
    ],
  ),
  ElectricityMetricSection(
    id: 'fuel_movement',
    titleAr: 'حركة الفيول',
    fields: [
      ElectricityField('الفيول الوارد', 'fuel_oil_received_tpd', 'طن/يوم'),
      ElectricityField('حركة الفيول المستهلك', 'fuel_flow_consumed_tpd', 'طن/يوم'),
      ElectricityField('وفر الفيول', 'fuel_oil_balance_tpd', 'طن/يوم'),
    ],
  ),
  ElectricityMetricSection(
    id: 'fuel_tanks',
    titleAr: 'معلومات خزانات الوقود',
    fields: [
      ElectricityField('السعة الأعظمية لخزانات الوقود', 'fuel_tank_max_capacity_tons', 'طن'),
      ElectricityField('المخزون القابل للاستهلاك', 'fuel_reserve_tons', 'طن'),
      ElectricityField('تردد الشبكة', 'grid_frequency_hz', 'هرتز'),
      ElectricityField('مخزون خزانات الوقود', 'fuel_tank_stock_tons', 'طن'),
    ],
  ),
  ElectricityMetricSection(
    id: 'generation_report',
    titleAr: 'تقرير التوليد',
    fields: [
      ElectricityField('الاستطاعة المتاحة المولدة مع الشمسي', 'available_generated_power', 'ميغاواط'),
      ElectricityField('استهلاك ذاتي و ضياع', 'self_use_losses_mw', 'ميغاواط'),
      ElectricityField('التوليد الصافي', 'net_generation_mwh', 'ميغاواط'),
      ElectricityField('استهلاك صناعي', 'industrial_self_use_mw', 'ميغاواط'),
      ElectricityField('الاستطاعة المولدة بدون صناعي', 'generation_without_industrial_mw', 'ميغاواط'),
      ElectricityField('السدود', 'hydro_output_mw', 'ميغاواط'),
      ElectricityField('احتياط دوار', 'rotary_reserve_mw', 'ميغاواط'),
      ElectricityField('الاستطاعة المستهلكة', 'gov_consumed_mw', 'ميغاواط'),
      ElectricityField('استطاعة المجموعات الغازية', 'gas_groups_mw', 'ميغاواط'),
      ElectricityField('استطاعة المجموعات البخارية', 'steam_groups_mw', 'ميغاواط'),
      ElectricityField('الغاز الوارد', 'gas_import_mm3d', 'مليون م³/يوم'),
      ElectricityField('المخزون الاحتياطي من الفيول', 'fuel_reserve_tons', 'طن'),
    ],
  ),
];

/// Extra national keys not in section grids but still upserted when present.
const List<ElectricityField> kExtraNationalMetricFields = [
  ElectricityField('ذروة التوليد', 'peak_generation_mw', 'ميغاواط'),
  ElectricityField('نسبة المخزون', 'fuel_reserve_pct', ''),
  ElectricityField('الكمية المخصصة (وطني)', 'gov_allocated_mw', 'ميغاواط'),
  ElectricityField('التجاوز (وطني)', 'gov_excess_mw', 'ميغاواط'),
  ElectricityField('كمية الفيول المتاحة', 'available_fuel_quantity', ''),
  ElectricityField('حوادث التوليد (عدد)', 'generation_incidents_count', ''),
  ElectricityField('حوادث الخطوط (عدد)', 'grid_incidents_count', ''),
  ElectricityField('مجموع التوليد البخاري على الفيول', 'steam_fuel_demand_tpd', 'طن/يوم'),
];

List<ElectricityField> get kAllElectricityMetricFields => [
      for (final s in kElectricityMetricSections) ...s.fields,
      ...kExtraNationalMetricFields,
    ];

const List<ElectricityField> kHydraulicFields = [
  ElectricityField('المنسوب الامامي (m)', 'front_level'),
  ElectricityField('المنسوب الخلفي (m)', 'back_level'),
  ElectricityField('التوليد (MWh)', 'generation'),
  ElectricityField('المرر (m3/sec)', 'outflow'),
  ElectricityField('الوارد', 'inflow'),
  ElectricityField('المتوقع', 'expected'),
];

class NamedCode {
  final String code;
  final String nameAr;
  final double? maxCapacity;
  const NamedCode(this.code, this.nameAr, [this.maxCapacity]);
}

const List<NamedCode> kHydraulicDams = [
  NamedCode('thawra', 'سد الفرات'),
  NamedCode('euphrates', 'سد الفرات'),
  NamedCode('tishreen', 'سد تشرين'),
];

const List<NamedCode> kGovernorates = [
  NamedCode('damascus', 'دمشق'),
  NamedCode('rif_damascus', 'ريف دمشق'),
  NamedCode('sweida', 'السويداء'),
  NamedCode('daraa', 'درعا'),
  NamedCode('quneitra', 'القنيطرة'),
  NamedCode('homs', 'حمص'),
  NamedCode('hama', 'حماه'),
  NamedCode('tartous', 'طرطوس'),
  NamedCode('latakia', 'اللاذقية'),
  NamedCode('aleppo', 'حلب'),
  NamedCode('deir_ez_zor', 'دير الزور'),
  NamedCode('raqqa', 'الرقة'),
  NamedCode('hasakah', 'الحسكة'),
];

const List<NamedCode> kFuelTanks = [
  NamedCode('zara', 'الزارة', 72000),
  NamedCode('banias', 'بانياس', 84000),
  NamedCode('tishreen', 'تشرين', 48000),
  NamedCode('maharda', 'محردة', 36000),
  NamedCode('aleppo', 'حلب', 56000),
];
