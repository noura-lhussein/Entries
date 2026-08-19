import '../widgets/models/petroleum_data.dart';

OilField parseField(dynamic raw) {
  if (raw is String) return OilField(raw, raw);
  if (raw is! Map) return const OilField('?', '?');
  final m = Map<String, dynamic>.from(raw);
  final code = (m['code'] ?? m['field_code'] ?? m['slug'] ?? '').toString();
  final name = (m['name_ar'] ?? m['name'] ?? m['label_ar'] ?? code).toString();
  return OilField(name, code.isEmpty ? name : code);
}

String parseRefinery(dynamic raw) {
  if (raw is String) return raw;
  if (raw is! Map) return '';
  final m = Map<String, dynamic>.from(raw);
  return (m['name_ar'] ?? m['name'] ?? m['refinery_name'] ?? m['code'] ?? '')
      .toString();
}

({String label, String code}) parseFacility(dynamic raw) {
  if (raw is String) return (label: raw, code: raw);
  if (raw is! Map) return (label: '', code: '');
  final m = Map<String, dynamic>.from(raw);
  final code =
      (m['code'] ?? m['facility_code'] ?? m['slug'] ?? '').toString();
  final label = (m['name_ar'] ?? m['name'] ?? m['label_ar'] ?? code).toString();
  return (label: label.isEmpty ? code : label, code: code.isEmpty ? label : code);
}

bool isPowerFacility(Map m) {
  final type = (m['facility_type'] ?? m['type'] ?? '').toString().toLowerCase();
  final sector = (m['sector'] ?? '').toString().toLowerCase();
  return type.contains('power') ||
      type.contains('plant') ||
      sector.contains('electric') ||
      sector.contains('power');
}

bool isDepotFacility(Map m) {
  final type = (m['facility_type'] ?? m['type'] ?? '').toString().toLowerCase();
  return type.contains('depot') ||
      type.contains('storage') ||
      type.contains('fuel') ||
      type.contains('warehouse');
}
