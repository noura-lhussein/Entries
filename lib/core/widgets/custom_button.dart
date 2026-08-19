import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_theme.dart';

class CustomButton extends StatelessWidget {
  const CustomButton({
    super.key,
    this.fillColor = AppColors.forest,
    this.isFilled = true,
    this.labelColor = AppColors.forest,
    required this.label,
    this.onTap,
  });

  final Color fillColor;
  final bool isFilled;
  final Color labelColor;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48.h.clamp(44.0, 56.0),
      child: Material(
        color: isFilled ? fillColor : Colors.transparent,
        borderRadius: BorderRadius.circular(10.r),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10.r),
          child: Container(
            alignment: Alignment.center,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10.r),
              border: Border.all(color: fillColor),
            ),
            child: Text(
              label,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 14.sp,
                fontWeight: FontWeight.w700,
                color: isFilled ? Colors.white : labelColor,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
