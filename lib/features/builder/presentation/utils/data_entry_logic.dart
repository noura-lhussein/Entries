import '../../data/models/builder_models.dart';

bool isReportDateField(FormSchemaField field) {
  final key = field.key.trim();
  final label = field.labelAr.trim();
  return field.type == 'date' ||
      key == 'report_date' ||
      key == 'reading_date' ||
      key == 'update_date' ||
      label == 'تاريخ التقرير' ||
      label == 'تاريخ القراءة' ||
      label == 'تاريخ التحديث';
}

String? normalizeDateValue(String? raw) {
  if (raw == null) return null;
  final text = raw.trim();
  if (text.length >= 10 && text[4] == '-' && text[7] == '-') {
    return text.substring(0, 10);
  }
  return null;
}

FormSchemaField? findReportDateField(List<FormSchemaField> fields) {
  for (final f in fields) {
    if (isReportDateField(f)) return f;
  }
  return null;
}

String? fieldKeyOfType(List<FormSchemaField> fields, String type) {
  for (final f in fields) {
    if (f.type == type) return f.key;
  }
  return null;
}

({String? entityType, int? entityId}) currentEntityFromValues(
  List<FormSchemaField> fields,
  Map<String, String> values,
) {
  for (final f in fields) {
    if (!f.isEntity) continue;
    final raw = values[f.key];
    if (raw == null || raw.trim().isEmpty) continue;
    final id = int.tryParse(raw);
    if (id != null) return (entityType: f.type, entityId: id);
  }
  return (entityType: null, entityId: null);
}

Map<String, String> applyComputedAndWarnings({
  required List<FormSchemaField> fields,
  required Map<String, String> values,
}) {
  final next = Map<String, String>.from(values);
  for (final f in fields) {
    final expr = (f.computedFrom ?? '').replaceAll(RegExp(r'\s+'), '');
    if (expr.isEmpty) continue;
    final m = RegExp(r'^([a-zA-Z0-9_]+)-([a-zA-Z0-9_]+)$').firstMatch(expr);
    if (m == null) continue;
    final a = num.tryParse(next[m.group(1)!] ?? '');
    final b = num.tryParse(next[m.group(2)!] ?? '');
    if (a != null && b != null) {
      next[f.key] = (a - b).toString();
    }
  }
  return next;
}

Map<String, String> collectWarnings({
  required List<FormSchemaField> fields,
  required Map<String, String> values,
}) {
  final warnings = <String, String>{};
  for (final f in fields) {
    final capKey = f.warnIfGtField;
    if (capKey == null || capKey.isEmpty) continue;
    final v = num.tryParse(values[f.key] ?? '');
    final cap = num.tryParse(values[capKey] ?? '');
    if (v != null && cap != null && v > cap) {
      warnings[f.key] = f.messageAr?.trim().isNotEmpty == true
          ? f.messageAr!
          : 'القيمة أعلى من الحد';
    }
  }
  return warnings;
}

String? validateField(FormSchemaField field, Map<String, String> values) {
  if (field.readonly) return null;
  final raw = values[field.key] ?? '';
  if (field.required && raw.trim().isEmpty) return 'هذا الحقل مطلوب';
  if (field.type == 'number' && raw.trim().isNotEmpty) {
    final n = num.tryParse(raw);
    if (n == null) return 'قيمة غير صالحة';
    if (field.min != null && n < field.min!) {
      return 'الحد الأدنى ${field.min}';
    }
    if (field.max != null && n > field.max!) {
      return 'الحد الأعلى ${field.max}';
    }
    if (field.maxField != null && field.maxField!.isNotEmpty) {
      final cap = num.tryParse(values[field.maxField!] ?? '');
      if (cap != null && n > cap) {
        return field.messageAr?.trim().isNotEmpty == true
            ? field.messageAr!
            : 'أعلى من ${field.maxField}';
      }
    }
  }
  return null;
}

Map<String, String> validateRequired(
  List<FormSchemaField> fields,
  Map<String, String> values,
) {
  final errors = <String, String>{};
  for (final f in fields) {
    if (f.readonly || !f.required) continue;
    final v = values[f.key];
    if (v == null || v.trim().isEmpty) {
      errors[f.key] = 'هذا الحقل مطلوب';
    }
  }
  return errors;
}

List<Map<String, dynamic>> collectAttributeValues({
  required List<FormSchemaField> fields,
  required Map<String, String> values,
}) {
  final rows = <Map<String, dynamic>>[];
  for (final f in fields) {
    if (f.readonly) continue;
    var value = values[f.key] ?? '';
    if (f.isBoolean) {
      final on = value == 'true' || value == '1';
      rows.add({'id': f.id, 'value': on});
      continue;
    }
    if (value.trim().isEmpty) continue;
    rows.add({'id': f.id, 'value': value});
  }
  return rows;
}

String? extractApiDetail(Object error) {
  try {
    final response = (error as dynamic).response;
    final data = response?.data;
    if (data is Map) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) return detail;
      final message = data['message'];
      if (message is String && message.trim().isNotEmpty) return message;
    }
  } catch (_) {}
  return null;
}

bool isDuplicateDateError(Object error) {
  try {
    final response = (error as dynamic).response;
    final status = response?.statusCode;
    final data = response?.data;
    if (status == 409) return true;
    if (data is Map && data['code'] == 'duplicate_report_date') return true;
  } catch (_) {}
  return false;
}
