import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import 'models/electricity_fields_data.dart';

class FuelTanksTable extends StatelessWidget {
  final Map<String, TextEditingController> currentStockControllers;
  final Map<String, TextEditingController> maxCapacityControllers;
  const FuelTanksTable({
    super.key,
    required this.currentStockControllers,
    required this.maxCapacityControllers,
  });

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'خزانات الوقود',
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
              (label: 'المحطة', flex: 4),
              (label: 'المخزون الحالي', flex: 3),
              (label: 'السعة القصوى', flex: 3),
            ]),
            ...List.generate(kFuelTanks.length, (i) => _row(kFuelTanks[i], i)),
          ],
        ),
      ),
    );
  }

  Widget _row(NamedCode tank, int i) {
    return Container(
      decoration: BoxDecoration(
        color: i.isEven ? AppColors.golden3 : Colors.white,
        border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5)),
      ),
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
      child: Row(children: [
        Expanded(
          flex: 4,
          child: Text(
            tank.nameAr,
            textAlign: TextAlign.start,
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
            child: TableCell(controller: currentStockControllers[tank.code]),
          ),
        ),
        Expanded(
          flex: 3,
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 3.w),
            child: TableCell(controller: maxCapacityControllers[tank.code]),
          ),
        ),
      ]),
    );
  }
}
