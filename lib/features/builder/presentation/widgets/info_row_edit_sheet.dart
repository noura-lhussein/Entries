import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/datasources/builder_remote_data_source.dart';
import '../../data/models/builder_models.dart';

Future<bool> showInfoRowEditSheet(
  BuildContext context, {
  required InfoRecord row,
  required List<BuilderAttribute> attributes,
  required Map<String, String> labels,
}) async {
  final saved = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: AppColors.surface,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16.r)),
    ),
    builder: (_) => _InfoRowEditSheet(
      row: row,
      attributes: attributes,
      labels: labels,
    ),
  );
  return saved == true;
}

class _EditField {
  final int? infoId;
  final int attributeId;
  final String label;
  final String type;
  const _EditField({
    required this.attributeId,
    required this.label,
    this.infoId,
    this.type = 'text',
  });
}

class _InfoRowEditSheet extends StatefulWidget {
  final InfoRecord row;
  final List<BuilderAttribute> attributes;
  final Map<String, String> labels;
  const _InfoRowEditSheet({
    required this.row,
    required this.attributes,
    required this.labels,
  });

  @override
  State<_InfoRowEditSheet> createState() => _InfoRowEditSheetState();
}

class _InfoRowEditSheetState extends State<_InfoRowEditSheet> {
  final _remote = getIt<BuilderRemoteDataSource>();
  var _loading = true;
  var _saving = false;
  String? _error;
  List<_EditField> _fields = const [];
  final _controllers = <int, TextEditingController>{};

  String _labelFor(String key, [String fallback = '']) {
    final mapped = widget.labels[key]?.trim() ?? '';
    if (mapped.isNotEmpty) return mapped;
    for (final a in widget.attributes) {
      if ('${a.id}' == key && a.label.trim().isNotEmpty) return a.label;
    }
    return fallback.trim().isNotEmpty ? fallback : key;
  }

  String _emptyIfDash(String? raw) {
    final v = raw?.trim() ?? '';
    if (v.isEmpty || v == '—') return '';
    return v;
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final byAttr = <int, InfoCellDetail>{};
      for (final id in widget.row.infoIds.where((e) => e > 0)) {
        try {
          final cell = await _remote.getInfoDetail(id);
          if (cell.confirmed == 'accept') {
            if (!mounted) return;
            setState(() {
              _loading = false;
              _error = 'لا يمكن تعديل سجل موافق عليه';
            });
            return;
          }
          final attrId = cell.attributeId > 0 ? cell.attributeId : 0;
          if (attrId > 0) byAttr[attrId] = cell;
        } catch (_) {
          // Keep schema fields even if one cell fails to load.
        }
      }

      final keys = <String>{};
      final titleId = widget.row.titleId;
      if (titleId != null) {
        for (final a in widget.attributes) {
          if (a.titleId == titleId && a.id > 0) keys.add('${a.id}');
        }
      }
      keys.addAll(widget.row.fields.keys);
      for (final id in byAttr.keys) {
        keys.add('$id');
      }

      final fields = <_EditField>[];
      for (final key in keys) {
        final attrId = int.tryParse(key) ?? 0;
        if (attrId <= 0) continue;
        BuilderAttribute? schema;
        for (final a in widget.attributes) {
          if (a.id == attrId) {
            schema = a;
            break;
          }
        }
        final cell = byAttr[attrId];
        final label = _labelFor(key, cell?.label ?? schema?.label ?? '');
        fields.add(_EditField(
          infoId: (cell?.id ?? 0) > 0 ? cell!.id : null,
          attributeId: attrId,
          label: label,
          type: schema?.type ?? cell?.type ?? 'text',
        ));
        _controllers[attrId] = TextEditingController(
          text: _emptyIfDash(cell?.value ?? widget.row.fields[key]),
        );
      }
      fields.sort((a, b) => a.label.compareTo(b.label));
      if (!mounted) return;
      setState(() {
        _fields = fields;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'تعذر تحميل السجل';
      });
    }
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final subMainId = widget.row.subMainId;
      for (final field in _fields) {
        final value = _controllers[field.attributeId]?.text.trim() ?? '';
        if (field.infoId != null) {
          if (value.isEmpty) continue;
          await _remote.patchInfoValue(field.infoId!, value);
          continue;
        }
        if (value.isEmpty || subMainId == null) continue;
        await _remote.createInfoValue(
          attributeId: field.attributeId,
          subMainId: subMainId,
          value: value,
          rowKey: widget.row.rowKey,
        );
      }
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = 'تعذر حفظ التعديلات';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
      child: SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxHeight: MediaQuery.sizeOf(context).height * 0.85,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
              Text(
                'تعديل السجل',
                textAlign: TextAlign.start,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 4.h),
              Text(
                'كل الحقول ظاهرة — الفارغ يمكن تعبئته',
                textAlign: TextAlign.start,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 12.sp,
                  color: AppColors.textHint,
                ),
              ),
              SizedBox(height: 12.h),
              if (_loading)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_error != null && _fields.isEmpty)
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 13.sp,
                    color: AppColors.errorRed,
                  ),
                )
              else ...[
                if (_error != null)
                  Padding(
                    padding: EdgeInsets.only(bottom: 8.h),
                    child: Text(
                      _error!,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 12.sp,
                        color: AppColors.errorRed,
                      ),
                    ),
                  ),
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    keyboardDismissBehavior:
                        ScrollViewKeyboardDismissBehavior.onDrag,
                    itemCount: _fields.length,
                    separatorBuilder: (_, _) => SizedBox(height: 10.h),
                    itemBuilder: (_, i) {
                      final field = _fields[i];
                      return AppTextField(
                        label: field.label.isEmpty ? 'حقل' : field.label,
                        hint: 'أدخل القيمة',
                        controller: _controllers[field.attributeId],
                        keyboardType: field.type == 'number'
                            ? const TextInputType.numberWithOptions(
                                decimal: true)
                            : TextInputType.text,
                        maxLines: field.type == 'textarea' ? 3 : 1,
                      );
                    },
                  ),
                ),
                SizedBox(height: 14.h),
                SaveButton(
                  label: 'حفظ',
                  isLoading: _saving,
                  onPressed: _saving ? null : _save,
                ),
              ],
            ],
          ),
        ),
      ),
    ),
    );
  }
}
