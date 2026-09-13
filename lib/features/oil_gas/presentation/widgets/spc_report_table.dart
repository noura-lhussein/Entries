import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'models/petroleum_data.dart';

class SpcReportTable extends StatelessWidget {
  final Map<String, TextEditingController> controllers;
  final DateTime reportDate;
  const SpcReportTable({
    super.key,
    required this.controllers,
    required this.reportDate,
  });

  static const _rowColors = [Color(0xffE8F5E9), Color(0xffE3F2FD), Color(0xffFFF8E1)];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final section in kOilMetricSections) ...[
          SectionCard(
            title: section.titleAr,
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
                  ...List.generate(
                    section.fields.length,
                    (i) => _buildRow(section.fields[i], i),
                  ),
                ],
              ),
            ),
          ),
          SizedBox(height: 12.h),
        ],
      ],
    );
  }

  Widget _buildRow(SpcRow r, int i) {
    final base = _rowColors[r.colorIndex];
    final bg = i.isEven ? base : Color.lerp(base, Colors.white, 0.5)!;
    return Container(
      decoration: BoxDecoration(
        color: bg,
        border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            flex: 5,
            child: Text(
              fuelSalesLabel(r, reportDate),
              textAlign: TextAlign.start,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 10.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 3.w),
              child: TableCell(controller: controllers[r.key]),
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              r.unit,
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
