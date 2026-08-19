import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String? unit;
  const StatCard({super.key, required this.label, required this.value, this.unit});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(0.w, 2.h, 0.w, 2.h),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: AppColors.border),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha:0.03), blurRadius: 4, offset: const Offset(0, 1))],
      ),
      child: Stack(children: [
        Positioned(top: 0, bottom: 0, right: 0,
          child: Container(
            width: 3.w,
            decoration: BoxDecoration(
              gradient: AppColors.goldGradient,
              borderRadius: BorderRadius.only(topRight: Radius.circular(12.r), bottomRight: Radius.circular(12.r)),
            ),
          ),
        ),
       
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                style: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, height: 1.35, color: AppColors.textHint, fontWeight: FontWeight.w500),
                textAlign: TextAlign.right,
                softWrap: true),
              SizedBox(height: 4.h),
              Text(value,
                style: TextStyle(fontFamily: 'Cairo', fontSize: 17.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
                textAlign: TextAlign.right, overflow: TextOverflow.ellipsis),
              if (unit != null)
                Text(unit!,
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 9.sp, color: AppColors.textHint),
                  textAlign: TextAlign.right),
            ],
          ),
        ),
      ]),
    );
  }
}

class StatsGrid extends StatelessWidget {
  final List<({String label, String value, String? unit})> items;
  final int crossAxisCount;
  const StatsGrid({super.key, required this.items, this.crossAxisCount = 2});

  @override
  Widget build(BuildContext context) {
    final rows = <Widget>[];
    for (var i = 0; i < items.length; i += crossAxisCount) {
      final row = items.sublist(i, (i + crossAxisCount).clamp(0, items.length));
      rows.add(IntrinsicHeight(
        child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          for (var j = 0; j < row.length; j++) ...[
            if (j > 0) SizedBox(width: 8.w),
            Expanded(child: StatCard(label: row[j].label, value: row[j].value, unit: row[j].unit)),
          ],
          if (row.length < crossAxisCount)
            ...List.generate(crossAxisCount - row.length, (_) => Expanded(child: const SizedBox())),
        ]),
      ));
      if (i + crossAxisCount < items.length) rows.add(SizedBox(height: 8.h));
    }
    return Column(mainAxisSize: MainAxisSize.min, children: rows);
  }
}

class GradientHeaderCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  const GradientHeaderCard({super.key, required this.title, required this.subtitle, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.r),
      decoration: BoxDecoration(
        gradient: AppColors.cardForestGradient,
        borderRadius: BorderRadius.circular(14.r),
      ),
      child: Row(children: [
      
        Container(
          width: 42.r, height: 42.r,
          decoration: BoxDecoration(
            color: AppColors.goldWarm.withValues(alpha:0.12),
            borderRadius: BorderRadius.circular(10.r),
            border: Border.all(color: AppColors.goldWarm.withValues(alpha:0.25)),
          ),
          child: Icon(icon, color: AppColors.goldWarm, size: 22.r),
        ),
      SizedBox(width: 12.w),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: TextStyle(fontFamily: 'Cairo', fontSize: 15.sp, fontWeight: FontWeight.w800, color: Colors.white)),
            SizedBox(height: 3.h),
            Text(subtitle, style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, color: Colors.white.withValues(alpha:0.55)), maxLines: 2),
          ]),
        ),
          ]),
    );
  }
}
