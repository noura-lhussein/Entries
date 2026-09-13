import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../domain/entities/ore_product_option.dart';
import 'geology_ore_form_models.dart';
import 'geology_ore_type_line.dart';

class GeologyOreCard extends StatelessWidget {
  const GeologyOreCard({
    super.key,
    required this.group,
    required this.planYear,
    required this.onRemove,
    required this.onAddTypeLine,
    required this.onRemoveTypeLine,
    required this.onH1Changed,
    required this.onChanged,
  });

  final OreProductGroup group;
  final int planYear;
  final VoidCallback onRemove;
  final VoidCallback onAddTypeLine;
  final ValueChanged<int> onRemoveTypeLine;
  final ValueChanged<OreTypeLine> onH1Changed;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final productItems = {
      ...kOreProductOptions.map((o) => o.nameAr),
      if (group.productNameAr.isNotEmpty) group.productNameAr,
    }.toList();
    return Container(
      margin: EdgeInsets.only(bottom: 12.h),
      padding: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: AppColors.golden3,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue:
                      group.productNameAr.isEmpty ? null : group.productNameAr,
                  decoration: const InputDecoration(
                    labelText: 'نوع المنتج',
                    border: OutlineInputBorder(),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  items: [
                    for (final name in productItems)
                      DropdownMenuItem(value: name, child: Text(name)),
                  ],
                  onChanged: (name) {
                    if (name == null) return;
                    final found = findOreProduct(name);
                    group.productNameAr = name;
                    group.productNameEn = found?.nameEn ?? '';
                    onChanged();
                  },
                ),
              ),
              IconButton(
                onPressed: onRemove,
                icon: Icon(Icons.close, color: AppColors.red2, size: 20.r),
                tooltip: 'حذف الخام',
              ),
            ],
          ),
          SizedBox(height: 8.h),
          ...List.generate(
            group.lines.length,
            (li) => GeologyOreTypeLine(
              line: group.lines[li],
              planYear: planYear,
              lineIndex: li,
              onRemove: () => onRemoveTypeLine(li),
              onH1Changed: onH1Changed,
              onChanged: onChanged,
            ),
          ),
          Align(
            alignment: AlignmentDirectional.centerStart,
            child: TextButton(
              onPressed: onAddTypeLine,
              child: const Text('+ نوع'),
            ),
          ),
          AppTextField(
            label: 'عدد العقود',
            controller: group.contractsCtrl,
            keyboardType: TextInputType.number,
          ),
          SizedBox(height: 8.h),
          AppTextField(
            label: 'الاحتياطي (طن)',
            controller: group.reserveCtrl,
            maxLines: 3,
          ),
        ],
      ),
    );
  }
}
