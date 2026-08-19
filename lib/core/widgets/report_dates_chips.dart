import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_theme.dart';

/// Horizontal chips of available report dates from `report-dates/` API.
class ReportDatesChips extends StatelessWidget {
  final List<String> dates;
  final String? selected;
  final ValueChanged<String> onSelected;
  final Color accent;

  const ReportDatesChips({
    super.key,
    required this.dates,
    required this.selected,
    required this.onSelected,
    this.accent = AppColors.forest1,
  });

  @override
  Widget build(BuildContext context) {
    if (dates.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'تواريخ التقارير المتوفرة',
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 12.sp,
            fontWeight: FontWeight.w700,
            color: AppColors.textSecondary,
          ),
        ),
        SizedBox(height: 8.h),
        SizedBox(
          height: 36.h,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: dates.length,
            separatorBuilder: (_, _) => SizedBox(width: 6.w),
            itemBuilder: (context, i) {
              final d = dates[i];
              final sel = d == selected;
              return ChoiceChip(
                label: Text(
                  d,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                    color: sel ? accent : AppColors.textPrimary,
                  ),
                ),
                selected: sel,
                selectedColor: accent.withValues(alpha: 0.18),
                onSelected: (_) => onSelected(d),
                visualDensity: VisualDensity.compact,
              );
            },
          ),
        ),
      ],
    );
  }
}
