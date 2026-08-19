import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class DuplicateNote extends StatelessWidget {
  const DuplicateNote({super.key});
  @override
  Widget build(BuildContext context) => Row(children: [
    Icon(Icons.info_outline_rounded, size: 12.r, color: AppColors.textHint),
    SizedBox(width: 5.w),
    Expanded(child: Text(
      'إذا وُجد سجل لنفس المفتاح (التاريخ + المحطة) سيتم تحديثه.',
      style: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, color: AppColors.textHint, fontStyle: FontStyle.italic),
      textAlign: TextAlign.right)),
  ]);
}
