import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/models/builder_models.dart';

class LabeledSelectField extends StatelessWidget {
  final String label;
  final String? value;
  final List<BuilderSelectOption> options;
  final ValueChanged<String?> onChanged;
  final bool enabled;
  final bool required;
  final String hint;

  const LabeledSelectField({
    super.key,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.enabled = true,
    this.required = false,
    this.hint = 'اختر…',
  });

  @override
  Widget build(BuildContext context) {
    final ids = options.map((e) => e.id.toString()).toSet();
    final current = (value != null && ids.contains(value)) ? value : null;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label.isNotEmpty)
          Text.rich(
            TextSpan(
              text: label,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textHint,
              ),
              children: [
                if (required)
                  TextSpan(
                    text: ' *',
                    style: TextStyle(color: AppColors.errorRed, fontSize: 11.sp),
                  ),
              ],
            ),
          ),
        if (label.isNotEmpty) SizedBox(height: 5.h),
        Container(
          decoration: BoxDecoration(
            color: enabled ? AppColors.goldWash : AppColors.cream,
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppColors.border),
          ),
          padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: current,
              hint: Text(
                hint,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  color: AppColors.textHint,
                ),
              ),
              isExpanded: true,
              isDense: true,
              alignment: Alignment.centerRight,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                color: AppColors.textPrimary,
              ),
              icon: Icon(
                Icons.keyboard_arrow_down_rounded,
                color: AppColors.textHint,
                size: 18.r,
              ),
              items: options
                  .map(
                    (e) => DropdownMenuItem(
                      value: e.id.toString(),
                      alignment: Alignment.centerRight,
                      child: Text(
                        e.label,
                        textAlign: TextAlign.right,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 13.sp,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  )
                  .toList(),
              onChanged: enabled ? onChanged : null,
            ),
          ),
        ),
      ],
    );
  }
}
