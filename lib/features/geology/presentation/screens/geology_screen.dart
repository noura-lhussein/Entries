import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../../../core/widgets/excel_entry_bar.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/datasources/geology_remote_data_source.dart';
import '../../data/ore_product_catalog.dart';
import '../widgets/geology_entry/geology_ore_form_models.dart';
import '../widgets/geology_entry/geology_ore_grouping.dart';
import '../widgets/geology_entry/geology_ore_section.dart';

/// Ore production & contracts — matches moe-portal geology-data-entry.
class GeologyScreen extends StatefulWidget {
  const GeologyScreen({super.key});

  @override
  State<GeologyScreen> createState() => _GeologyScreenState();
}

class _GeologyScreenState extends State<GeologyScreen> {
  final _ds = getIt<GeologyRemoteDataSource>();
  final _notesAr = TextEditingController();
  final _notesEn = TextEditingController();

  int _planYear = DateTime.now().year;
  String _status = 'draft';
  String _oreToAdd = '';
  var _loading = true;
  var _saving = false;
  var _downloading = false;
  var _importing = false;
  String? _error;
  var _saved = false;
  var _importOk = false;
  List<OreProductGroup> _groups = [OreProductGroup()];

  String get _snapshotDate => '$_planYear-01-01';

  List<int> get _yearOptions {
    final current = DateTime.now().year;
    final years = [for (var y = current + 1; y >= current - 5; y--) y];
    if (!years.contains(_planYear)) {
      years.add(_planYear);
      years.sort((a, b) => b.compareTo(a));
    }
    return years;
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _notesAr.dispose();
    _notesEn.dispose();
    for (final g in _groups) {
      g.dispose();
    }
    super.dispose();
  }

