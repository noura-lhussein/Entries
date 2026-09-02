import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../domain/entities/ore_product_option.dart';
import 'geology_ore_card.dart';
import 'geology_ore_form_models.dart';

class GeologyOreSection extends StatelessWidget {
  const GeologyOreSection({
    super.key,
    required this.groups,
    required this.oreToAdd,
    required this.planYear,
    required this.onOreToAddChanged,
    required this.onAddOreGroup,
    required this.onRemoveOreGroup,
    required this.onAddTypeLine,
    required this.onRemoveTypeLine,
    required this.onH1Changed,
    required this.onChanged,
  });

  final List<OreProductGroup> groups;
  final String oreToAdd;
  final int planYear;
  final ValueChanged<String> onOreToAddChanged;
  final VoidCallback onAddOreGroup;
  final ValueChanged<int> onRemoveOreGroup;
  final ValueChanged<int> onAddTypeLine;
  final void Function(int gi, int li) onRemoveTypeLine;
  final ValueChanged<OreTypeLine> onH1Changed;
  final VoidCallback onChanged;

  List<String> get _availableOreNames {
    final used = groups
        .map((g) => g.productNameAr.trim())
        .where((n) => n.isNotEmpty)
        .toSet();
    return [
      for (final opt in kOreProductOptions)
        if (!used.contains(opt.nameAr)) opt.nameAr,
    ];
  }

  @override
  Widget build(BuildContext context) {
    final available = _availableOreNames;
    return SectionCard(
      title: 'إنتاج الخامات المعدنية',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'لكل خام يمكن إضافة أكثر من نوع تشغيل (ذاتي أو معهّد) مع وحدته (طن أو م3). العقود والاحتياطي مشتركان لنفس الخام.',
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              color: AppColors.textSecondary,
            ),
          ),
          SizedBox(height: 10.h),
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: oreToAdd.isEmpty ? null : oreToAdd,
                  decoration: const InputDecoration(
                    labelText: 'اختر خاماً…',
                    border: OutlineInputBorder(),
                  ),
                  items: [
                    for (final name in available)
                      DropdownMenuItem(value: name, child: Text(name)),
                  ],
                  onChanged: (v) => onOreToAddChanged(v ?? ''),
                ),
              ),
              SizedBox(width: 8.w),
              FilledButton(
                onPressed: oreToAdd.isEmpty ? null : onAddOreGroup,
                child: const Text('إضافة خام'),
              ),
            ],
          ),
          SizedBox(height: 12.h),
          ...List.generate(
            groups.length,
            (gi) => GeologyOreCard(
              group: groups[gi],
              planYear: planYear,
              onRemove: () => onRemoveOreGroup(gi),
              onAddTypeLine: () => onAddTypeLine(gi),
              onRemoveTypeLine: (li) => onRemoveTypeLine(gi, li),
              onH1Changed: onH1Changed,
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }
}
