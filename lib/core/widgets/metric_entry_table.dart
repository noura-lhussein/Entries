import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class MetricEntryRow {
  final String label;
  final String unit;
  final TextEditingController controller;
  const MetricEntryRow({
    required this.label,
    required this.unit,
    required this.controller,
  });
}

/// Statement | value | unit table — matches moe-portal daily-report sections.
class MetricEntryTable extends StatelessWidget {
  final String title;
  final List<MetricEntryRow> rows;
  const MetricEntryTable({
    super.key,
    required this.title,
    required this.rows,
  });

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: title,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8.r),
          border: Border.all(color: AppColors.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TableHeaderRow(cols: const [
              (label: 'البيان', flex: 5),
              (label: 'القيمة', flex: 3),
              (label: 'الواحدة', flex: 2),
            ]),
            ...List.generate(rows.length, (i) => _row(rows[i], i)),
          ],
        ),
      ),
    );
  }

  Widget _row(MetricEntryRow row, int i) {
    return Container(
      decoration: BoxDecoration(
        color: i.isEven ? AppColors.golden3 : Colors.white,
        border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
      child: Row(
        children: [
          Expanded(
            flex: 5,
            child: Text(
              row.label,
              textAlign: TextAlign.right,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 3.w),
              child: TableCell(controller: row.controller),
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              row.unit,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 9.sp,
                color: AppColors.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
