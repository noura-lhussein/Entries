import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class LoginInputDecoration {
  LoginInputDecoration._();

  static InputDecoration build({
    required String hint,
    required IconData icon,
    Widget? suffix,
  }) {
    final radius = BorderRadius.circular(12.r);
    final idle = BorderSide(color: const Color(0xFFD5DDD8), width: 1.2);

    return InputDecoration(
      hintText: hint,
      hintStyle: TextStyle(
        fontFamily: 'Cairo',
        fontSize: 13.sp,
        color: AppColors.inkSoft.withValues(alpha: 0.65),
      ),
      prefixIcon: Icon(icon, size: 20.r, color: AppColors.inkMid),
      suffixIcon: suffix,
      filled: true,
      fillColor: const Color(0xFFF4F7F5),
      contentPadding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 15.h),
      border: OutlineInputBorder(borderRadius: radius, borderSide: idle),
      enabledBorder: OutlineInputBorder(borderRadius: radius, borderSide: idle),
      focusedBorder: OutlineInputBorder(
        borderRadius: radius,
        borderSide: const BorderSide(color: AppColors.inkMid, width: 1.8),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: radius,
        borderSide: const BorderSide(color: AppColors.errorRed, width: 1.4),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: radius,
        borderSide: const BorderSide(color: AppColors.errorRed, width: 1.8),
      ),
      errorStyle: TextStyle(
        fontFamily: 'Cairo',
        fontSize: 11.sp,
        color: AppColors.errorRed,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}

class LoginFieldLabel extends StatelessWidget {
  const LoginFieldLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontFamily: 'Cairo',
        fontSize: 13.sp,
        fontWeight: FontWeight.w800,
        color: AppColors.inkDeep,
      ),
    );
  }
}
