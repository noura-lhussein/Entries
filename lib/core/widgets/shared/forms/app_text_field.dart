import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class AppTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController? controller;
  final TextInputType? keyboardType;
  final String? suffixText;
  final int maxLines;
  final ValueChanged<String>? onChanged;
  final bool obscureText;
  const AppTextField({
    super.key, required this.label, this.hint, this.controller,
    this.keyboardType, this.suffixText, this.maxLines = 1, this.onChanged,
    this.obscureText = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, fontWeight: FontWeight.w600, color: AppColors.textHint),
          textAlign: TextAlign.right, maxLines: 1, overflow: TextOverflow.ellipsis),
        SizedBox(height: 5.h),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          maxLines: obscureText ? 1 : maxLines,
          obscureText: obscureText,
          onChanged: onChanged,
          textAlign: TextAlign.right,
          textDirection: TextDirection.rtl,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.textPrimary),
          decoration: InputDecoration(
            hintText: hint,
            isDense: true,
            contentPadding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
            suffixText: suffixText,
            suffixStyle: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, color: AppColors.textHint),
          ),
        ),
      ],
    );
  }
}
