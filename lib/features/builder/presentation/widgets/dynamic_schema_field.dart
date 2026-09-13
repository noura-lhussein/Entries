import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/datasources/builder_remote_data_source.dart';
import '../../data/models/builder_models.dart';
import '../bloc/data_entry_bloc.dart';
import '../bloc/data_entry_event.dart';
import '../bloc/data_entry_state.dart';
import 'labeled_select_field.dart';
import 'schema_date_field.dart';

class DynamicSchemaField extends StatelessWidget {
  final FormSchemaField field;
  const DynamicSchemaField({super.key, required this.field});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DataEntryBloc, DataEntryState>(
      buildWhen: (p, c) =>
          p.values[field.key] != c.values[field.key] ||
          p.fieldErrors[field.key] != c.fieldErrors[field.key] ||
          p.fieldWarnings[field.key] != c.fieldWarnings[field.key] ||
          p.entityOptions[field.type] != c.entityOptions[field.type] ||
          p.governorates != c.governorates ||
          p.districts != c.districts ||
          p.subdistricts != c.subdistricts ||
          p.communities != c.communities ||
          p.dateDuplicateWarning != c.dateDuplicateWarning,
      builder: (context, state) {
        final error = state.fieldErrors[field.key];
        final warning = state.fieldWarnings[field.key];
        final value = state.values[field.key] ?? '';
        final hasError = error != null && error.isNotEmpty;
        final hasWarn = !hasError && warning != null && warning.isNotEmpty;

        return Container(
          padding: EdgeInsets.symmetric(vertical: 2.h),
          decoration: BoxDecoration(
            border: BorderDirectional(
              start: BorderSide(
                width: 2.5,
                color: hasError
                    ? AppColors.errorRed
                    : hasWarn
                        ? AppColors.goldMid
                        : Colors.transparent,
              ),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildControl(context, state, value),
              if (field.helpAr != null && field.helpAr!.trim().isNotEmpty) ...[
                SizedBox(height: 4.h),
                Text(
                  field.helpAr!,
                  textAlign: TextAlign.start,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 10.sp,
                    color: AppColors.textHint,
                  ),
                ),
              ],
              if (hasError) ...[
                SizedBox(height: 4.h),
                Text(
                  error,
                  textAlign: TextAlign.start,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    color: AppColors.errorRed,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ] else if (hasWarn) ...[
                SizedBox(height: 4.h),
                Text(
                  warning,
                  textAlign: TextAlign.start,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    color: AppColors.goldDeep,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildControl(
    BuildContext context,
    DataEntryState state,
    String value,
  ) {
    final bloc = context.read<DataEntryBloc>();
    void commit(String v) => bloc.add(FieldValueChanged(field.key, v));
    void blur() => bloc.add(FieldBlurred(field.key));

    if (field.isBoolean) {
      final on = value == 'true' || value == '1';
      return SwitchListTile.adaptive(
        contentPadding: EdgeInsets.zero,
        dense: true,
        controlAffinity: ListTileControlAffinity.trailing,
        title: Text(
          field.labelAr,
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 13.sp,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        value: on,
        activeThumbColor: AppColors.successGreen,
        onChanged: field.readonly
            ? null
            : (v) {
                commit(v ? 'true' : 'false');
                blur();
              },
      );
    }

    if (field.isDate) {
      return SchemaDateField(
        label: field.labelAr,
        value: value,
        required: field.required && !field.readonly,
        enabled: !field.readonly,
        onChanged: (v) {
          commit(v);
          blur();
        },
      );
    }

    if (field.isDropdown) {
      return LabeledSelectField(
        label: field.labelAr,
        value: value.isEmpty ? null : value,
        required: field.required && !field.readonly,
        enabled: !field.readonly && _dropdownEnabled(state),
        options: _dropdownOptions(state),
        onChanged: (v) {
          commit(v ?? '');
          blur();
        },
      );
    }

    if (field.isFile) {
      return _FileField(
        field: field,
        value: value,
        onChanged: (v) {
          commit(v);
          blur();
        },
      );
    }

    return _BoundTextField(
      label: field.labelAr,
      value: value,
      unit: field.unitAr,
      required: field.required && !field.readonly,
      readonly: field.readonly,
      number: field.isNumber,
      multiline: field.isTextarea,
      onChanged: commit,
      onBlur: blur,
    );
  }

  bool _dropdownEnabled(DataEntryState state) {
    if (field.readonly) return false;
    if (field.type == 'district') {
      final city = state.schema?.fields.where((f) => f.type == 'city');
      if (city != null && city.isNotEmpty) {
        final key = city.first.key;
        return (state.values[key] ?? '').isNotEmpty;
      }
    }
    if (field.type == 'sub_district') {
      final dist = state.schema?.fields.where((f) => f.type == 'district');
      if (dist != null && dist.isNotEmpty) {
        return (state.values[dist.first.key] ?? '').isNotEmpty;
      }
    }
    if (field.type == 'community') {
      final sub = state.schema?.fields.where((f) => f.type == 'sub_district');
      if (sub != null && sub.isNotEmpty) {
        return (state.values[sub.first.key] ?? '').isNotEmpty;
      }
    }
    return true;
  }

  List<BuilderSelectOption> _dropdownOptions(DataEntryState state) {
    if (field.options.isNotEmpty) return field.options;
    switch (field.type) {
      case 'city':
        return state.governorates;
      case 'district':
        return state.districts;
      case 'sub_district':
        return state.subdistricts;
      case 'community':
        return state.communities;
      default:
        return state.entityOptions[field.type] ?? const [];
    }
  }
}

class _BoundTextField extends StatefulWidget {
  final String label;
  final String value;
  final String? unit;
  final bool required;
  final bool readonly;
  final bool number;
  final bool multiline;
  final ValueChanged<String> onChanged;
  final VoidCallback onBlur;

  const _BoundTextField({
    required this.label,
    required this.value,
    required this.onChanged,
    required this.onBlur,
    this.unit,
    this.required = false,
    this.readonly = false,
    this.number = false,
    this.multiline = false,
  });

  @override
  State<_BoundTextField> createState() => _BoundTextFieldState();
}

class _BoundTextFieldState extends State<_BoundTextField> {
  late final TextEditingController _ctrl;
  late final FocusNode _focus;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.value);
    _focus = FocusNode()..addListener(_onFocus);
  }

  void _onFocus() {
    if (!_focus.hasFocus) widget.onBlur();
  }

  @override
  void didUpdateWidget(covariant _BoundTextField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.value != _ctrl.text && !_focus.hasFocus) {
      _ctrl.value = TextEditingValue(
        text: widget.value,
        selection: TextSelection.collapsed(offset: widget.value.length),
      );
    }
  }

  @override
  void dispose() {
    _focus.removeListener(_onFocus);
    _focus.dispose();
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text.rich(
          TextSpan(
            text: widget.label,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textHint,
            ),
            children: [
              if (widget.required)
                TextSpan(
                  text: ' *',
                  style: TextStyle(color: AppColors.errorRed, fontSize: 11.sp),
                ),
            ],
          ),
          textAlign: TextAlign.start,
        ),
        SizedBox(height: 5.h),
        TextField(
          controller: _ctrl,
          focusNode: _focus,
          readOnly: widget.readonly,
          maxLines: widget.multiline ? 3 : 1,
          keyboardType: widget.number
              ? const TextInputType.numberWithOptions(decimal: true)
              : TextInputType.text,
          textAlign: widget.number ? TextAlign.end : TextAlign.start,
          textDirection:
              widget.number ? TextDirection.ltr : TextDirection.rtl,
          onChanged: widget.onChanged,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 13.sp,
            color: AppColors.textPrimary,
          ),
          decoration: InputDecoration(
            isDense: true,
            filled: true,
            fillColor: widget.readonly ? AppColors.cream : AppColors.goldWash,
            contentPadding:
                EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
            suffixText: widget.unit,
            suffixStyle: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 10.sp,
              color: AppColors.textHint,
            ),
          ),
        ),
      ],
    );
  }
}

