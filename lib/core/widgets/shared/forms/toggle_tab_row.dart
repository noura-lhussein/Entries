import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class ToggleTabRow extends StatelessWidget {
  final bool isDailyEntry;
  final ValueChanged<bool> onChanged;
  const ToggleTabRow({super.key, required this.isDailyEntry, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.goldWash,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: AppColors.border),
      ),
      padding: EdgeInsets.all(3.r),
      child: Row(children: [
        _Seg(label: 'إدخال يومي',    icon: Icons.edit_outlined,           isActive: isDailyEntry,  onTap: () => onChanged(true)),
        SizedBox(width: 3.w),
        _Seg(label: 'استيراد ملفات', icon: Icons.upload_file_outlined,    isActive: !isDailyEntry, onTap: () => onChanged(false)),
      ]),
    );
  }
}

class _Seg extends StatelessWidget {
  final String label; final IconData icon; final bool isActive; final VoidCallback onTap;
  const _Seg({required this.label, required this.icon, required this.isActive, required this.onTap});

  @override
  Widget build(BuildContext context) => Expanded(
    child: GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: EdgeInsets.symmetric(vertical: 9.h),
        decoration: BoxDecoration(
          color: isActive ? AppColors.ink : Colors.transparent,
          borderRadius: BorderRadius.circular(7.r),
        ),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, size: 13.r, color: isActive ? AppColors.goldWarm : AppColors.textHint),
          SizedBox(width: 5.w),
          Text(label, style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp, fontWeight: FontWeight.w700,
            color: isActive ? AppColors.goldWarm : AppColors.textHint)),
        ]),
      ),
    ),
  );
}
