import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../data/ore_product_catalog.dart';
import 'geology_ore_form_models.dart';

class GeologyOreTypeLine extends StatelessWidget {
  const GeologyOreTypeLine({
    super.key,
    required this.line,
    required this.planYear,
    required this.lineIndex,
    required this.onRemove,
    required this.onH1Changed,
    required this.onChanged,
  });

  final OreTypeLine line;
  final int planYear;
  final int lineIndex;
  final VoidCallback onRemove;
  final ValueChanged<OreTypeLine> onH1Changed;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: 10.h),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue:
                      line.productionType.isEmpty ? null : line.productionType,
                  decoration: const InputDecoration(
                    labelText: 'النوع',
                    border: OutlineInputBorder(),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  items: [
                    for (final opt in kProductionTypeOptions)
                      DropdownMenuItem(value: opt, child: Text(opt)),
                  ],
                  onChanged: (v) {
                    line.productionType = v ?? '';
                    onChanged();
                  },
                ),
              ),
              SizedBox(width: 8.w),
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: line.unit.isEmpty ? null : line.unit,
                  decoration: const InputDecoration(
                    labelText: 'الوحدة',
                    border: OutlineInputBorder(),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  items: [
                    for (final opt in kOreUnitOptions)
                      DropdownMenuItem(value: opt, child: Text(opt)),
                  ],
                  onChanged: (v) {
                    line.unit = v ?? '';
                    onChanged();
                  },
                ),
              ),
              if (lineIndex > 0)
                IconButton(
                  onPressed: onRemove,
                  icon: Icon(Icons.remove_circle_outline,
                      color: AppColors.red2, size: 20.r),
                ),
            ],
          ),
          SizedBox(height: 8.h),
          AppTextField(
            label: 'المخطط لكامل العام $planYear',
            controller: line.annualCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          SizedBox(height: 8.h),
          AppTextField(
            label: 'المخطط عن العام $planYear',
            controller: line.h1PlanCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            onChanged: (_) => onH1Changed(line),
          ),
          SizedBox(height: 8.h),
          AppTextField(
            label: 'المنفذ خلال العام $planYear',
            controller: line.h1ExecCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            onChanged: (_) => onH1Changed(line),
          ),
          SizedBox(height: 8.h),
          AppTextField(
            label: 'نسبة التنفيذ (%)',
            controller: line.pctCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
        ],
      ),
    );
  }
}
