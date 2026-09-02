import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';
import 'drinking_value_dropdown.dart';

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
          DrinkingValueDropdown(
            label: 'محطة ضخ',
            fieldKey: 'pumpingStation',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'محطة بئر',
            fieldKey: 'wellStation',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'محطة تنقية',
            fieldKey: 'treatmentStation',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
