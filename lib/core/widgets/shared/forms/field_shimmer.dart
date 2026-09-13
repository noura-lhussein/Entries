import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:shimmer/shimmer.dart';
import '../../../theme/app_theme.dart';

class FieldShimmer extends StatelessWidget {
  final String label;
  const FieldShimmer({super.key, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textHint),
            textAlign: TextAlign.start),
        SizedBox(height: 5.h),
        Shimmer.fromColors(
          baseColor: AppColors.goldWash,
          highlightColor: Colors.white.withValues(alpha:0.5),
          child: Container(
            height: 44.h,
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.goldWash,
              borderRadius: BorderRadius.circular(8.r),
              border: Border.all(color: AppColors.border),
            ),
          ),
        ),
      ],
    );
  }
}
