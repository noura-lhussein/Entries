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
    final v = value?.trim();
    if (v == null || v.isEmpty) return null;
    if (v.length >= 10 && v[4] == '-' && v[7] == '-') {
      return DateTime.tryParse(v.substring(0, 10));
    }
    final slash = RegExp(r'^(\d{1,2})[/.](\d{1,2})[/.](\d{4})$').firstMatch(v);
    if (slash != null) {
      return DateTime(
        int.parse(slash.group(3)!),
        int.parse(slash.group(2)!),
        int.parse(slash.group(1)!),
      );
    }
    return DateTime.tryParse(v);
  }

  String _iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  String _ar(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  @override
  Widget build(BuildContext context) {
    final parsed = _parsed;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
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
            textAlign: TextAlign.right,
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
                    if (picked != null) onChanged(_iso(picked));
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
                children: [
                  Expanded(
                    child: Text(
                      parsed == null ? 'اختر التاريخ' : _ar(parsed),
                      textAlign: TextAlign.right,
                      textDirection: parsed == null
                          ? TextDirection.rtl
                          : TextDirection.ltr,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 13.sp,
                        color: parsed == null
                            ? AppColors.textHint
                            : AppColors.textPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  SizedBox(width: 10.w),
                  Icon(
                    Icons.calendar_today_outlined,
                    size: 15.r,
                    color: AppColors.textHint,
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
