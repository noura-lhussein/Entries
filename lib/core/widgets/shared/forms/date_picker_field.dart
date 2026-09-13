import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class DatePickerField extends StatefulWidget {
  final String label;
  final DateTime initialDate;
  final ValueChanged<DateTime> onDateChanged;
  const DatePickerField({super.key, required this.label, required this.initialDate, required this.onDateChanged});
  @override State<DatePickerField> createState() => _DatePickerFieldState();
}

class _DatePickerFieldState extends State<DatePickerField> {
  late DateTime _sel;
  @override void initState() { super.initState(); _sel = widget.initialDate; }
  String _fmt(DateTime d) => '${d.day.toString().padLeft(2,'0')}/${d.month.toString().padLeft(2,'0')}/${d.year}';

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(widget.label,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, fontWeight: FontWeight.w600, color: AppColors.textHint)),
        SizedBox(height: 5.h),
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () async {
              final p = await showDatePicker(
                context: context, initialDate: _sel,
                firstDate: DateTime(1970), lastDate: DateTime(2099),
                locale: const Locale('ar'),
                builder: (ctx, child) => Theme(
                  data: Theme.of(ctx).copyWith(
                    colorScheme: const ColorScheme.light(primary: AppColors.inkMid, onPrimary: Colors.white)),
                  child: child!),
              );
              if (p != null) { setState(() => _sel = p); widget.onDateChanged(p); }
            },
            borderRadius: BorderRadius.circular(8.r),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
              decoration: BoxDecoration(
                color: AppColors.goldWash,
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      _fmt(_sel),
                      textAlign: TextAlign.end,
                      textDirection: TextDirection.ltr,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 13.sp,
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  SizedBox(width: 10.w),
                  Icon(Icons.calendar_today_outlined, size: 15.r, color: AppColors.goldDeep),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
