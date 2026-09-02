import 'package:flutter/material.dart';

import '../widgets/models/electricity_fields_data.dart';

class ElectricityFormControllers {
  ElectricityFormControllers()
      : fieldCtrls = {
          for (final key in {
            for (final f in kAllElectricityMetricFields) f.key,
          })
            key: TextEditingController(),
        },
        consumedCtrls = {
          for (final g in kGovernorates) g.code: TextEditingController(),
        },
        allocatedCtrls = {
          for (final g in kGovernorates) g.code: TextEditingController(),
        },
        tankCtrls = {
          for (final t in kFuelTanks) t.code: TextEditingController(),
        },
        tankMaxCtrls = {
          for (final t in kFuelTanks)
            t.code: TextEditingController(
              text: '${t.maxCapacity?.toInt() ?? ''}',
            ),
        },
        hydraulicCtrls = {
          for (final dam in kHydraulicDams)
            for (final f in kHydraulicFields)
              '${dam.code}_${f.key}': TextEditingController(),
        },
        arabicNotesCtrl = TextEditingController(),
        englishNotesCtrl = TextEditingController();

  final Map<String, TextEditingController> fieldCtrls;
  final Map<String, TextEditingController> consumedCtrls;
  final Map<String, TextEditingController> allocatedCtrls;
  final Map<String, TextEditingController> tankCtrls;
  final Map<String, TextEditingController> tankMaxCtrls;
  final Map<String, TextEditingController> hydraulicCtrls;
  final TextEditingController arabicNotesCtrl;
  final TextEditingController englishNotesCtrl;

  void dispose() {
    for (final c in [
      ...fieldCtrls.values,
      ...consumedCtrls.values,
      ...allocatedCtrls.values,
      ...tankCtrls.values,
      ...tankMaxCtrls.values,
      ...hydraulicCtrls.values,
      arabicNotesCtrl,
      englishNotesCtrl,
    ]) {
      c.dispose();
    }
  }
}
