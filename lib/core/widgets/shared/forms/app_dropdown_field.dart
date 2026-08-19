import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class AppDropdownField extends StatelessWidget {
  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String?> onChanged;
  const AppDropdownField({super.key, required this.label, required this.value, required this.items, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, fontWeight: FontWeight.w600, color: AppColors.textHint),
          textAlign: TextAlign.right),
        SizedBox(height: 5.h),
        Container(
          decoration: BoxDecoration(
            color: AppColors.goldWash,
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppColors.border),
          ),
          padding: EdgeInsets.symmetric(horizontal: 10.w,vertical: 10.h),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value.isEmpty || !items.contains(value) ? null : value,
              hint: Text('اختر…',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.textHint)),
              isExpanded: true, isDense: true,
              alignment: Alignment.centerRight,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.textPrimary),
              icon: Icon(Icons.keyboard_arrow_down_rounded, color: AppColors.textHint, size: 18.r),
              items: items.map((e) => DropdownMenuItem(
                value: e, alignment: Alignment.centerRight,
                child: Text(e, textAlign: TextAlign.right, overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.textPrimary)))).toList(),
              onChanged: onChanged,
            ),
          ),
        ),
      ],
    );
  }
}
