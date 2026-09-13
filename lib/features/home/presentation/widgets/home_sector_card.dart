import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/sector_registry.dart';

class HomeSectorCard extends StatelessWidget {
  final SectorInfo info;
  final Color modeAccent;
  final VoidCallback onTap;
  const HomeSectorCard({
    super.key,
    required this.info,
    required this.modeAccent,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(14.r),
        onTap: onTap,
        child: Container(
          padding: EdgeInsetsDirectional.fromSTEB(12.w, 12.h, 10.w, 12.h),
          decoration: AppDecorations.surfaceCard(),
          child: Row(
            children: [
              Container(
                width: 3.w,
                height: 36.h,
                decoration: BoxDecoration(
                  color: info.color,
                  borderRadius: BorderRadius.circular(2.r),
                ),
              ),
              SizedBox(width: 10.w),
              Container(
                width: 44.r,
                height: 44.r,
                decoration: BoxDecoration(
                  color: info.color.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(12.r),
                  border: Border.all(color: info.color.withValues(alpha: 0.28)),
                ),
                child: Icon(info.icon, color: info.color, size: 22.r),
              ),
              SizedBox(width: 12.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      info.label,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    SizedBox(height: 3.h),
                    Text(
                      'فتح نماذج الإدخال',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 11.sp,
                        fontWeight: FontWeight.w600,
                        color: modeAccent,
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(width: 8.w),
              Container(
                width: 28.r,
                height: 28.r,
                decoration: BoxDecoration(
                  color: AppColors.goldWash,
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.border),
                ),
                child: Icon(
                  Icons.arrow_forward_ios_rounded,
                  color: AppColors.goldDeep,
                  size: 14.r,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
