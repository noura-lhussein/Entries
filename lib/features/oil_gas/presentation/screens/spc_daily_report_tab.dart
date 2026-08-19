import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../../../core/widgets/excel_entry_bar.dart';
import '../../../../core/widgets/report_dates_chips.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/datasources/oil_gas_remote_data_source.dart';
import '../utils/petroleum_form_utils.dart';
import '../widgets/models/petroleum_data.dart';
import '../widgets/spc_report_table.dart';

class SpcDailyReportTab extends StatefulWidget {
  const SpcDailyReportTab({super.key});
  @override
  State<SpcDailyReportTab> createState() => _SpcDailyReportTabState();
}

class _SpcDailyReportTabState extends State<SpcDailyReportTab> {
  DateTime _date = DateTime.now();
  bool _saving = false;
  bool _loading = false;
  bool _publish = true;
  String? _loadError;
  List<String> _reportDates = const [];
  var _downloading = false;
  var _importing = false;
  final _notesCtrl = TextEditingController();
  final Map<String, TextEditingController> _ctrls = {
    for (final r in kSpcRows) r.key: TextEditingController()
  };

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      final raw = await getIt<OilGasRemoteDataSource>().getReportDates();
      final dates = raw.map((e) => e.toString()).where((e) => e.isNotEmpty).toList();
      if (!mounted) return;
      setState(() {
        _reportDates = dates;
        if (dates.isNotEmpty) {
          final parsed = DateTime.tryParse(dates.first);
          if (parsed != null) _date = parsed;
        }
      });
    } catch (_) {
      // keep today; still try load report
    }
    await _loadReport();
  }

  Future<void> _loadReport() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final detail =
          await getIt<OilGasRemoteDataSource>().getReportDetail(fmtDate(_date));
      for (final c in _ctrls.values) {
        c.clear();
      }
      _notesCtrl.text = detail['notes_ar']?.toString() ?? '';
      final metrics = detail['metrics'] as List? ?? const [];
      for (final raw in metrics.whereType<Map>()) {
        final key = raw['metric_key']?.toString();
        if (key == null || !_ctrls.containsKey(key)) continue;
        final v = raw['value'];
        _ctrls[key]!.text = v == null ? '' : '$v';
      }
      final status = detail['status']?.toString();
      if (status != null) _publish = status == 'published';
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadError = userFacingErrorMessage(
          e,
          fallback: 'تعذر تحميل التقرير اليومي لهذا التاريخ',
        );
      });
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _downloadTemplate() async {
    setState(() => _downloading = true);
    try {
      final res = await getIt<OilGasRemoteDataSource>()
          .downloadExecutiveTemplate(date: fmtDate(_date));
      final bytes = res.data;
      if (bytes == null || bytes.isEmpty) throw Exception('empty');
      await saveAndOpenBytes(
        bytes,
        filename: filenameFromResponse(res, 'oil_gas_executive_report_template.xlsx'),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('تعذر تنزيل قالب Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.red2,
      ));
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _importExcel() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['xlsx', 'xlsm'],
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
    setState(() => _importing = true);
    try {
      final imported = await getIt<OilGasRemoteDataSource>()
          .importExecutiveReport(file, publish: _publish);
      final dateStr = imported['report_date']?.toString();
      final parsed = dateStr == null ? null : DateTime.tryParse(dateStr);
      if (parsed != null) _date = parsed;
      await _loadReport();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('تم استيراد التقرير من Excel بنجاح.',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.forest1,
      ));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('تعذر استيراد ملف Excel. تحقق من القالب والقيم.',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.red2,
      ));
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  @override
  void dispose() {
    _notesCtrl.dispose();
    for (final c in _ctrls.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final metrics = <Map<String, dynamic>>[];
      for (final r in kSpcRows) {
        final v = parseNum(_ctrls[r.key]?.text ?? '');
        if (v != null) {
          metrics.add({
            'metric_key': r.key,
            'dimension': '',
            'value': v,
            'unit': r.unit,
          });
        }
      }
      await getIt<OilGasRemoteDataSource>().upsertDailyReport({
        'report_date': fmtDate(_date),
        'status': _publish ? 'published' : 'draft',
        'notes_ar': _notesCtrl.text.trim(),
        'notes_en': '',
        'metrics': metrics,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('تم حفظ التقرير اليومي بنجاح',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.forest1,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
            userFacingErrorMessage(e, fallback: 'فشل حفظ التقرير اليومي'),
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.red2,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
      ));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.all(14.r),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          GradientHeaderCard(
            title: 'التقرير اليومي',
            subtitle: 'إدخال بيانات التقرير اليومي التنفيذي لقطاع البترول ومشتقاته',
            icon: Icons.oil_barrel_outlined,
          ),
          SizedBox(height: 12.h),
          ExcelEntryBar(
            hint: 'نزّل القالب، املأ القيم، ثم ارفع الملف لاستيراد التقرير.',
            downloading: _downloading,
            importing: _importing,
            onDownload: _downloadTemplate,
            onUpload: _importExcel,
          ),
          SizedBox(height: 12.h),
          ReportDatesChips(
            dates: _reportDates,
            selected: fmtDate(_date),
            onSelected: (d) {
              final parsed = DateTime.tryParse(d);
              if (parsed == null) return;
              setState(() => _date = parsed);
              _loadReport();
            },
          ),
          if (_reportDates.isNotEmpty) SizedBox(height: 12.h),
          if (_loadError != null) ...[
            Material(
              color: AppColors.red2.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10.r),
              child: Padding(
                padding: EdgeInsets.all(12.r),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: AppColors.red2, size: 20.r),
                    SizedBox(width: 8.w),
                    Expanded(
                      child: Text(
                        _loadError!,
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 12.sp,
                          color: AppColors.red2,
                        ),
                      ),
                    ),
                    TextButton(
                      onPressed: _loadReport,
                      child: const Text('إعادة'),
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(height: 12.h),
          ],
          FormCard(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
            DatePickerField(
                label: 'تاريخ التقرير',
                initialDate: _date,
                onDateChanged: (d) {
                  setState(() => _date = d);
                  _loadReport();
                }),
            if (_loading) ...[
              SizedBox(height: 8.h),
              const LinearProgressIndicator(minHeight: 2),
            ],
            SizedBox(height: 8.h),
            Text(
              'الموضوع: التقرير اليومي لتاريخ ${_date.day}/${_date.month}/${_date.year}',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 12.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ])),
          SizedBox(height: 12.h),
          SpcReportTable(controllers: _ctrls, reportDate: _date),
          SizedBox(height: 12.h),
          FormCard(
            child: AppTextField(
              label: 'ملاحظات (عربي)',
              controller: _notesCtrl,
              maxLines: 4,
            ),
          ),
          SizedBox(height: 12.h),
          FormCard(
            child: InkWell(
              onTap: () => setState(() => _publish = !_publish),
              child: Row(children: [
                Checkbox(
                  value: _publish,
                  activeColor: AppColors.forest1,
                  onChanged: (v) => setState(() => _publish = v ?? true),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4.r)),
                ),
                Expanded(
                  child: Text(
                    'نشر التقرير بعد الحفظ',
                    style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 12.sp,
                        color: AppColors.textPrimary),
                  ),
                ),
              ]),
            ),
          ),
          SizedBox(height: 12.h),
          SaveButton(
            isLoading: _saving,
            label: 'حفظ التقرير اليومي',
            onPressed: _save,
          ),
          SizedBox(height: 16.h),
        ]),
      ),
    );
  }
}
