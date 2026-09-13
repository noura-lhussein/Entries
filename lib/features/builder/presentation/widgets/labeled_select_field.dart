import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/models/builder_models.dart';

class LabeledSelectField extends StatelessWidget {
  final String label;
  final String? value;
  final List<BuilderSelectOption> options;
  final ValueChanged<String?> onChanged;
  final bool enabled;
  final bool required;
  final bool clearable;
  final String hint;

  const LabeledSelectField({
    super.key,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.enabled = true,
    this.required = false,
    this.clearable = false,
    this.hint = 'اختر…',
  });

  static String _norm(String? raw) {
    if (raw == null) return '';
    final t = raw.trim();
    if (t.isEmpty) return '';
    final n = num.tryParse(t);
    if (n != null && n == n.roundToDouble()) return n.round().toString();
    return t;
  }

  List<BuilderSelectOption> get _unique {
    final seen = <String>{};
    return [
      for (final o in options)
        if (o.value.trim().isNotEmpty && seen.add(_norm(o.value))) o,
    ];
  }

  BuilderSelectOption? _match(List<BuilderSelectOption> items) {
    final raw = _norm(value);
    if (raw.isEmpty) return null;
    for (final o in items) {
      if (_norm(o.value) == raw) return o;
      if (_norm(o.id.toString()) == raw) return o;
      if (o.label.trim() == (value ?? '').trim()) return o;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final items = _unique;
    final matched = _match(items);
    final extras = <BuilderSelectOption>[];
    if (matched == null && value != null && value!.trim().isNotEmpty) {
      extras.add(BuilderSelectOption(
        id: int.tryParse(value!) ?? 0,
        value: value,
        label: value!,
      ));
    }
    final seen = <String>{};
    final all = <BuilderSelectOption>[];
    for (final o in [...extras, ...items]) {
      if (o.value.isEmpty) continue;
      if (seen.add(o.value)) all.add(o);
    }
    final current = matched?.value ??
        (all.any((o) => o.value == value) ? value : null);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (label.isNotEmpty)
          Text.rich(
            TextSpan(
              text: label,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textHint,
              ),
              children: [
                if (required)
                  TextSpan(
                    text: ' *',
                    style: TextStyle(color: AppColors.errorRed, fontSize: 11.sp),
                  ),
              ],
            ),
            textAlign: TextAlign.start,
          ),
        if (label.isNotEmpty) SizedBox(height: 5.h),
        InputDecorator(
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: enabled ? AppColors.goldWash : AppColors.cream,
            contentPadding:
                EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            enabled: enabled,
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: current,
              hint: Text(
                hint,
                textAlign: TextAlign.start,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  color: AppColors.textHint,
                ),
              ),
              isExpanded: true,
              isDense: true,
              alignment: AlignmentDirectional.centerStart,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                color: AppColors.textPrimary,
              ),
              icon: clearable && current != null && enabled
                  ? GestureDetector(
                      onTap: () => onChanged(null),
                      child: Icon(
                        Icons.close_rounded,
                        color: AppColors.inkSoft,
                        size: 16.r,
                      ),
                    )
                  : Icon(
                      Icons.keyboard_arrow_down_rounded,
                      color: AppColors.goldDeep,
                      size: 18.r,
                    ),
              items: all
                  .map(
                    (e) => DropdownMenuItem(
                      value: e.value,
                      alignment: AlignmentDirectional.centerStart,
                      child: Text(
                        e.label,
                        textAlign: TextAlign.start,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 13.sp,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  )
                  .toList(),
              onChanged: enabled ? onChanged : null,
            ),
          ),
        ),
      ],
    );
  }
}
