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

class RainfallScreen extends StatefulWidget {
  const RainfallScreen({super.key});
  @override State<RainfallScreen> createState() => _RainfallScreenState();
}

class _RainfallScreenState extends State<RainfallScreen> {
  bool _daily = true;
  DateTime _date = DateTime.now();
  bool _saving = false;
  WaterLookupItemEntity? _selectedBasin;
  WaterLookupItemEntity? _selectedStation;
  WaterLookupItemEntity? _selectedGov;
  final _rfCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
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

  @override void dispose() { _rfCtrl.dispose(); _notesCtrl.dispose(); super.dispose(); }

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

  Future<void> _importRainfall() async {
    final repo = getIt<WaterRepository>();
    setState(() => _saving = true);

    final files = await _pickMultipartFiles(
      allowedExtensions: ['xls', 'xlsx', 'zip'],
    );
    if (files.isEmpty) {
      setState(() => _saving = false);
      return;
    }

    final result = await repo.importRainfall(
      files: files,
      clear: false,
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم استيراد بيانات الهطول بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل استيراد بيانات الهطول');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            msg,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: r.ok ? AppColors.forest1 : AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل استيراد بيانات الهطول';
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
    return BlocBuilder<WaterLookupsBloc, WaterLookupsState>(
      builder: (context, state) {
        List<WaterLookupItemEntity> basins = [];
        List<WaterLookupItemEntity> stations = [];
        List<WaterLookupItemEntity> governorates = [];

        if (state is WaterLookupsLoaded) {
          basins = state.lookups.basins;
          stations = state.lookups.stations;
          governorates = state.lookups.governorates;
        }

        return Directionality(
          textDirection: TextDirection.rtl,
          child: SingleChildScrollView(
            padding: EdgeInsets.all(14.r),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const GradientHeaderCard(
                      title: 'تحليل الهطول',
                      subtitle: 'ملفات .xls لمحطات الأحواض أو إدخال يومي للمحطة',
                      icon: Icons.grain_outlined),
                  SizedBox(height: 12.h),
                  StatsGrid(
                      crossAxisCount: 3,
                      items: WaterImportStatusStats.rainfallTop(_importStatus)),
                  SizedBox(height: 8.h),
                  StatsGrid(
                      items: WaterImportStatusStats.rainfallBottom(
                          _importStatus)),
                  SizedBox(height: 12.h),
                  ToggleTabRow(
                      isDailyEntry: _daily,
                      onChanged: (v) => setState(() => _daily = v)),
                  SizedBox(height: 12.h),
                  if (_daily) ...[
                    FormCard(
                        child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                          DatePickerField(
                              label: 'التاريخ',
                              initialDate: _date,
                              onDateChanged: (d) => setState(() => _date = d)),
                          SizedBox(height: 12.h),
                          if (state is WaterLookupsLoading) ...[
                            const FieldShimmer(label: 'الحوض'),
                            SizedBox(height: 12.h),
                            const FieldShimmer(label: 'المحطة'),
                            SizedBox(height: 12.h),
                            const FieldShimmer(label: 'المحافظة'),
                          ] else if (state is WaterLookupsError)
                            Text(state.message,
                                style: const TextStyle(color: Colors.red))
                          else ...[
                            AppDropdownField(
                                label: 'المحطة',
                                value: _selectedStation?.name ?? '',
                                items: stations.map((e) => e.name).toList(),
                                onChanged: (v) {
                                  if (v == null) return;
                                  final station = stations
                                      .firstWhere((e) => e.name == v);
                                  WaterLookupItemEntity? basin;
                                  WaterLookupItemEntity? gov;
                                  if (station.basinSlug != null &&
                                      station.basinSlug!.isNotEmpty) {
                                    for (final b in basins) {
                                      if (b.slug == station.basinSlug) {
                                        basin = b;
                                        break;
                                      }
                                    }
                                  }
                                  if (station.governorate != null &&
                                      station.governorate!.isNotEmpty) {
                                    for (final g in governorates) {
                                      if (g.slug == station.governorate ||
                                          g.name == station.governorate) {
                                        gov = g;
                                        break;
                                      }
                                    }
                                  }
                                  setState(() {
                                    _selectedStation = station;
                                    _selectedBasin = basin;
                                    _selectedGov = gov;
                                  });
                                }),
                            SizedBox(height: 12.h),
                            _ReadonlyField(
                              label: 'الحوض',
                              value: _selectedBasin?.name ?? '—',
                            ),
                            SizedBox(height: 12.h),
                            _ReadonlyField(
                              label: 'المحافظة',
                              value: _selectedGov?.name ??
                                  _selectedStation?.governorate ??
                                  '—',
                            ),
                          ],
                          SizedBox(height: 12.h),
                          AppTextField(
                              label: 'الهطول (ملم)',
                              controller: _rfCtrl,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                      decimal: true),
                              suffixText: 'ملم'),
                          SizedBox(height: 12.h),
                          AppTextField(
                              label: 'ملاحظات',
                              controller: _notesCtrl,
                              maxLines: 2),
                          SizedBox(height: 8.h),
                          Text(
                            'يُملأ الحوض والمحافظة تلقائياً عند اختيار المحطة.',
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 11.sp,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ])),
                    SizedBox(height: 12.h),
                    const DuplicateNote(),
                    SizedBox(height: 12.h),
                    SaveButton(isLoading: _saving, onPressed: _save),
                  ] else
                    FileImportPlaceholder(
                      note:
                          'اسحب وأفلت ملفات .XLS أو .XLSX أو .ZIP الخاصة بالهطول',
                      onPickFiles: _importRainfall,
                      onDownloadTemplate: () => downloadWaterTemplate(
                        context,
                        kind: 'rainfall',
                        fallbackName: 'rainfall.xlsx',
                      ),
                      onClear: () => clearWaterImport(
                        context,
                        clear: () => getIt<WaterRepository>().clearRainfall(),
                        onDone: _loadImportStatus,
                      ),
                    ),
                  SizedBox(height: 16.h),
                ]),
          ),
        );
      },
    );
  }

  Future<void> _save() async {
    final repo = getIt<WaterRepository>();

    final stationId = _selectedStation?.id;
    final basinSlug = _selectedStation?.basinSlug ?? _selectedBasin?.slug ?? '';
    final governorate =
        _selectedStation?.governorate ?? _selectedGov?.slug ?? '';
    final stationName = _selectedStation?.name ?? '';

    if (stationId == null || stationId == 0 || stationName.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('اختر المحطة',
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
      return;
    }

    setState(() => _saving = true);
    final result = await repo.saveRainfallDaily(
      observationDate: _date,
      basinSlug: basinSlug,
      stationName: stationName,
      governorate: governorate,
      precipitationMm: _tryParseDouble(_rfCtrl.text),
      notes: _notesCtrl.text.trim(),
      stationId: stationId,
    );
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم حفظ بيانات الهطول بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل حفظ بيانات الهطول');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            msg,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: r.ok ? AppColors.forest1 : AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
      if (r.ok) {
        _rfCtrl.clear();
        _notesCtrl.clear();
      }
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل حفظ بيانات الهطول';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            msg,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
    }
  }
}

class _ReadonlyField extends StatelessWidget {
  final String label;
  final String value;
  const _ReadonlyField({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          label,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 11.sp,
            fontWeight: FontWeight.w600,
            color: AppColors.textHint,
          ),
        ),
        SizedBox(height: 5.h),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 12.h),
          decoration: BoxDecoration(
            color: AppColors.goldWash,
            borderRadius: BorderRadius.circular(8.r),
            border: Border.all(color: AppColors.border),
          ),
          child: Text(
            value,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 13.sp,
              color: AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
