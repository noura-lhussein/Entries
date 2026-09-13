import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../widgets/login_background.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.ink,
      body: Stack(
        fit: StackFit.expand,
        children: [
          const LoginBackground(),
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset(
                  'assets/images/h-logo.webp',
                  width: 250.w,
                  height: 80.h,
                  fit: BoxFit.contain,
                  filterQuality: FilterQuality.high,
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
                SizedBox(height: 12.h),
                Text(
                  'وزارة الطاقة',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w700,
                    color: AppColors.goldWarm,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
