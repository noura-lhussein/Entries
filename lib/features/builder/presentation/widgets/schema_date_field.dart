import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class SchemaDateField extends StatelessWidget {
  final String label;
  final String? value;
  final ValueChanged<String> onChanged;
  final bool enabled;
  final bool required;

  const SchemaDateField({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.enabled = true,
    this.required = false,
  });

  DateTime? get _parsed {
    final v = value;
    if (v == null || v.length < 10) return null;
    return DateTime.tryParse(v.substring(0, 10));
  }

  String _fmt(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final parsed = _parsed;
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
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: !enabled
                ? null
                : () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: parsed ?? DateTime.now(),
                      firstDate: DateTime(1970),
                      lastDate: DateTime(2099),
                      locale: const Locale('ar'),
                      builder: (ctx, child) => Theme(
                        data: Theme.of(ctx).copyWith(
                          colorScheme: const ColorScheme.light(
                            primary: AppColors.inkMid,
                            onPrimary: Colors.white,
                          ),
                        ),
                        child: child!,
                      ),
                    );
                    if (picked != null) onChanged(_fmt(picked));
                  },
            borderRadius: BorderRadius.circular(8.r),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
              decoration: BoxDecoration(
                color: enabled ? AppColors.goldWash : AppColors.cream,
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(
                    Icons.calendar_today_outlined,
                    size: 15.r,
                    color: AppColors.textHint,
                  ),
                  Text(
                    parsed == null ? 'اختر التاريخ' : _fmt(parsed),
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 13.sp,
                      color: parsed == null
                          ? AppColors.textHint
                          : AppColors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
