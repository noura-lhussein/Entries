import 'package:flutter/material.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../utils/drinking_water_options.dart';

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
          _dropdown(
            'إمداد الشبكة العامة؟',
            'publicGrid',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'هل يعمل توصيل الشبكة؟',
            'gridConnectionWorks',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'كفاءة التوصيل الكهربائي',
            'electricalConnectionEfficiency',
            DrinkingWaterOptions.conditions,
          ),
          _dropdown(
            'كفاءة المحول',
            'transformerEfficiency',
            DrinkingWaterOptions.conditions,
          ),
          _dropdown(
            'كفاءة اللوحة الكهربائية',
            'panelEfficiency',
            DrinkingWaterOptions.conditions,
          ),
          _dropdown('إنتاجية طاقة الشبكة', 'gridEnergyProductivity', const [
            '0%',
            '25%',
            '50%',
            '75%',
            '100%',
          ]),
          _dropdown(
            'طاقة شمسية متوفرة؟',
            'solarAvailable',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown('إنتاجية الطاقة الشمسية', 'solarProductivity', const [
            'غير محدد',
            '0%',
            '25%',
            '50%',
            '75%',
            '100%',
          ]),
          _dropdown(
            'كفاءة النظام الشمسي',
            'solarSystemEfficiency',
            DrinkingWaterOptions.efficiencies,
          ),
          _dropdown(
            'مولد متوفر؟',
            'generatorAvailable',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'الحاجة لتركيب طاقة شمسية؟',
            'needsSolarInstallation',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'مساحة متوفرة للطاقة الشمسية؟',
            'solarSpaceAvailable',
            DrinkingWaterOptions.yesNo,
          ),
          _dropdown(
            'مصدر طاقة بديل؟',
            'alternativeEnergy',
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
