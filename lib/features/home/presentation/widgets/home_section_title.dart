import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class HomeSectionTitle extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Color? accent;
  const HomeSectionTitle({
    super.key,
    required this.title,
    this.subtitle,
    this.accent,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            Container(
              height: 16.r,
              width: 3.w,
              decoration: BoxDecoration(
                color: accent ?? AppColors.goldMid,
                borderRadius: BorderRadius.circular(2.r),
              ),
            ),
            SizedBox(width: 7.w),
            Text(
              title,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 15.sp,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
        if (subtitle != null) ...[
          SizedBox(height: 4.h),
          Text(
            subtitle!,
            textAlign: TextAlign.start,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              color: AppColors.textHint,
            ),
          ),
        ],
      ],
    );
  }
}
