import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/theme/app_theme.dart';

class PetroleumHeader extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  const PetroleumHeader({
    super.key,
    required this.title,
    required this.subtitle,
    this.icon = Icons.oil_barrel_outlined,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.r),
      decoration: BoxDecoration(
        gradient: AppColors.cardForestGradient,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: TextStyle(fontFamily: 'Cairo', fontSize: 16.sp, fontWeight: FontWeight.w800, color: Colors.white)),
          SizedBox(height: 3.h),
          Text(subtitle, style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, color: Colors.white70)),
        ])),
        SizedBox(width: 12.w),
        Container(
          padding: EdgeInsets.all(10.r),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha:0.1), borderRadius: BorderRadius.circular(8.r)),
          child: Icon(icon, color: AppColors.golden1, size: 28.r),
        ),
      ]),
    );
  }
}
