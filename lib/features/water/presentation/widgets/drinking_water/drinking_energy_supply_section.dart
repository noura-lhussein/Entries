import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';
import 'drinking_value_dropdown.dart';

class DrinkingEnergySupplySection extends StatelessWidget {
  const DrinkingEnergySupplySection({
    super.key,
    required this.values,
    required this.onChanged,
  });

  final Map<String, String> values;
  final void Function(String key, String value) onChanged;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'إمداد الطاقة',
      child: FieldsWrap(
        fields: [
          DrinkingValueDropdown(
            label: 'إمداد الشبكة العامة؟',
            fieldKey: 'publicGrid',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'هل يعمل توصيل الشبكة؟',
            fieldKey: 'gridConnectionWorks',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'كفاءة التوصيل الكهربائي',
            fieldKey: 'electricalConnectionEfficiency',
            items: DrinkingWaterOptions.conditions,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'كفاءة المحول',
            fieldKey: 'transformerEfficiency',
            items: DrinkingWaterOptions.conditions,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'كفاءة اللوحة الكهربائية',
            fieldKey: 'panelEfficiency',
            items: DrinkingWaterOptions.conditions,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'إنتاجية طاقة الشبكة',
            fieldKey: 'gridEnergyProductivity',
            items: const ['0%', '25%', '50%', '75%', '100%'],
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'طاقة شمسية متوفرة؟',
            fieldKey: 'solarAvailable',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'إنتاجية الطاقة الشمسية',
            fieldKey: 'solarProductivity',
            items: const ['غير محدد', '0%', '25%', '50%', '75%', '100%'],
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'كفاءة النظام الشمسي',
            fieldKey: 'solarSystemEfficiency',
            items: DrinkingWaterOptions.efficiencies,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'مولد متوفر؟',
            fieldKey: 'generatorAvailable',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'الحاجة لتركيب طاقة شمسية؟',
            fieldKey: 'needsSolarInstallation',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'مساحة متوفرة للطاقة الشمسية؟',
            fieldKey: 'solarSpaceAvailable',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
          DrinkingValueDropdown(
            label: 'مصدر طاقة بديل؟',
            fieldKey: 'alternativeEnergy',
            items: DrinkingWaterOptions.yesNo,
            values: values,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }
}
