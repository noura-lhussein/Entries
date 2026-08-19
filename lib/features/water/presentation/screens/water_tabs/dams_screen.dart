import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:file_picker/file_picker.dart';
import 'package:dio/dio.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../../../core/di/injection.dart';
import '../../../../../core/network/api_result.dart';
import 'package:meters_entry/features/water/presentation/bloc/water_lookups_bloc.dart';
import 'package:meters_entry/features/water/presentation/bloc/water_lookups_state.dart';
import 'package:meters_entry/features/water/domain/entities/water_lookup_item_entity.dart';
import 'package:meters_entry/features/water/domain/entities/water_import_result_entity.dart';
import 'package:meters_entry/features/water/domain/repositories/water_repository.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_import_status_stats.dart';

class DamsScreen extends StatefulWidget {
  const DamsScreen({super.key});
  @override State<DamsScreen> createState() => _DamsScreenState();
}

class _DamsScreenState extends State<DamsScreen> {
  bool _daily = true;
  DateTime _date = DateTime.now();
  WaterLookupItemEntity? _selectedDam;
  final _storCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  bool _saving = false;
  Map<String, dynamic>? _importStatus;

  @override
  void initState() {
    super.initState();
    _loadImportStatus();
  }

  Future<void> _loadImportStatus() async {
    final result = await getIt<WaterRepository>().getImportStatus();
    if (!mounted) return;
    if (result is Success<Map<String, dynamic>>) {
      setState(() => _importStatus = (result).data);
    }
  }

  @override void dispose() { _storCtrl.dispose(); _notesCtrl.dispose(); super.dispose(); }

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

  Future<void> _importDams() async {
    final repo = getIt<WaterRepository>();
    setState(() => _saving = true);

    final files = await _pickMultipartFiles(
      allowedExtensions: ['xls', 'xlsx'],
    );
    if (files.isEmpty) {
      setState(() => _saving = false);
      return;
    }

    final result = await repo.importDams(
      files: files,
      clear: false, // default: don't replace all data
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم استيراد بيانات السدود بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل استيراد بيانات السدود');
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
      final msg = e.apiErrorModel.message ?? 'فشل استيراد بيانات السدود';
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
          GradientHeaderCard(title: 'معلومات السدود', subtitle: 'قراءات المخزون اليومية + ملفات .XLS السنوية', icon: Icons.water_damage_outlined),
          SizedBox(height: 12.h),
          StatsGrid(items: WaterImportStatusStats.dams(_importStatus)),
          SizedBox(height: 12.h),
          ToggleTabRow(isDailyEntry: _daily, onChanged: (v) => setState(() => _daily = v)),
          SizedBox(height: 12.h),
          _daily
              ? _buildForm()
              : FileImportPlaceholder(
                  note: 'اسحب وأفلت ملفات .XLS أو .XLSX الخاصة بالسدود',
                  onPickFiles: _importDams,
                  onDownloadTemplate: () => downloadWaterTemplate(
                    context,
                    kind: 'dams-storage',
                    fallbackName: 'dams-storage.xlsx',
                  ),
                  onClear: () => clearWaterImport(
                    context,
                    clear: () => getIt<WaterRepository>().clearDamStorage(),
                    onDone: _loadImportStatus,
                  ),
                ),
          SizedBox(height: 16.h),
        ]),
      ),
    );
  }

  Widget _buildForm() {
    return BlocBuilder<WaterLookupsBloc, WaterLookupsState>(
      builder: (context, state) {
        List<WaterLookupItemEntity> dams = [];
        if (state is WaterLookupsLoaded) {
          dams = state.lookups.dams;
          if (_selectedDam == null && dams.isNotEmpty) {
            _selectedDam = dams.first;
          }
        }

        return FormCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DatePickerField(
                  label: 'التاريخ',
                  initialDate: _date,
                  onDateChanged: (d) => setState(() => _date = d)),
              SizedBox(height: 12.h),
              if (state is WaterLookupsLoading)
                const FieldShimmer(label: 'السد')
              else if (state is WaterLookupsError)
                Text(state.message, style: const TextStyle(color: Colors.red))
              else
                AppDropdownField(
                  label: 'السد',
                  value: _selectedDam?.name ?? '',
                  items: dams.map((e) => e.name).toList(),
                  onChanged: (v) {
                    setState(() {
                      _selectedDam = dams.firstWhere((e) => e.name == v);
                    });
                  },
                ),
              SizedBox(height: 12.h),
              AppTextField(
                  label: 'المخزون (مليون م³)',
                  controller: _storCtrl,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  suffixText: 'مليون م³'),
              SizedBox(height: 12.h),
              AppTextField(label: 'ملاحظات', controller: _notesCtrl, maxLines: 2),
              SizedBox(height: 14.h),
              const DuplicateNote(),
              SizedBox(height: 14.h),
              SaveButton(isLoading: _saving, onPressed: _saveReal),
            ],
          ),
        );
      },
    );
  }

  Future<void> _saveReal() async {
    final repo = getIt<WaterRepository>();
    final damId = _selectedDam?.id;

    if (damId == null || damId == 0) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'اختر السد أولاً',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
      return;
    }

    setState(() => _saving = true);
    final result = await repo.saveDamDaily(
      readingDate: _date,
      damId: damId,
      storageMcm: _tryParseDouble(_storCtrl.text),
      notes: _notesCtrl.text.trim(),
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم حفظ بيانات السد بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل حفظ بيانات السد');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content:
              Text(msg, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
          backgroundColor: r.ok ? AppColors.forest1 : AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
      if (r.ok) {
        _storCtrl.clear();
        _notesCtrl.clear();
      }
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل حفظ بيانات السد';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content:
              Text(msg, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    }
  }
}
