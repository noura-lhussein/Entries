import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';
import 'drinking_value_dropdown.dart';

class DrinkingOperationStatusSection extends StatelessWidget {
  const DrinkingOperationStatusSection({
    super.key,
    required this.values,
    required this.onChanged,
    required this.notOperatingReasonController,
  });

  final Map<String, String> values;
  final void Function(String key, String value) onChanged;
  final TextEditingController notOperatingReasonController;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'التشغيل والحالة',
      child: FieldsWrap(
        fields: [
          DrinkingValueDropdown(
            label: 'هل المحطة تعمل؟',
            fieldKey: 'isWorking',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          AppTextField(
            label: 'سبب عدم التشغيل',
            controller: notOperatingReasonController,
          ),
          DrinkingValueDropdown(
            label: 'حالة مبنى المحطة',
            fieldKey: 'buildingStatus',
            items: DrinkingWaterOptions.conditions,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'وجود إجراءات السلامة',
            fieldKey: 'safetyProcedures',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'تأهيل سابق؟',
            fieldKey: 'previousRehab',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'نوع التأهيل',
            fieldKey: 'rehabType',
            items: DrinkingWaterOptions.rehabTypes,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'حماية الضربة المائية',
            fieldKey: 'waterHammerProtection',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'كفاءة حماية الضربة المائية',
            fieldKey: 'waterHammerEfficiency',
            items: DrinkingWaterOptions.efficiencies,
            values: values,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
