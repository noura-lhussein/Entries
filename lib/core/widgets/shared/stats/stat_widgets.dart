import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';
import '../chrome/forest_page_header.dart';

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
        boxShadow: AppDecorations.cardShadow,
      ),
      child: Stack(children: [
        PositionedDirectional(
          top: 0,
          bottom: 0,
          start: 0,
          child: Container(
            width: 3.w,
            decoration: BoxDecoration(
              gradient: AppColors.goldGradient,
              borderRadius: BorderRadiusDirectional.only(
                topStart: Radius.circular(12.r),
                bottomStart: Radius.circular(12.r),
              ),
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
                textAlign: TextAlign.start,
                softWrap: true),
              SizedBox(height: 4.h),
              Text(value,
                style: TextStyle(fontFamily: 'Cairo', fontSize: 17.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
                textAlign: TextAlign.start, overflow: TextOverflow.ellipsis),
              if (unit != null)
                Text(unit!,
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 9.sp, color: AppColors.textHint),
                  textAlign: TextAlign.start),
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
    return ForestPageHeader(title: title, subtitle: subtitle, icon: icon);
  }
}
