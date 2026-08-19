import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';

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
          _dropdown('هل المحطة تعمل؟', 'isWorking', DrinkingWaterOptions.yesNo),
          AppTextField(
            label: 'سبب عدم التشغيل',
            controller: notOperatingReasonController,
          ),
          _dropdown(
            'حالة مبنى المحطة',
            'buildingStatus',
            DrinkingWaterOptions.conditions,
          ),
          _dropdown(
            'وجود إجراءات السلامة',
            'safetyProcedures',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'تأهيل سابق؟',
            'previousRehab',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'نوع التأهيل',
            'rehabType',
            DrinkingWaterOptions.rehabTypes,
          ),
          _dropdown(
            'حماية الضربة المائية',
            'waterHammerProtection',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'كفاءة حماية الضربة المائية',
            'waterHammerEfficiency',
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
