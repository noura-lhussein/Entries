import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';

class DrinkingStationTypeSection extends StatelessWidget {
  const DrinkingStationTypeSection({
    super.key,
    required this.values,
    required this.onChanged,
  });

  final Map<String, String> values;
  final void Function(String key, String value) onChanged;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'نوع المحطة',
      child: FieldsWrap(
        fields: [
          _dropdown(
            'محطة ضخ',
            'pumpingStation',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'محطة بئر',
            'wellStation',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'محطة تنقية',
            'treatmentStation',
            DrinkingWaterOptions.yesNo,
          ),
        ],
      ),
    );
  }

  Widget _dropdown(String label, String key, List<String> items) =>
      AppDropdownField(
        label: label,
        value: values[key]!,
        items: items,
        onChanged: (v) {
          if (v == null) return;
          onChanged(key, v);
        },
      );
}
