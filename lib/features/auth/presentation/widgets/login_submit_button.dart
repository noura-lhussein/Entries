import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class LoginSubmitButton extends StatelessWidget {
  const LoginSubmitButton({
    super.key,
    required this.onPressed,
    this.isLoading = false,
  });

  final VoidCallback onPressed;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52.h,
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        elevation: isLoading ? 2 : 8,
        shadowColor: AppColors.ink.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12.r),
        child: InkWell(
          onTap: isLoading ? null : onPressed,
          borderRadius: BorderRadius.circular(12.r),
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12.r),
              gradient: const LinearGradient(
                begin: Alignment.centerRight,
                end: Alignment.centerLeft,
                colors: [
                  AppColors.inkMid,
                  AppColors.inkDeep,
                  AppColors.ink,
                ],
                stops: [0.0, 0.55, 1.0],
              ),
              border: Border(
                top: BorderSide(
                  color: AppColors.goldWarm.withValues(alpha: 0.55),
                  width: 1.2,
                ),
              ),
            ),
            child: Center(
              child: isLoading
                  ? SizedBox(
                      width: 24.r,
                      height: 24.r,
                      child: const CircularProgressIndicator(
                        strokeWidth: 2.4,
                        color: AppColors.goldWarm,
                      ),
                    )
                  : Text(
                      'تسجيل الدخول',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 15.5.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.goldWarm,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
