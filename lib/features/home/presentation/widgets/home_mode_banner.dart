import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class HomeModeBanner extends StatelessWidget {
  final Color accent;
  const HomeModeBanner({
    super.key,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 11.h),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: accent.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(
            Icons.edit_note_rounded,
            size: 18.r,
            color: accent,
          ),
          SizedBox(width: 8.w),
          Expanded(
            child: Text(
              'أنت في تطبيق قسم الإدخال — نماذج الإدخال اليومية للقطاعات.',
              textAlign: TextAlign.right,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.5.sp,
                fontWeight: FontWeight.w700,
                color: accent,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
