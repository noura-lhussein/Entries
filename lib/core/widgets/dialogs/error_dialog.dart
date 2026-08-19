import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../theme/app_theme.dart';
import '../custom_button.dart';
import 'custom_dialog.dart';

class ErrorDialog {
  static void openDialog(BuildContext context, String? message) {
    showDialog<void>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => _ErrorDialogBody(message: message),
    );
  }
}

class _ErrorDialogBody extends StatelessWidget {
  const _ErrorDialogBody({this.message});

  final String? message;

  @override
  Widget build(BuildContext context) {
    final text = (message == null || message!.trim().isEmpty)
        ? 'يوجد مشكلة'
        : message!.trim();
    final maxMessageHeight = MediaQuery.sizeOf(context).height * 0.35;

    return CustomDialog(
      icon: Icons.error_outline_rounded,
      color: AppColors.errorRed,
      content: Padding(
        padding: EdgeInsets.fromLTRB(20.w, 36.h, 20.w, 16.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ConstrainedBox(
              constraints: BoxConstraints(maxHeight: maxMessageHeight),
              child: SingleChildScrollView(
                child: Text(
                  text,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                    height: 1.45,
                  ),
                ),
              ),
            ),
            SizedBox(height: 20.h),
            CustomButton(
              label: 'إغلاق',
              fillColor: AppColors.ink,
              onTap: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      ),
    );
  }
}
