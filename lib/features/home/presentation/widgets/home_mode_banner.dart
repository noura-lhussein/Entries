import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class HomeModeBanner extends StatelessWidget {
  final Color accent;
  const HomeModeBanner({
    super.key,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.goldWash,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: AppColors.borderMid),
      ),
      child: Row(
        children: [
          Container(
            width: 32.r,
            height: 32.r,
            decoration: BoxDecoration(
              color: AppColors.ink,
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Icon(
              Icons.edit_note_rounded,
              size: 18.r,
              color: AppColors.goldWarm,
            ),
          ),
          SizedBox(width: 10.w),
          Expanded(
            child: Text(
              'أنت في تطبيق قسم الإدخال — نماذج الإدخال اليومية للقطاعات.',
              textAlign: TextAlign.start,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.5.sp,
                fontWeight: FontWeight.w700,
                color: accent,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
