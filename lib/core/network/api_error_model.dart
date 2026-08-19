class ApiErrorModel {
  final String? message;
  final dynamic data;
  final int? code;
  final Map<String, dynamic>? errors;

  ApiErrorModel({
    required this.message,
    this.code,
    this.data,
    this.errors,
  });

  factory ApiErrorModel.fromJson(Map<String, dynamic> json) {
    final errors = _extractErrors(json);
    return ApiErrorModel(
      message: _extractMessage(json),
      code: (json['code'] as num?)?.toInt() ??
          (json['status_code'] as num?)?.toInt(),
      data: json['data'],
      errors: errors,
    );
  }

  static String? _extractMessage(Map<String, dynamic> json) {
    for (final key in const ['message', 'detail', 'error', 'msg']) {
      final value = json[key];
      if (value is String && value.trim().isNotEmpty) return value.trim();
      if (value is List && value.isNotEmpty) {
        final first = value.first?.toString().trim();
        if (first != null && first.isNotEmpty) return first;
      }
    }

    final nonField = json['non_field_errors'];
    if (nonField is List && nonField.isNotEmpty) {
      final first = nonField.first?.toString().trim();
      if (first != null && first.isNotEmpty) return first;
    }
    if (nonField is String && nonField.trim().isNotEmpty) {
      return nonField.trim();
    }

    return null;
  }

  static Map<String, dynamic>? _extractErrors(Map<String, dynamic> json) {
    final nested = json['errors'];
    if (nested is Map) {
      return nested.map((key, value) => MapEntry(key.toString(), value));
    }

    // DRF field errors live at the top level alongside detail/message.
    const reserved = {
      'message',
      'detail',
      'error',
      'msg',
      'code',
      'status_code',
      'data',
      'errors',
      'non_field_errors',
    };
    final fieldErrors = <String, dynamic>{};
    for (final entry in json.entries) {
      if (reserved.contains(entry.key)) continue;
      final value = entry.value;
      if (value is List || value is String) {
        fieldErrors[entry.key] = value;
      }
    }
    return fieldErrors.isEmpty ? null : fieldErrors;
  }

  Map<String, dynamic> toJson() => {
        'message': message,
        'data': data,
        'code': code,
        'errors': errors,
      };
}
