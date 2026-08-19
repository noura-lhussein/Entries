import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class LoginBrandHeader extends StatelessWidget {
  const LoginBrandHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Image.asset(
          'assets/images/h-logo.webp',
          width: 240.w,
          height: 72.h,
          fit: BoxFit.contain,
          filterQuality: FilterQuality.high,
        ),
        SizedBox(height: 20.h),
        Text(
          'بوابة معلومات وزارة الطاقة',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 22.sp,
            fontWeight: FontWeight.w800,
            color: Colors.white,
            height: 1.3,
          ),
        ),
        SizedBox(height: 6.h),
        Text(
          'قسم إدخال البيانات',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
            color: AppColors.goldWarm,
          ),
        ),
        SizedBox(height: 8.h),
        Text(
          'سجّل الدخول للوصول إلى حسابك',
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 13.sp,
            fontWeight: FontWeight.w500,
            color: AppColors.goldLight,
          ),
        ),
        SizedBox(height: 16.h),
        Container(
          width: 56.w,
          height: 3.h,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(3.r),
            gradient: const LinearGradient(
              colors: [AppColors.inkMid, AppColors.goldMid, AppColors.goldWarm],
            ),
          ),
        ),
      ],
    );
  }
}
