import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../bloc/geology_feedback.dart';

void showGeologySnack(
  BuildContext context,
  String message, {
  bool ok = true,
  bool floating = true,
}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        message,
        style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
      ),
      backgroundColor: ok ? AppColors.forest1 : AppColors.red2,
      behavior: floating ? SnackBarBehavior.floating : SnackBarBehavior.fixed,
      shape: floating
          ? RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r))
          : null,
    ),
  );
}

void listenGeologyFeedback(BuildContext context, GeologyFeedback? next) {
  if (next == null) return;
  showGeologySnack(
    context,
    next.message,
    ok: next.isSuccess,
    floating: next.floating,
  );
}
