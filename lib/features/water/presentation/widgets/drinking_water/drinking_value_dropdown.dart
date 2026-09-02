import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';

class DrinkingValueDropdown extends StatelessWidget {
  const DrinkingValueDropdown({
    super.key,
    required this.label,
    required this.fieldKey,
    required this.items,
    required this.values,
    required this.onChanged,
  });

  final String label;
  final String fieldKey;
  final List<String> items;
  final Map<String, String> values;
  final void Function(String key, String value) onChanged;

  @override
  Widget build(BuildContext context) {
    return AppDropdownField(
      label: label,
      value: values[fieldKey]!,
      items: items,
      onChanged: (v) {
        if (v == null) return;
        onChanged(fieldKey, v);
      },
    );
  }
}
