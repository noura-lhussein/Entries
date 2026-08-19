import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import 'models/electricity_fields_data.dart';

class HydraulicEnergySection extends StatelessWidget {
  final Map<String, TextEditingController> controllers;
  const HydraulicEnergySection({super.key, required this.controllers});

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'معلومات السدود',
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: kHydraulicDams
            .map(
              (dam) => Container(
                margin: EdgeInsets.only(bottom: 10.h),
                padding: EdgeInsets.all(10.r),
                decoration: BoxDecoration(
                  color: AppColors.golden3,
                  borderRadius: BorderRadius.circular(8.r),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      dam.nameAr,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.forest1,
                      ),
                    ),
                    SizedBox(height: 8.h),
                    FieldsWrap(
                      fields: kHydraulicFields
                          .map(
                            (f) => AppTextField(
                              label: f.label,
                              controller: controllers['${dam.code}_${f.key}'],
                              hint: '0',
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                      decimal: true),
                            ),
                          )
                          .toList(),
                    ),
                  ],
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
