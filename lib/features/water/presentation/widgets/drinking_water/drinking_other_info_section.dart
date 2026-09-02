import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';
import 'drinking_value_dropdown.dart';

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
          DrinkingValueDropdown(
            label: 'هل تم تحليل المياه؟',
            fieldKey: 'waterAnalysis',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'خزانات المياه متوفرة؟',
            fieldKey: 'waterTanks',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'معدات المختبر مكتملة؟',
            fieldKey: 'labEquipment',
            items: DrinkingWaterOptions.efficiencies,
            values: values,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