  void _replaceGroups(List<OreProductGroup> next) {
    for (final g in _groups) {
      g.dispose();
    }
    _groups = next;
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
      _saved = false;
    });
    try {
      final row = await _ds.getDailyReport(_snapshotDate);
      if (!mounted) return;
      _replaceGroups(groupOreRows(row['ore_rows'] as List? ?? const []));
      setState(() {
        _status =
            row['status']?.toString() == 'published' ? 'published' : 'draft';
        _notesAr.text = row['notes_ar']?.toString() ?? '';
        _notesEn.text = row['notes_en']?.toString() ?? '';
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = userFacingErrorMessage(e, fallback: 'تعذّر تحميل بيانات الإنتاج.');
      });
    }
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
      _saved = false;
      _importOk = false;
    });
    try {
      final row = await _ds.saveDailyReport({
        'report_date': _snapshotDate,
        'status': _status,
        'notes_ar': _notesAr.text.trim(),
        'notes_en': _notesEn.text.trim(),
        'ore_rows': flattenOreGroups(_groups),
      });
      if (!mounted) return;
      _replaceGroups(groupOreRows(row['ore_rows'] as List? ?? const []));
      setState(() {
        _saving = false;
        _saved = true;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = userFacingErrorMessage(e, fallback: 'تعذّر حفظ بيانات الإنتاج.');
      });
    }
  }

  Future<MultipartFile?> _pickExcel() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['xlsx', 'xlsm'],
    );
    if (result == null || result.files.isEmpty) return null;
    final f = result.files.first;
    if (f.path != null) {
      return MultipartFile.fromFile(f.path!, filename: f.name);
    }
    if (f.bytes != null) {
      return MultipartFile.fromBytes(f.bytes!, filename: f.name);
    }
    return null;
  }

  Future<void> _downloadTemplate() async {
    setState(() {
      _downloading = true;
      _error = null;
      _saved = false;
      _importOk = false;
    });
    try {
      final res = await _ds.downloadOreTemplate(planYear: _planYear);
      final bytes = res.data;
      if (bytes == null || bytes.isEmpty) {
        throw Exception('empty');
      }
      await saveAndOpenBytes(
        bytes,
        filename: filenameFromResponse(
          res,
          'geology_ore_production_template_$_planYear.xlsx',
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'تعذر تنزيل قالب Excel.');
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _exportExcel() async {
    setState(() {
      _error = null;
      _saved = false;
      _importOk = false;
    });
    try {
      final res = await _ds.exportOreProduction(_planYear);
      final bytes = res.data;
      if (bytes == null || bytes.isEmpty) {
        throw Exception('empty');
      }
      await saveAndOpenBytes(
        bytes,
        filename: filenameFromResponse(
          res,
          'geology_ore_production_$_planYear.xlsx',
        ),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'تعذر استخراج البيانات.');
    }
  }

  Future<void> _importExcel() async {
    final file = await _pickExcel();
    if (file == null) return;
    setState(() {
      _importing = true;
      _error = null;
      _saved = false;
      _importOk = false;
    });
    try {
      final result = await _ds.importOreProduction(
        file,
        publish: _status == 'published',
      );
      final year = result['plan_year'];
      if (year is int) _planYear = year;
      if (!mounted) return;
      setState(() => _importOk = true);
      await _load();
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'تعذر استيراد ملف Excel.');
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  void _onH1Changed(OreTypeLine line) {
    final pct = executionPct(
      parseNum(line.h1PlanCtrl.text),
      parseNum(line.h1ExecCtrl.text),
    );
    line.pctCtrl.text = pct == null ? '' : '$pct';
  }

  void _addOreGroup() {
    final nameAr = _oreToAdd.trim();
    if (nameAr.isEmpty) return;
    if (_groups.any((g) => g.productNameAr.trim() == nameAr)) {
      setState(() => _oreToAdd = '');
      return;
    }
    final found = findOreProduct(nameAr);
    final defaultLines = nameAr == 'رمال كوارتزية'
        ? [
            OreTypeLine(productionType: 'ذاتي', unit: 'طن'),
            OreTypeLine(productionType: 'معهّد', unit: 'م3')
          ]
        : [OreTypeLine(unit: 'طن')];
    setState(() {
      _groups = [
        ..._groups.where((g) => g.productNameAr.trim().isNotEmpty),
        OreProductGroup(
          productNameAr: nameAr,
          productNameEn: found?.nameEn ?? '',
          lines: defaultLines,
        ),
      ];
      _oreToAdd = '';
    });
  }

  void _addTypeLine(int gi) {
    setState(() {
      _groups[gi].lines = [
        ..._groups[gi].lines,
        OreTypeLine(productionType: 'معهّد', unit: 'م3'),
      ];
    });
  }

  void _removeTypeLine(int gi, int li) {
    final group = _groups[gi];
    if (group.lines.length <= 1) {
      _removeOreGroup(gi);
      return;
    }
    setState(() {
      group.lines[li].dispose();
      group.lines = [
        for (var i = 0; i < group.lines.length; i++)
          if (i != li) group.lines[i],
      ];
    });
  }

  void _removeOreGroup(int gi) {
    setState(() {
      if (_groups.length <= 1) {
        _groups[gi].dispose();
        _groups = [OreProductGroup()];
        return;
      }
      _groups[gi].dispose();
      _groups = [
        for (var i = 0; i < _groups.length; i++)
          if (i != gi) _groups[i],
      ];
    });
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: ListView(
        padding: EdgeInsets.all(16.r),
        children: [
          Text(
            'إنتاج الخامات والعقود',
            style: TextStyle(
              fontFamily: 'Cairo',
              fontWeight: FontWeight.w700,
              fontSize: 16.sp,
            ),
          ),
          SizedBox(height: 4.h),
          Text(
            'حدّث خطة الإنتاج والتنفيذ وعدد العقود عند إبرام عقد جديد أو تغيّر الأرقام — ليست تقريراً يومياً.',
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 12.sp,
              color: AppColors.textSecondary,
            ),
          ),
          SizedBox(height: 12.h),
          ExcelEntryBar(
            hint:
                'نزّل القالب أو استخرج البيانات الحالية، عدّلها في Excel، ثم ارفع الملف لملء الجدول.',
            downloading: _downloading,
            importing: _importing,
            onDownload: _downloadTemplate,
            onExport: _exportExcel,
            onUpload: _importExcel,
          ),
          SizedBox(height: 12.h),
          FormCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<int>(
                        initialValue: _planYear,
                        decoration: const InputDecoration(
                          labelText: 'سنة الخطة',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          for (final y in _yearOptions)
                            DropdownMenuItem(value: y, child: Text('$y')),
                        ],
                        onChanged: _loading
                            ? null
                            : (y) {
                                if (y == null) return;
                                setState(() => _planYear = y);
                                _load();
                              },
                      ),
                    ),
                    SizedBox(width: 12.w),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: _status,
                        decoration: const InputDecoration(
                          labelText: 'الحالة',
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'draft', child: Text('مسودة')),
                          DropdownMenuItem(
                              value: 'published', child: Text('منشور')),
                        ],
                        onChanged: _loading
                            ? null
                            : (s) => setState(() => _status = s ?? 'draft'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          SizedBox(height: 12.h),
          GeologyOreSection(
            groups: _groups,
            oreToAdd: _oreToAdd,
            planYear: _planYear,
            onOreToAddChanged: (v) => setState(() => _oreToAdd = v),
            onAddOreGroup: _addOreGroup,
            onRemoveOreGroup: _removeOreGroup,
            onAddTypeLine: _addTypeLine,
            onRemoveTypeLine: _removeTypeLine,
            onH1Changed: _onH1Changed,
            onChanged: () => setState(() {}),
          ),
          SizedBox(height: 12.h),
          FormCard(
            child: Column(
              children: [
                AppTextField(
                  label: 'ملاحظات (عربي)',
                  controller: _notesAr,
                  maxLines: 3,
                ),
                SizedBox(height: 10.h),
                AppTextField(
                  label: 'ملاحظات (إنجليزي)',
                  controller: _notesEn,
                  maxLines: 3,
                ),
              ],
            ),
          ),
          SizedBox(height: 12.h),
          if (_loading) const LinearProgressIndicator(minHeight: 2),
          if (_error != null)
            Padding(
              padding: EdgeInsets.only(bottom: 8.h),
              child: Text(
                _error!,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  color: AppColors.red2,
                  fontSize: 12.sp,
                ),
              ),
            ),
          if (_importOk)
            Padding(
              padding: EdgeInsets.only(bottom: 8.h),
              child: Text(
                'تم استيراد ملف Excel بنجاح.',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  color: AppColors.successGreen,
                  fontSize: 12.sp,
                ),
              ),
            ),
          if (_saved)
            Padding(
              padding: EdgeInsets.only(bottom: 8.h),
              child: Text(
                'تم حفظ بيانات الإنتاج والعقود.',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  color: AppColors.successGreen,
                  fontSize: 12.sp,
                ),
              ),
            ),
          SaveButton(
            isLoading: _saving,
            label: 'حفظ البيانات',
            onPressed: _loading ? null : _save,
          ),
          SizedBox(height: 16.h),
        ],
      ),
    );
  }
}
