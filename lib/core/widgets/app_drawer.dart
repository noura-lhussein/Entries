import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../models/user_model.dart';
import '../theme/app_theme.dart';
import '../utils/sector_registry.dart';
import 'shared/chrome/user_photo_circle.dart';

class AppDrawer extends StatelessWidget {
  final UserModel user;
  final UserDepartment? activeSector;
  final String? activePage;
  final ValueChanged<UserDepartment> onSelectSector;
  final VoidCallback onHome;
  final VoidCallback? onMyData;
  final VoidCallback? onEnteredData;
  final VoidCallback? onProfile;
  final VoidCallback onLogout;

  const AppDrawer({
    super.key,
    required this.user,
    required this.activeSector,
    required this.onSelectSector,
    required this.onHome,
    required this.onLogout,
    this.activePage,
    this.onMyData,
    this.onEnteredData,
    this.onProfile,
  });

  @override
  Widget build(BuildContext context) {
    final headerGradient = AppColors.headerGradient;
    final modeAccent = AppColors.goldDeep;

    return Drawer(
      backgroundColor: AppColors.background,
      width: 300.w,
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: EdgeInsets.fromLTRB(
              16.w,
              MediaQuery.paddingOf(context).top + 18.h,
              16.w,
              18.h,
            ),
            decoration: BoxDecoration(
              gradient: headerGradient,
              border: Border(
                bottom: BorderSide(
                  color: AppColors.goldWarm.withValues(alpha: 0.45),
                  width: 1.5,
                ),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    UserPhotoCircle(
                      photoUrl: user.photoUrl,
                      initials: user.name.trim().isNotEmpty
                          ? user.name.characters.first
                          : '؟',
                      size: 48,
                      fontSize: 18,
                    ),
                    SizedBox(width: 12.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(user.name,
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontFamily: 'Cairo', fontSize: 14.5.sp, fontWeight: FontWeight.w800, color: Colors.white)),
                          SizedBox(height: 3.h),
                          Text(user.role,
                            maxLines: 1, overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, color: Colors.white70)),
                        ],
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 12.h),
                Wrap(spacing: 6.w, runSpacing: 6.h, children: [
                  _Chip(label: user.appRoleLabel, color: AppColors.goldMid),
                  _Chip(label: user.departmentLabel, color: Colors.white70),
                  _Chip(label: 'قسم الإدخال', color: AppColors.goldLight),
                ]),
              ],
            ),
          ),

          Expanded(
            child: SafeArea(
              top: false,
              child: ListView(
                padding: EdgeInsets.symmetric(vertical: 10.h),
                children: [
                  _DrawerSectionLabel(label: 'التنقّل'),
                  _DrawerTile(
                    icon: Icons.home_rounded,
                    label: 'الرئيسية',
                    isActive: activePage == 'home' ||
                        (activePage == null && activeSector == null),
                    accent: modeAccent,
                    onTap: () { Navigator.pop(context); onHome(); },
                  ),
                  if (user.isAdmin || user.canEnterData)
                    _DrawerTile(
                      icon: Icons.storage_outlined,
                      label: 'بياناتي',
                      isActive: activePage == 'myData',
                      accent: modeAccent,
                      onTap: () {
                        Navigator.pop(context);
                        onMyData?.call();
                      },
                    ),
                  if (user.isAdmin || user.canViewData || user.canEnterData)
                    _DrawerTile(
                      icon: Icons.table_rows_outlined,
                      label: 'البيانات المدخلة',
                      isActive: activePage == 'entered',
                      accent: modeAccent,
                      onTap: () {
                        Navigator.pop(context);
                        onEnteredData?.call();
                      },
                    ),

                  SizedBox(height: 10.h),
                  _DrawerSectionLabel(
                    label: user.isAdmin ? 'كل القطاعات' : (user.sectors.length > 1 ? 'قطاعاتي' : 'قطاعي'),
                  ),
                  for (final sector in user.accessibleSectors)
                    _DrawerTile(
                      icon: sectorInfo(sector).icon,
                      label: sectorInfo(sector).label,
                      isActive: activeSector == sector,
                      accent: modeAccent,
                      dotColor: sectorInfo(sector).color,
                      onTap: () { Navigator.pop(context); onSelectSector(sector); },
                    ),
                ],
              ),
            ),
          ),

            SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Divider(height: 1, color: AppColors.divider),
                  _DrawerSectionLabel(label: 'الحساب'),
                  _DrawerTile(
                    icon: Icons.person_outline_rounded,
                    label: 'الملف الشخصي',
                    isActive: activePage == 'profile',
                    accent: modeAccent,
                    onTap: () {
                      Navigator.pop(context);
                      onProfile?.call();
                    },
                  ),
                  _DrawerTile(
                    icon: Icons.logout_rounded,
                    label: 'تسجيل الخروج',
                    isActive: false,
                    accent: AppColors.burgundy,
                    labelColor: AppColors.burgundy,
                    onTap: () { Navigator.pop(context); onLogout(); },
                  ),
                  SizedBox(height: 8.h),
                ],
              ),
            ),
          ],
        ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  const _Chip({required this.label, required this.color});
  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 3.h),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha:0.10),
      borderRadius: BorderRadius.circular(20.r),
      border: Border.all(color: color.withValues(alpha:0.5)),
    ),
    child: Text(label, style: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, fontWeight: FontWeight.w700, color: color)),
  );
}

class _DrawerSectionLabel extends StatelessWidget {
  final String label;
  const _DrawerSectionLabel({required this.label});
  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.fromLTRB(16.w, 6.h, 16.w, 6.h),
    child: Align(
      alignment: AlignmentDirectional.centerStart,
      child: Text(label, style: TextStyle(fontFamily: 'Cairo', fontSize: 10.5.sp, fontWeight: FontWeight.w700, color: AppColors.textHint)),
    ),
  );
}

class _DrawerTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final Color accent;
  final Color? dotColor;
  final Color? labelColor;
  final VoidCallback onTap;
  const _DrawerTile({
    required this.icon, required this.label, required this.isActive,
    required this.accent, this.dotColor, this.labelColor, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 3.h),
      child: Material(
        color: isActive ? AppColors.goldWash : Colors.transparent,
        borderRadius: BorderRadius.circular(10.r),
        child: InkWell(
          borderRadius: BorderRadius.circular(10.r),
          onTap: onTap,
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
            child: Row(
              children: [
                if (isActive)
                  Container(
                    width: 3.w,
                    height: 16.h,
                    decoration: BoxDecoration(
                      gradient: AppColors.goldGradient,
                      borderRadius: BorderRadius.circular(2.r),
                    ),
                  )
                else
                  SizedBox(width: 3.w),
                SizedBox(width: 8.w),
                Icon(icon, size: 18.r, color: labelColor ?? (isActive ? accent : AppColors.textHint)),
                if (dotColor != null) ...[
                  SizedBox(width: 6.w),
                  Container(
                    width: 8.r,
                    height: 8.r,
                    decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                  ),
                ],
                SizedBox(width: 10.w),
                Expanded(
                  child: Text(label,
                    textAlign: TextAlign.start,
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp,
                      fontWeight: isActive ? FontWeight.w800 : FontWeight.w600,
                      color: labelColor ?? (isActive ? accent : AppColors.textPrimary))),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
