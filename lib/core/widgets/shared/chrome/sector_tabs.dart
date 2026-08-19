import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

/// Equal-width tabs with a full-tab underline so the active one is obvious.
class SectorTabBar extends StatelessWidget {
  final TabController controller;
  final List<Widget> tabs;
  const SectorTabBar({
    super.key,
    required this.controller,
    required this.tabs,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.golden2,
      child: TabBar(
        controller: controller,
        isScrollable: false,
        tabAlignment: TabAlignment.fill,
        indicatorSize: TabBarIndicatorSize.tab,
        dividerColor: AppColors.goldMid.withValues(alpha: 0.4),
        dividerHeight: 1,
        indicator: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.45),
          border: const Border(
            bottom: BorderSide(color: AppColors.forest, width: 3.5),
          ),
        ),
        labelColor: AppColors.forest,
        unselectedLabelColor: AppColors.textSecondary,
        overlayColor: WidgetStatePropertyAll(
          AppColors.forest.withValues(alpha: 0.06),
        ),
        labelPadding: EdgeInsets.symmetric(horizontal: 4.w),
        labelStyle: TextStyle(
          fontFamily: 'Cairo',
          fontWeight: FontWeight.w800,
          fontSize: 11.sp,
          height: 1.15,
        ),
        unselectedLabelStyle: TextStyle(
          fontFamily: 'Cairo',
          fontWeight: FontWeight.w500,
          fontSize: 11.sp,
          height: 1.15,
        ),
        tabs: tabs,
      ),
    );
  }
}

class SectorTab extends StatelessWidget {
  final IconData icon;
  final String label;
  const SectorTab({super.key, required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Tab(
      height: 52,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 16.r),
          SizedBox(height: 2.h),
          FittedBox(fit: BoxFit.scaleDown, child: Text(label, maxLines: 1)),
        ],
      ),
    );
  }
}

/// Pinned gold bar (same chrome as [SectorTabBar]) naming the current sector.
class SectorTitleBar extends StatelessWidget {
  final IconData icon;
  final String label;
  const SectorTitleBar({super.key, required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.golden2,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 11.h),
        decoration: const BoxDecoration(
          border: Border(
            bottom: BorderSide(color: AppColors.forest, width: 3.5),
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppColors.forest, size: 18.r),
            SizedBox(width: 8.w),
            Expanded(
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontWeight: FontWeight.w800,
                  fontSize: 13.sp,
                  height: 1.15,
                  color: AppColors.forest,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
