import '../utils/parse_geology_number.dart';

double? parseGeologyNum(String text) => parseGeologyNumber(text);

({String productionType, String unit}) parseLegacyUnit(String raw) {
  final text = raw.trim();
  if (text.isEmpty) return (productionType: '', unit: '');
  var productionType = '';
  var unit = text;
  if (text.contains('ذاتي')) {
    productionType = 'ذاتي';
  } else if (text.contains('معهّد') || text.contains('معهد')) {
    productionType = 'معهّد';
  }
  if (text.contains('/')) {
    final parts =
        text.split('/').map((p) => p.trim()).where((p) => p.isNotEmpty);
    final list = parts.toList();
    if (list.length >= 2) {
      if (productionType.isEmpty) productionType = list.first;
      unit = list.last;
    }
  }
  unit = unit.replaceAll('م³', 'م3').replaceAll('م^3', 'م3').trim();
  if (unit == 'طن/' || unit == 'طن') unit = 'طن';
  return (productionType: productionType, unit: unit);
}

double? executionPct(double? plan, double? executed) {
  if (plan == null || executed == null || plan == 0) return null;
  return ((executed * 10000) / plan).round() / 100;
}

List<dynamic> extractGeologyOreRows(Map<String, dynamic> detail) {
  const keys = ['rows', 'items', 'ore_rows', 'production', 'products'];
  for (final key in keys) {
    final value = detail[key];
    if (value is List) return value;
  }
  final data = detail['data'];
  if (data is List) return data;
  if (data is Map) {
    return extractGeologyOreRows(Map<String, dynamic>.from(data));
  }
  return const [];
}
