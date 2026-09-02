import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class SaveButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final bool isLoading;
  final String label;
  const SaveButton({super.key, this.onPressed, this.isLoading = false, this.label = 'حفظ القراءة'});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity, height: 48.h,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: AppColors.actionGradient,
          borderRadius: BorderRadius.circular(10.r),
          border: Border(top: BorderSide(color: AppColors.goldWarm.withValues(alpha:0.4), width: 1)),
        ),
        child: ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent, shadowColor: Colors.transparent,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10.r)),
          ),
          child: isLoading
            ? SizedBox(height: 20.r, width: 20.r, child: CircularProgressIndicator(color: AppColors.goldWarm, strokeWidth: 2))
            : Text(label, textAlign: TextAlign.center, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, fontWeight: FontWeight.w700, color: AppColors.goldWarm)),
        ),
      ),
    );
  }
}
