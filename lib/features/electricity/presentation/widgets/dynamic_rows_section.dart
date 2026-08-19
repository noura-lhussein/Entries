import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';

/// rows, each made of [fieldLabels.length] text fields. Row add/remove is
/// driven by the bloc; the actual per-row TextEditingControllers are kept
/// locally here (keyed by row id) since raw text input doesn't belong in
/// bloc state.
class DynamicRowsSection extends StatefulWidget {
  final String title;
  final DynamicSectionType sectionType;
  final List<DynamicRow> rows;
  final List<String> fieldLabels;
  final String emptyMessage;

  const DynamicRowsSection({
    super.key,
    required this.title,
    required this.sectionType,
    required this.rows,
    required this.fieldLabels,
    required this.emptyMessage,
  });

  @override
  State<DynamicRowsSection> createState() => DynamicRowsSectionState();
}

class DynamicRowsSectionState extends State<DynamicRowsSection> {
  final Map<String, List<TextEditingController>> _controllers = {};

  /// Returns raw field values per row (same order as [fieldLabels]).
  List<List<String>> collectRows() {
    return [
      for (final row in widget.rows)
        (_controllers[row.id] ?? const []).map((c) => c.text.trim()).toList(),
    ];
  }

  List<TextEditingController> _controllersFor(DynamicRow row) {
    return _controllers.putIfAbsent(
      row.id,
      () => List.generate(
        widget.fieldLabels.length,
        (i) => TextEditingController(
          text: i < row.initialValues.length ? row.initialValues[i] : '',
        ),
      ),
    );
  }

  void _disposeRemovedRows() {
    final currentIds = widget.rows.map((r) => r.id).toSet();
    final staleIds =
        _controllers.keys.where((id) => !currentIds.contains(id)).toList();
    for (final id in staleIds) {
      for (final c in _controllers[id]!) {
        c.dispose();
      }
      _controllers.remove(id);
    }
  }

  @override
  void dispose() {
    for (final list in _controllers.values) {
      for (final c in list) {
        c.dispose();
      }
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    _disposeRemovedRows();
    return FormCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  widget.title,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w800,
                    color: AppColors.forest,
                  ),
                ),
              ),
              TextButton.icon(
                onPressed: () => context
                    .read<ElectricityBloc>()
                    .add(DynamicRowAdded(widget.sectionType)),
                icon: Icon(Icons.add, size: 16.r, color: AppColors.forest1),
                label: Text(
                  'إضافة صف',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 12.sp,
                    color: AppColors.forest1,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          if (widget.rows.isEmpty)
            Padding(
              padding: EdgeInsets.symmetric(vertical: 10.h),
              child: Text(
                widget.emptyMessage,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 12.sp,
                  color: AppColors.textSecondary,
                ),
              ),
            )
          else
            ...widget.rows.map(_buildRow),
        ],
      ),
    );
  }

  Widget _buildRow(DynamicRow row) {
    final ctrls = _controllersFor(row);
    return Container(
      margin: EdgeInsets.only(top: 10.h),
      padding: EdgeInsets.all(10.r),
      decoration: BoxDecoration(
        color: AppColors.golden3,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Wrap(
              spacing: 8.w,
              runSpacing: 8.h,
              children: List.generate(widget.fieldLabels.length, (i) {
                return SizedBox(
                  width: 150.w,
                  child: AppTextField(
                    label: widget.fieldLabels[i],
                    controller: ctrls[i],
                    hint: '',
                  ),
                );
              }),
            ),
          ),
          IconButton(
            onPressed: () => context
                .read<ElectricityBloc>()
                .add(DynamicRowRemoved(widget.sectionType, row.id)),
            icon: Icon(Icons.close, size: 18.r, color: AppColors.red2),
          ),
        ],
      ),
    );
  }
}
