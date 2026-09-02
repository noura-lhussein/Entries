import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';
import '../../../models/user_model.dart';

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
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.r)),
      color: AppColors.surface,
      elevation: 8,
      child: Container(
        width: 34.r,
        height: 34.r,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: AppColors.cardGoldenGradient,
          boxShadow: [BoxShadow(color: AppColors.golden.withValues(alpha:0.4), blurRadius: 6)],
        ),
        child: Center(
          child: Text(
            _initial,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, fontWeight: FontWeight.w800, color: Colors.white),
          ),
        ),
      ),
      itemBuilder: (_) => [
        PopupMenuItem(
          enabled: false,
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(user.name.trim().isEmpty ? user.email : user.name,
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
              SizedBox(height: 2.h),
              Text(user.role,
                style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, color: AppColors.textSecondary)),
              SizedBox(height: 2.h),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
                decoration: BoxDecoration(color: AppColors.golden2, borderRadius: BorderRadius.circular(20.r)),
                child: Text(user.departmentLabel,
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, color: AppColors.forest1, fontWeight: FontWeight.w600)),
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
              const Icon(Icons.person_outline_rounded, color: AppColors.ink, size: 18),
              SizedBox(width: 8.w),
              Text('الملف الشخصي',
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.ink, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
        PopupMenuItem(
          value: 'logout',
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
          child: Row(
            children: [
              const Icon(Icons.logout_rounded, color: AppColors.ink, size: 18),
              SizedBox(width: 8.w),
              Text('تسجيل الخروج',
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.ink, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ],
    );
  }
}
