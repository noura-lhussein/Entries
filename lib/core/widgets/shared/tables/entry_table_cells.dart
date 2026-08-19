import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class TableHeaderRow extends StatelessWidget {
  final List<({String label, int flex})> cols;
  const TableHeaderRow({super.key, required this.cols});

  @override
  Widget build(BuildContext context) => Container(
    color: AppColors.ink,
    padding: EdgeInsets.symmetric(horizontal: 0.w, vertical: 8.h),
    child: Row(children: cols.map((c) => Expanded(flex: c.flex,
      child: Text(c.label, textAlign: TextAlign.center,
        style: TextStyle(fontFamily: 'Cairo', fontSize: 10.sp, fontWeight: FontWeight.w700, color: AppColors.goldWarm)))).toList()),
  );
}

class TableCell extends StatelessWidget {
  final TextEditingController? controller;
  const TableCell({super.key, this.controller});

  @override
  Widget build(BuildContext context) => TextField(
    controller: controller,
    keyboardType: const TextInputType.numberWithOptions(decimal: true),
    textAlign: TextAlign.center,
    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
    decoration: InputDecoration(
      isDense: true,
      contentPadding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 8.h),
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(6.r), borderSide: BorderSide(color: AppColors.border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6.r), borderSide: BorderSide(color: AppColors.border)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(6.r), borderSide: BorderSide(color: AppColors.goldMid, width: 1.5)),
    ),
  );
}
