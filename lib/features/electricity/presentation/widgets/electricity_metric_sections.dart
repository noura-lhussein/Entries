import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/widgets/metric_entry_table.dart';
import 'models/electricity_fields_data.dart';

class ElectricityMetricSections extends StatelessWidget {
  const ElectricityMetricSections({super.key, required this.fieldCtrls});

  final Map<String, TextEditingController> fieldCtrls;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final section in kElectricityMetricSections)
          Padding(
            padding: EdgeInsets.only(bottom: 14.h),
            child: MetricEntryTable(
              title: section.titleAr,
              rows: [
                for (final f in section.fields)
                  MetricEntryRow(
                    label: f.label,
                    unit: f.unit,
                    controller: fieldCtrls[f.key]!,
                  ),
              ],
            ),
          ),
      ],
    );
  }
}
