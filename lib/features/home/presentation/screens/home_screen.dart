import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/utils/sector_registry.dart';
import '../widgets/home_founding_item.dart';
import '../widgets/home_hero_banner.dart';
import '../widgets/home_info_row.dart';
import '../widgets/home_mode_banner.dart';
import '../widgets/home_section_title.dart';
import '../widgets/home_sector_card.dart';

class HomeScreen extends StatelessWidget {
  final UserModel user;
  final ValueChanged<UserDepartment> onOpenSector;
  const HomeScreen({
    super.key,
    required this.user,
    required this.onOpenSector,
  });

  bool get _canEnter => user.isAdmin || user.canEnterData;

  @override
  Widget build(BuildContext context) {
    final modeAccent = AppColors.goldDeep;
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(16.w, 14.h, 16.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const HomeHeroBanner(),
          SizedBox(height: 18.h),
          HomeModeBanner(accent: modeAccent),
          if (!_canEnter) ...[
            SizedBox(height: 12.h),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
              decoration: BoxDecoration(
                color: AppColors.errorBg,
                borderRadius: BorderRadius.circular(12.r),
                border: Border.all(color: AppColors.errorRed.withValues(alpha: 0.25)),
              ),
              child: Text(
                'حسابك لا يملك صلاحية إدخال البيانات. هذا التطبيق مخصص لقسم الإدخال فقط.',
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.errorRed,
                ),
              ),
            ),
          ],
          SizedBox(height: 22.h),
          HomeSectionTitle(
            title: user.isAdmin
                ? 'كل القطاعات'
                : (user.sectors.length > 1 ? 'قطاعاتي' : 'قطاعي'),
            subtitle: 'اضغط على القطاع للانتقال إلى نماذج الإدخال اليومية.',
            accent: modeAccent,
          ),
          SizedBox(height: 12.h),
          for (final sector in user.accessibleSectors) ...[
            HomeSectorCard(
              info: sectorInfo(sector),
              modeAccent: modeAccent,
              onTap: _canEnter ? () => onOpenSector(sector) : () {},
            ),
            SizedBox(height: 10.h),
          ],
          SizedBox(height: 12.h),
          const HomeSectionTitle(title: 'التأسيس'),
          SizedBox(height: 10.h),
          Container(
            padding: EdgeInsets.all(14.r),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14.r),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'تأسست الوزارة نتيجة اندماج ثلاث وزارات سابقة:',
                  textAlign: TextAlign.right,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 12.5.sp,
                    color: AppColors.textSecondary,
                    height: 1.6,
                  ),
                ),
                SizedBox(height: 10.h),
                const HomeFoundingItem(label: 'وزارة النفط والثروة المعدنية'),
                SizedBox(height: 8.h),
                const HomeFoundingItem(label: 'وزارة الكهرباء'),
                SizedBox(height: 8.h),
                const HomeFoundingItem(label: 'وزارة الموارد المائية'),
              ],
            ),
          ),
          SizedBox(height: 22.h),
          const HomeSectionTitle(title: 'التفاصيل العامة'),
          SizedBox(height: 10.h),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14.r),
              border: Border.all(color: AppColors.border),
            ),
            child: const Column(
              children: [
                HomeInfoRow(label: 'تأسست', value: '29 مارس 2025'),
                HomeInfoDivider(),
                HomeInfoRow(label: 'المقر الرئيسي', value: 'دمشق، سوريا'),
                HomeInfoDivider(),
                HomeInfoRow(label: 'وزير الطاقة', value: 'م.محمد البشير'),
              ],
            ),
          ),
          SizedBox(height: 80.h),
        ],
      ),
    );
  }
}
