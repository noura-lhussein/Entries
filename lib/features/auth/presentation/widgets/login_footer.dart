import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';

class LoginFooter extends StatelessWidget {
  const LoginFooter({super.key});

  @override
  Widget build(BuildContext context) {
    return Text(
      'الجمهورية العربية السورية  ·  وزارة الطاقة',
      textAlign: TextAlign.center,
      style: TextStyle(
        fontFamily: 'Cairo',
        fontSize: 11.5.sp,
        fontWeight: FontWeight.w600,
        color: AppColors.goldLight.withValues(alpha: 0.85),
        letterSpacing: 0.2,
      ),
    );
  }
}
