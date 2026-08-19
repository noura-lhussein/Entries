import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import 'models/electricity_fields_data.dart';

class GovernoratesConsumptionTable extends StatelessWidget {
  final Map<String, TextEditingController> consumedControllers;
  final Map<String, TextEditingController> allocatedControllers;
  const GovernoratesConsumptionTable({
    super.key,
    required this.consumedControllers,
    required this.allocatedControllers,
  });

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'استهلاك المحافظات',
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8.r),
          border: Border.all(color: AppColors.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TableHeaderRow(cols: [
              (label: 'المحافظة', flex: 4),
              (label: 'الطاقة المستهلكة', flex: 3),
              (label: 'الطاقة المخصصة', flex: 3),
            ]),
            ...List.generate(
              kGovernorates.length,
              (i) => _row(kGovernorates[i], i),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(NamedCode gov, int i) => Container(
        decoration: BoxDecoration(
          color: i.isEven ? AppColors.golden3 : Colors.white,
          border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5)),
        ),
        padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
        child: Row(children: [
          Expanded(
            flex: 4,
            child: Text(
              gov.nameAr,
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
              child: TableCell(controller: consumedControllers[gov.code]),
            ),
          ),
          SizedBox(width: 4.w),
          Expanded(
            flex: 3,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 3.w),
              child: TableCell(controller: allocatedControllers[gov.code]),
            ),
          ),
        ]),
      );
}
