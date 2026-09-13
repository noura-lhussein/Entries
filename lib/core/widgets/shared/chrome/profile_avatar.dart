import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';
import '../../../models/user_model.dart';
import 'user_photo_circle.dart';

class ProfileAvatar extends StatelessWidget {
  final UserModel user;
  final VoidCallback onLogout;
  final VoidCallback? onProfile;
  const ProfileAvatar({
    super.key,
    required this.user,
    required this.onLogout,
    this.onProfile,
  });

  String get _initial {
    final raw = user.name.trim().isNotEmpty
        ? user.name.trim()
        : user.email.trim();
    if (raw.isEmpty) return '?';
    return raw.characters.first;
  }

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      onSelected: (v) {
        if (v == 'logout') onLogout();
        if (v == 'profile') onProfile?.call();
      },
      offset: Offset(0, 46.h),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14.r),
        side: const BorderSide(color: AppColors.border),
      ),
      color: AppColors.surface,
      elevation: 10,
      shadowColor: AppColors.ink.withValues(alpha: 0.18),
      child: UserPhotoCircle(
        photoUrl: user.photoUrl,
        initials: _initial,
        size: 36,
        fontSize: 13,
      ),
      itemBuilder: (_) => [
        PopupMenuItem(
          enabled: false,
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                user.name.trim().isEmpty ? user.email : user.name,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 2.h),
              Text(
                user.role,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 11.sp,
                  color: AppColors.textSecondary,
                ),
              ),
              SizedBox(height: 6.h),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: AppColors.goldPale,
                  borderRadius: BorderRadius.circular(20.r),
                  border: Border.all(color: AppColors.border),
                ),
                child: Text(
                  user.departmentLabel,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 10.sp,
                    color: AppColors.goldDeep,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
        const PopupMenuDivider(),
        PopupMenuItem(
          value: 'profile',
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
          child: Row(
            children: [
              Icon(Icons.person_outline_rounded, color: AppColors.goldDeep, size: 18.r),
              SizedBox(width: 8.w),
              Text(
                'الملف الشخصي',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  color: AppColors.ink,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'logout',
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
          child: Row(
            children: [
              Icon(Icons.logout_rounded, color: AppColors.burgundy, size: 18.r),
              SizedBox(width: 8.w),
              Text(
                'تسجيل الخروج',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  color: AppColors.burgundy,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
