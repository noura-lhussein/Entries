/// Helpers for water admin `imports/status/` payload → StatsGrid values.
class WaterImportStatusStats {
  WaterImportStatusStats._();

  static String n(dynamic v, [String fallback = '—']) {
    if (v == null) return fallback;
    if (v is num) {
      final s = v.toString();
      // thousands separator for large ints
      if (v is int || v == v.roundToDouble()) {
        final i = v.round();
        final raw = i.toString();
        final buf = StringBuffer();
        for (var i = 0; i < raw.length; i++) {
          if (i > 0 && (raw.length - i) % 3 == 0) buf.write(',');
          buf.write(raw[i]);
        }
        return buf.toString();
      }
      return s;
    }
    final s = v.toString().trim();
    return s.isEmpty ? fallback : s;
  }

  static String yearRange(dynamic from, dynamic to) {
    if (from == null && to == null) return '—';
    if (from == null) return n(to);
    if (to == null) return n(from);
    return '${n(from)}–${n(to)}';
  }

  static List<({String label, String value, String? unit})> dams(
    Map<String, dynamic>? status,
  ) {
    final m = status?['dams'] as Map?;
    if (m == null) {
      return const [
        (label: 'السدود', value: '…', unit: null),
        (label: 'القراءات', value: '…', unit: null),
        (label: 'آخر تاريخ', value: '…', unit: null),
        (label: 'نطاق السنوات', value: '…', unit: null),
      ];
    }
    return [
      (label: 'السدود', value: n(m['dams']), unit: null),
      (label: 'القراءات', value: n(m['readings']), unit: null),
      (label: 'آخر تاريخ', value: n(m['latest_date']), unit: null),
      (
        label: 'نطاق السنوات',
        value: yearRange(m['year_from'], m['year_to']),
        unit: null
      ),
    ];
  }

  static List<({String label, String value, String? unit})> rainfallTop(
    Map<String, dynamic>? status,
  ) {
    final m = status?['rainfall'] as Map?;
    if (m == null) {
      return const [
        (label: 'الأحواض', value: '…', unit: null),
        (label: 'المحطات', value: '…', unit: null),
        (label: 'القراءات', value: '…', unit: null),
      ];
    }
    return [
      (label: 'الأحواض', value: n(m['basins']), unit: null),
      (label: 'المحطات', value: n(m['stations']), unit: null),
      (label: 'القراءات', value: n(m['observations']), unit: null),
    ];
  }

  static List<({String label, String value, String? unit})> rainfallBottom(
    Map<String, dynamic>? status,
  ) {
    final m = status?['rainfall'] as Map?;
    if (m == null) {
      return const [
        (label: 'آخر تاريخ', value: '…', unit: null),
        (label: 'نطاق السنوات', value: '…', unit: null),
      ];
    }
    return [
      (label: 'آخر تاريخ', value: n(m['latest_date']), unit: null),
      (
        label: 'نطاق السنوات',
        value: yearRange(m['year_from'], m['year_to']),
        unit: null
      ),
    ];
  }

  static List<({String label, String value, String? unit})> euphrates(
    Map<String, dynamic>? status,
  ) {
    final m = status?['euphrates'] as Map?;
    if (m == null) {
      return const [
        (label: 'إجمالي السجلات', value: '…', unit: null),
        (label: 'آخر تحديث', value: '…', unit: null),
        (label: 'الأشهر', value: '…', unit: null),
        (label: 'نطاق السنوات', value: '…', unit: null),
      ];
    }
    final months = m['months'];
    final monthCount = months is List ? months.length : 0;
    final latest = n(m['latest_date']);
    String yearRangeStr = '—';
    if (months is List && months.isNotEmpty) {
      final years = months
          .map((e) => e.toString().split('-').first)
          .where((e) => e.isNotEmpty)
          .toSet()
          .toList()
        ..sort();
      if (years.isNotEmpty) {
        yearRangeStr = years.length == 1
            ? years.first
            : '${years.first}–${years.last}';
      }
    }
    return [
      (label: 'إجمالي السجلات', value: n(m['readings']), unit: null),
      (label: 'آخر تحديث', value: latest, unit: null),
      (label: 'الأشهر', value: n(monthCount), unit: null),
      (label: 'نطاق السنوات', value: yearRangeStr, unit: null),
    ];
  }

  static List<({String label, String value, String? unit})> drinkingTop(
    Map<String, dynamic>? status,
  ) {
    final m = status?['drinking_water'] as Map?;
    if (m == null) {
      return const [
        (label: 'المحطات', value: '…', unit: null),
        (label: 'بإحداثيات', value: '…', unit: null),
        (label: 'باستمارة TEI', value: '…', unit: null),
      ];
    }
    return [
      (label: 'المحطات', value: n(m['stations']), unit: null),
      (label: 'بإحداثيات', value: n(m['with_coordinates']), unit: null),
      (label: 'باستمارة TEI', value: n(m['with_survey']), unit: null),
    ];
  }

  static List<({String label, String value, String? unit})> drinkingBottom(
    Map<String, dynamic>? status,
  ) {
    final m = status?['drinking_water'] as Map?;
    if (m == null) {
      return const [
        (label: 'تعمل', value: '…', unit: null),
        (label: 'لا تعمل', value: '…', unit: null),
        (label: 'آخر تاريخ', value: '…', unit: null),
      ];
    }
    return [
      (label: 'تعمل', value: n(m['operational']), unit: null),
      (label: 'لا تعمل', value: n(m['non_operational']), unit: null),
      (
        label: 'آخر تاريخ',
        value: n(m['latest_enrollment_date']),
        unit: null
      ),
    ];
  }
}
