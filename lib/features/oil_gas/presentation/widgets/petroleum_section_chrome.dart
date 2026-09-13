import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/theme/app_theme.dart';

class PetroleumSectionTitle extends StatelessWidget {
  final String title;
  final VoidCallback onAdd;
  const PetroleumSectionTitle({super.key, required this.title, required this.onAdd});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Text(title,
          style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
              color: AppColors.forest)),
      const Spacer(),
      TextButton.icon(
        onPressed: onAdd,
        icon: Icon(Icons.add, size: 15.r, color: AppColors.forest1),
        label: Text('إضافة صف',
            style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                color: AppColors.forest1,
                fontWeight: FontWeight.w700)),
      ),
    ]);
  }
}

class PetroleumDynCard extends StatelessWidget {
  final Widget child;
  final VoidCallback onRemove;
  const PetroleumDynCard({super.key, required this.child, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.only(top: 10.h),
      padding: EdgeInsets.all(10.r),
      decoration: BoxDecoration(
          color: AppColors.golden3,
          borderRadius: BorderRadius.circular(8.r),
          border: Border.all(color: AppColors.border)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: child),
        IconButton(
          onPressed: onRemove,
          icon: Icon(Icons.close, size: 16.r, color: AppColors.red2),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
      ]),
    );
  }
}

class PetroleumDropField extends StatelessWidget {
  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String?> onChanged;
  const PetroleumDropField(
      {super.key,
      required this.label,
      required this.value,
      required this.items,
      required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label,
          style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textSecondary)),
      SizedBox(height: 5.h),
      Container(
        decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppColors.border)),
        padding: EdgeInsets.symmetric(horizontal: 8.w),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: value,
            isExpanded: true,
            alignment: AlignmentDirectional.centerStart,
            style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 12.sp,
                color: AppColors.textPrimary),
            items: items
                .map((e) => DropdownMenuItem(
                      value: e,
                      alignment: AlignmentDirectional.centerStart,
                      child: Text(e,
                          textAlign: TextAlign.start,
                          overflow: TextOverflow.ellipsis),
                    ))
                .toList(),
            onChanged: onChanged,
          ),
        ),
      ),
    ]);
  }
}

class PetroleumEmptyHint extends StatelessWidget {
  final String message;
  const PetroleumEmptyHint(this.message, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 12.h),
      child: Text(message,
          textAlign: TextAlign.center,
          style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 12.sp,
              color: AppColors.textSecondary)),
    );
  }
}
