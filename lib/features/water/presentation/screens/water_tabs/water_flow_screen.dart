import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../../../core/di/injection.dart';
import '../../../../../core/network/api_result.dart';
import 'package:meters_entry/features/water/domain/repositories/water_repository.dart';
import 'package:meters_entry/features/water/domain/entities/water_import_result_entity.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_import_status_stats.dart';

class WaterFlowScreen extends StatefulWidget {
  const WaterFlowScreen({super.key});
  @override State<WaterFlowScreen> createState() => _WaterFlowScreenState();
}

class _WaterFlowScreenState extends State<WaterFlowScreen> {
  bool _daily = true;
  DateTime _date = DateTime.now();
  bool _saving = false;
  Map<String, dynamic>? _importStatus;
  final _titleCtrl = TextEditingController();
  // Tashreen
  final _tInCtrl   = TextEditingController(); // incoming
  final _tLvlCtrl  = TextEditingController();
  final _tStorCtrl = TextEditingController();
  final _tGenCtrl  = TextEditingController();
  // Euphrates
  final _fLvlCtrl  = TextEditingController();
  final _fStorCtrl = TextEditingController();
  final _fGenCtrl  = TextEditingController();
  // Kadeeran + total
  final _kGenCtrl  = TextEditingController();
  final _totCtrl   = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadImportStatus();
    _loadDaily();
  }

  Future<void> _loadImportStatus() async {
    final result = await getIt<WaterRepository>().getImportStatus();
    if (!mounted) return;
    if (result is Success<Map<String, dynamic>>) {
      setState(() => _importStatus = (result).data);
    }
  }

  Future<void> _loadDaily() async {
    final result = await getIt<WaterRepository>().getEuphratesDaily(_date);
    if (!mounted) return;
    if (result is! Success<Map<String, dynamic>?>) return;
    final reading = (result).data;
    if (reading == null) return;
    void setCtrl(TextEditingController c, dynamic v) {
      c.text = v == null ? '' : '$v';
    }
    setCtrl(_titleCtrl, reading['report_label']);
    setCtrl(_tInCtrl, reading['inflow_jarabulus']);
    setCtrl(_tLvlCtrl, reading['tishreen_level_m']);
    setCtrl(_tStorCtrl, reading['tishreen_storage_mcm']);
    setCtrl(_tGenCtrl, reading['tishreen_generation_mwh']);
    setCtrl(_fLvlCtrl, reading['furat_level_m']);
    setCtrl(_fStorCtrl, reading['furat_storage_mcm']);
    setCtrl(_fGenCtrl, reading['furat_generation_mwh']);
    setCtrl(_kGenCtrl, reading['kadiran_generation_mwh']);
    setCtrl(_totCtrl, reading['total_generation_mwh']);
    setState(() {});
  }

  @override void dispose() {
    for (final c in [_titleCtrl,_tInCtrl,_tLvlCtrl,_tStorCtrl,_tGenCtrl,_fLvlCtrl,_fStorCtrl,_fGenCtrl,_kGenCtrl,_totCtrl]) {
      c.dispose();
    }
    super.dispose();
  }

  double? _tryParseDouble(String text) {
    final t = text.trim().replaceAll(',', '.');
    if (t.isEmpty) return null;
    return double.tryParse(t);
  }

  Future<List<MultipartFile>> _pickMultipartFiles({
    required List<String> allowedExtensions,
  }) async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.custom,
      allowedExtensions: allowedExtensions,
    );
    if (result == null) return [];

    final files = <MultipartFile>[];
    for (final f in result.files) {
      final filename = f.name;
      if (f.path != null) {
        files.add(await MultipartFile.fromFile(
          f.path!,
          filename: filename,
        ));
      } else if (f.bytes != null) {
        files.add(MultipartFile.fromBytes(f.bytes!, filename: filename));
      }
    }
    return files;
  }

  Future<void> _importEuphrates() async {
    final repo = getIt<WaterRepository>();
    setState(() => _saving = true);

    final files = await _pickMultipartFiles(
      allowedExtensions: ['xls', 'xlsx'],
    );
    if (files.isEmpty) {
      setState(() => _saving = false);
      return;
    }

    final result = await repo.importEuphrates(
      files: files,
      clear: false,
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم استيراد بيانات الوارد المائي بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل استيراد بيانات الوارد المائي');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            msg,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: r.ok ? AppColors.forest1 : AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل استيراد بيانات الوارد المائي';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            msg,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(14.r),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          GradientHeaderCard(title: 'سلسلة سدود الفرات', subtitle: 'قراءات الوارد والمنسوب والتوليد لسدود تشرين والفرات وكديران', icon: Icons.waves_outlined),
          SizedBox(height: 12.h),
          StatsGrid(items: WaterImportStatusStats.euphrates(_importStatus)),
          SizedBox(height: 12.h),
          ToggleTabRow(isDailyEntry: _daily, onChanged: (v) => setState(() => _daily = v)),
          SizedBox(height: 12.h),
          if (_daily) ...[
            FormCard(child: Column(mainAxisSize: MainAxisSize.min, children: [
              AppTextField(label: 'عنوان التقرير', controller: _titleCtrl),
              SizedBox(height: 10.h),
              DatePickerField(
                label: 'التاريخ',
                initialDate: _date,
                onDateChanged: (d) {
                  setState(() => _date = d);
                  _loadDaily();
                },
              ),
            ])),
            SizedBox(height: 12.h),
            SectionCard(title: 'محطة تشرين',
              child: FieldsWrap(fields: [
                AppTextField(label: 'الوارد (م³/ث)', controller: _tInCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'م³/ث'),
                AppTextField(label: 'منسوب تشرين',   controller: _tLvlCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'م'),
                AppTextField(label: 'مخزون تشرين',        controller: _tStorCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'مليون م³'),
                AppTextField(label: 'توليد تشرين',        controller: _tGenCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'MW'),
              ])),
            SizedBox(height: 12.h),
            SectionCard(title: 'محطة الفرات + كديران',
              child: FieldsWrap(fields: [
                AppTextField(label: 'منسوب الفرات',   controller: _fLvlCtrl,  keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'م'),
                AppTextField(label: 'مخزون الفرات',        controller: _fStorCtrl, keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'مليون م³'),
                AppTextField(label: 'توليد الفرات',  controller: _fGenCtrl,  keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'MW'),
                AppTextField(label: 'توليد كديران',  controller: _kGenCtrl,  keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'MW'),
              ])),
            SizedBox(height: 12.h),
            SectionCard(title: 'الإجمالي',
              child: AppTextField(label: 'إجمالي التوليد', controller: _totCtrl,
                keyboardType: const TextInputType.numberWithOptions(decimal: true), suffixText: 'MW')),
            SizedBox(height: 12.h),
            const DuplicateNote(),
            SizedBox(height: 12.h),
            SaveButton(isLoading: _saving, onPressed: _save),
          ] else
            FileImportPlaceholder(
              note: 'اسحب وأفلت ملفات .XLS أو .XLSX الخاصة بالوارد المائي',
              onPickFiles: _importEuphrates,
              onDownloadTemplate: () => downloadWaterTemplate(
                context,
                kind: 'euphrates',
                fallbackName: 'euphrates.xlsx',
              ),
              onClear: () => clearWaterImport(
                context,
                clear: () => getIt<WaterRepository>().clearEuphrates(),
                onDone: _loadImportStatus,
              ),
            ),
          SizedBox(height: 16.h),
        ]),
      ),
    );
  }

  Future<void> _save() async {
    final repo = getIt<WaterRepository>();

    setState(() => _saving = true);
    final result = await repo.saveEuphratesDaily(
      payload: {
        'reading_date':
            '${_date.year.toString().padLeft(4, '0')}-${_date.month.toString().padLeft(2, '0')}-${_date.day.toString().padLeft(2, '0')}',
        'report_label': _titleCtrl.text.trim(),
        'inflow_jarabulus': _tryParseDouble(_tInCtrl.text),
        'tishreen_level_m': _tryParseDouble(_tLvlCtrl.text),
        'tishreen_storage_mcm': _tryParseDouble(_tStorCtrl.text),
        'tishreen_outflow': null,
        'tishreen_generation_mwh': _tryParseDouble(_tGenCtrl.text),
        'furat_level_m': _tryParseDouble(_fLvlCtrl.text),
        'furat_storage_mcm': _tryParseDouble(_fStorCtrl.text),
        'furat_outflow': null,
        'furat_generation_mwh': _tryParseDouble(_fGenCtrl.text),
        'kadiran_outflow': null,
        'kadiran_generation_mwh': _tryParseDouble(_kGenCtrl.text),
        'al_jalab_discharge': null,
        'total_generation_mwh': _tryParseDouble(_totCtrl.text),
      },
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم حفظ بيانات الوارد المائي بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل حفظ بيانات الوارد المائي');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
          backgroundColor: r.ok ? AppColors.forest1 : AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل حفظ بيانات الوارد المائي';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    }
  }
}
