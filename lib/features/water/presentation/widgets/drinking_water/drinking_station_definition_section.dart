import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';

class DrinkingStationDefinitionSection extends StatelessWidget {
  const DrinkingStationDefinitionSection({
    super.key,
    required this.stationName,
    required this.registrationDate,
    required this.onDateChanged,
    required this.orgUnitController,
  });

  final String stationName;
  final DateTime registrationDate;
  final ValueChanged<DateTime> onDateChanged;
  final TextEditingController orgUnitController;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'تعريف المحطة',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Wrap(
            spacing: 8.w,
            runSpacing: 8.h,
            children: [
              InfoChip(label: stationName),
            ],
          ),
          SizedBox(height: 12.h),
          Text(
            stationName,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 18.sp,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 12.h),
          FieldsWrap(
            fields: [
              DatePickerField(
                label: 'سنة التسجيل',
                initialDate: registrationDate,
                onDateChanged: onDateChanged,
              ),
              AppTextField(
                label: 'الوحدة التنظيمية',
                controller: orgUnitController,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class InfoChip extends StatelessWidget {
  const InfoChip({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Container(
        padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
        decoration: BoxDecoration(
          color: AppColors.golden2,
          borderRadius: BorderRadius.circular(20.r),
          border: Border.all(color: AppColors.borderMid),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 11.sp,
            color: AppColors.forest1,
            fontWeight: FontWeight.w700,
          ),
        ),
      );
}