class _FileField extends StatefulWidget {
  final FormSchemaField field;
  final String value;
  final ValueChanged<String> onChanged;
  const _FileField({
    required this.field,
    required this.value,
    required this.onChanged,
  });

  @override
  State<_FileField> createState() => _FileFieldState();
}

class _FileFieldState extends State<_FileField> {
  var _uploading = false;

  Future<void> _pick() async {
    final image = widget.field.type == 'image';
    final result = await FilePicker.platform.pickFiles(
      type: image ? FileType.image : FileType.any,
    );
    if (result == null || result.files.isEmpty) return;
    final f = result.files.first;
    MultipartFile file;
    if (f.path != null) {
      file = await MultipartFile.fromFile(f.path!, filename: f.name);
    } else if (f.bytes != null) {
      file = MultipartFile.fromBytes(f.bytes!, filename: f.name);
    } else {
      return;
    }
    setState(() => _uploading = true);
    try {
      final url = await getIt<BuilderRemoteDataSource>().uploadFormFile(
        file,
        kind: image ? 'image' : 'file',
      );
      widget.onChanged(url);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'تعذر رفع الملف',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
        ),
      );
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          widget.field.labelAr,
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 11.sp,
            fontWeight: FontWeight.w600,
            color: AppColors.textHint,
          ),
        ),
        SizedBox(height: 6.h),
        OutlinedButton.icon(
          onPressed: widget.field.readonly || _uploading ? null : _pick,
          icon: _uploading
              ? SizedBox(
                  width: 14.r,
                  height: 14.r,
                  child: const CircularProgressIndicator(strokeWidth: 2),
                )
              : Icon(Icons.attach_file, size: 16.r),
          label: Text(
            widget.value.isEmpty ? 'اختيار ملف' : 'تم الرفع',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
          ),
        ),
        if (widget.value.isNotEmpty)
          Padding(
            padding: EdgeInsets.only(top: 4.h),
            child: Text(
              widget.value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 10.sp,
                color: AppColors.textHint,
              ),
            ),
          ),
      ],
    );
  }
}
