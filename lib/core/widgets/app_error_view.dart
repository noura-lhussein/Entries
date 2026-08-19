import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_theme.dart';

/// Polished full-area error / empty state with optional retry.
class AppErrorView extends StatelessWidget {
  final String title;
  final String message;
  final VoidCallback? onRetry;
  final IconData icon;
  final bool isEmpty;

  const AppErrorView({
    super.key,
    this.title = 'تعذّر تحميل البيانات',
    required this.message,
    this.onRetry,
    this.icon = Icons.cloud_off_rounded,
    this.isEmpty = false,
  });

  factory AppErrorView.empty({
    Key? key,
    String title = 'لا توجد بيانات',
    String message = 'لم يُرجع الخادم أي بيانات للعرض حالياً.',
    VoidCallback? onRetry,
  }) {
    return AppErrorView(
      key: key,
      title: title,
      message: message,
      onRetry: onRetry,
      icon: Icons.inbox_outlined,
      isEmpty: true,
    );
  }

  @override
  Widget build(BuildContext context) {
    final accent = isEmpty ? AppColors.goldMid : AppColors.red2;
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 32.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72.r,
              height: 72.r,
              decoration: BoxDecoration(
                color: accent.withValues(alpha: 0.1),
                shape: BoxShape.circle,
                border: Border.all(color: accent.withValues(alpha: 0.25)),
              ),
              child: Icon(icon, size: 34.r, color: accent),
            ),
            SizedBox(height: 18.h),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 15.sp,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            SizedBox(height: 8.h),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 12.5.sp,
                height: 1.55,
                color: AppColors.textSecondary,
              ),
            ),
            if (onRetry != null) ...[
              SizedBox(height: 20.h),
              FilledButton.icon(
                onPressed: onRetry,
                icon: Icon(Icons.refresh_rounded, size: 18.r),
                label: Text(
                  'إعادة المحاولة',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.ink,
                  foregroundColor: Colors.white,
                  padding:
                      EdgeInsets.symmetric(horizontal: 22.w, vertical: 12.h),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10.r),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
