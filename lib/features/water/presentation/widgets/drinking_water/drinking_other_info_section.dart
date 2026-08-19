import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';

class DrinkingOtherInfoSection extends StatelessWidget {
  const DrinkingOtherInfoSection({
    super.key,
    required this.values,
    required this.onChanged,
  });

  final Map<String, String> values;
  final void Function(String key, String value) onChanged;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'معلومات أخرى',
      child: FieldsWrap(
        fields: [
          _dropdown(
            'هل تم تحليل المياه؟',
            'waterAnalysis',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'خزانات المياه متوفرة؟',
            'waterTanks',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'معدات المختبر مكتملة؟',
            'labEquipment',
            DrinkingWaterOptions.efficiencies,
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
