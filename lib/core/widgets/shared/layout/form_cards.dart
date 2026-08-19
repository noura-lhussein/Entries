import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class FormCard extends StatelessWidget {
  final Widget child;
  const FormCard({super.key, required this.child});

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.all(14.r),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(14.r),
      border: Border.all(color: AppColors.border),
      boxShadow: [BoxShadow(color: Colors.black.withValues(alpha:0.04), blurRadius: 6, offset: const Offset(0, 2))],
    ),
    child: child,
  );
}

class SectionCard extends StatelessWidget {
  final String title;
  final Widget child;
  final Widget? trailing;
  const SectionCard({super.key, required this.title, required this.child, this.trailing});

  @override
  Widget build(BuildContext context) => FormCard(
    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Row(children: [
        if (trailing != null) ...[trailing!, SizedBox(width: 8.w)],
     
        Container(
          height: 16.r,
          width: 3.w,
          decoration: BoxDecoration(
            gradient: AppColors.goldGradient,
            borderRadius: BorderRadius.circular(2.r),
          ),
          margin: EdgeInsets.only(left: 7.w),
        ),
        Text(title, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
      ]),
      SizedBox(height: 12.h),
      child,
    ]),
  );
}

class FieldsWrap extends StatelessWidget {
  final List<Widget> fields;
  const FieldsWrap({super.key, required this.fields});

  @override
  Widget build(BuildContext context) {
    final rows = <Widget>[];
    for (var i = 0; i < fields.length; i += 2) {
      rows.add(Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: fields[i]),
        SizedBox(width: 10.w),
        Expanded(child: i + 1 < fields.length ? fields[i + 1] : const SizedBox()),
      ]));
      if (i + 2 < fields.length) rows.add(SizedBox(height: 12.h));
    }
    return Column(mainAxisSize: MainAxisSize.min, children: rows);
  }
}
