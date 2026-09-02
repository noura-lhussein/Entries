import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../bloc/water_feedback.dart';

void showWaterSnack(
  BuildContext context,
  String message, {
  bool ok = true,
}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        message,
        style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
      ),
      backgroundColor: ok ? AppColors.forest1 : AppColors.red2,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
    ),
  );
}

Future<bool> confirmWaterClear(BuildContext context) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('تأكيد المسح', style: TextStyle(fontFamily: 'Cairo')),
      content: const Text(
        'هل تريد مسح البيانات المستوردة لهذا القسم؟',
        style: TextStyle(fontFamily: 'Cairo'),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: const Text('إلغاء'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('مسح'),
        ),
      ],
    ),
  );
  return ok == true;
}

void listenWaterFeedback(BuildContext context, WaterFeedback? previous, WaterFeedback? next) {
  if (next == null || next.id == previous?.id) return;
  showWaterSnack(context, next.message, ok: next.isSuccess);
}
