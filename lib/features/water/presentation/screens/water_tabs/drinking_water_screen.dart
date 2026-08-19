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
import '../../utils/drinking_water_payload_mapper.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_import_status_stats.dart';
import '../../widgets/drinking_water/drinking_energy_supply_section.dart';
import '../../widgets/drinking_water/drinking_import_mode_card.dart';
import '../../widgets/drinking_water/drinking_operation_status_section.dart';
import '../../widgets/drinking_water/drinking_other_info_section.dart';
import '../../widgets/drinking_water/drinking_station_definition_section.dart';
import '../../widgets/drinking_water/drinking_station_type_section.dart';

class DrinkingWaterScreen extends StatefulWidget {
  const DrinkingWaterScreen({super.key});

  @override
  State<DrinkingWaterScreen> createState() => _DrinkingWaterScreenState();
}

class _DrinkingWaterScreenState extends State<DrinkingWaterScreen> {
  bool _daily = true;
  bool _saving = false;
  bool _importSurvey = false;
  DateTime _registrationDate = DateTime(2026, 2, 14);
  WaterLookupItemEntity? _selectedStation;
  Map<String, dynamic>? _importStatus;

  final _orgUnitCtrl = TextEditingController();
  final _notOperatingReasonCtrl = TextEditingController(text: 'سرقة وتخريب');

  final Map<String, String> _values = {
    'isWorking': 'لا',
    'buildingStatus': '3 - لا حاجة للتدخل',
    'previousRehab': 'لا',
    'safetyProcedures': 'لا',
    'rehabType': 'غير محدد',
    'waterHammerProtection': 'لا',
    'waterHammerEfficiency': 'غير محدد',
    'publicGrid': 'لا',
    'gridConnectionWorks': 'لا',
    'electricalConnectionEfficiency': '2 - يحتاج صيانة دورية',
    'transformerEfficiency': '3 - لا حاجة للتدخل',
    'panelEfficiency': '3 - لا حاجة للتدخل',
    'gridEnergyProductivity': '0%',
    'solarAvailable': 'لا',
    'solarProductivity': 'غير محدد',
    'solarSystemEfficiency': 'غير محدد',
    'generatorAvailable': 'نعم',
    'needsSolarInstallation': 'نعم',
    'solarSpaceAvailable': 'لا',
    'alternativeEnergy': 'لا',
    'pumpingStation': 'لا',
    'wellStation': 'لا',
    'treatmentStation': 'لا',
    'waterAnalysis': 'نعم',
    'waterTanks': 'لا',
    'labEquipment': 'غير محدد',
  };

  @override
  void initState() {
    super.initState();
    _loadImportStatus();
  }

  Future<void> _loadImportStatus() async {
    final result = await getIt<WaterRepository>().getImportStatus();
    if (!mounted) return;
    if (result is Success<Map<String, dynamic>>) {
      setState(
          () => _importStatus = (result).data);
    }
  }

  @override
  void dispose() {
    _orgUnitCtrl.dispose();
    _notOperatingReasonCtrl.dispose();
    super.dispose();
  }

  void _onFieldChanged(String key, String value) {
    setState(() => _values[key] = value);
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<WaterLookupsBloc, WaterLookupsState>(
      builder: (context, state) {
        List<WaterLookupItemEntity> stations = [];
        if (state is WaterLookupsLoaded) {
          stations = state.lookups.drinkingWaterStations;
          _selectedStation ??= stations.isNotEmpty ? stations.first : null;
        }

        return Directionality(
          textDirection: TextDirection.rtl,
          child: SingleChildScrollView(
            padding: EdgeInsets.all(14.r),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const GradientHeaderCard(
                    title: 'محطات مياه الشرب',
                    subtitle:
                        'استورد السجل الجغرافي ثم استمارة TEI، أو عدّل محطة واحدة يدوياً',
                    icon: Icons.local_drink_outlined,
                  ),
                  SizedBox(height: 12.h),
                  StatsGrid(
                    crossAxisCount: 3,
                    items: WaterImportStatusStats.drinkingTop(_importStatus),
                  ),
                  SizedBox(height: 8.h),
                  StatsGrid(
                    crossAxisCount: 3,
                    items: WaterImportStatusStats.drinkingBottom(_importStatus),
                  ),
                  SizedBox(height: 12.h),
                  ToggleTabRow(
                    isDailyEntry: _daily,
                    onChanged: (v) => setState(() => _daily = v),
                  ),
                  SizedBox(height: 12.h),
                  if (_daily) ...[
                    if (state is WaterLookupsLoading)
                      const FieldShimmer(label: 'اختر محطة مياه الشرب')
                    else if (state is WaterLookupsError)
                      Text(state.message,
                          style: const TextStyle(color: Colors.red))
                    else
                      FormCard(
                        child: AppDropdownField(
                          label: 'اختر محطة مياه الشرب',
                          value: _selectedStation?.name ?? '',
                          items: stations.map((e) => e.name).toList(),
                          onChanged: (v) {
                            if (v != null) {
                              setState(() {
                                _selectedStation =
                                    stations.firstWhere((e) => e.name == v);
                              });
                            }
                          },
                        ),
                      ),
                    SizedBox(height: 12.h),
                    DrinkingStationDefinitionSection(
                      stationName: _selectedStation?.name ?? '',
                      registrationDate: _registrationDate,
                      onDateChanged: (d) =>
                          setState(() => _registrationDate = d),
                      orgUnitController: _orgUnitCtrl,
                    ),
                    SizedBox(height: 12.h),
                    DrinkingOperationStatusSection(
                      values: _values,
                      onChanged: _onFieldChanged,
                      notOperatingReasonController: _notOperatingReasonCtrl,
                    ),
                    SizedBox(height: 12.h),
                    DrinkingEnergySupplySection(
                      values: _values,
                      onChanged: _onFieldChanged,
                    ),
                    SizedBox(height: 12.h),
                    DrinkingStationTypeSection(
                      values: _values,
                      onChanged: _onFieldChanged,
                    ),
                    SizedBox(height: 12.h),
                    DrinkingOtherInfoSection(
                      values: _values,
                      onChanged: _onFieldChanged,
                    ),
                    SizedBox(height: 12.h),
                    const DuplicateNote(),
                    SizedBox(height: 12.h),
                    SaveButton(
                      label: 'حفظ بيانات المحطة',
                      isLoading: _saving,
                      onPressed: _save,
                    ),
                  ] else ...[
                    DrinkingImportModeCard(
                      importSurvey: _importSurvey,
                      onChanged: (v) => setState(() => _importSurvey = v),
                    ),
                    SizedBox(height: 12.h),
                    FileImportPlaceholder(
                      note: _importSurvey
                          ? 'اسحب وأفلت ملفات استمارة TEI (.XLS / .XLSX / .ZIP)'
                          : 'اسحب وأفلت ملفات السجل الجغرافي (.XLS / .XLSX / .ZIP)',
                      onPickFiles: _importDrinkingWater,
                      onDownloadTemplate: () => downloadWaterTemplate(
                        context,
                        kind: _importSurvey
                            ? 'drinking-water-survey'
                            : 'drinking-water-geo',
                        fallbackName: _importSurvey
                            ? 'drinking-water-survey.xlsx'
                            : 'drinking-water-geo.xlsx',
                      ),
                      onExport: _importSurvey
                          ? () => exportDrinkingSurvey(context)
                          : null,
                      exportLabel: 'تصدير استمارة TEI',
                    ),
                  ],
                  SizedBox(height: 16.h),
                ]),
          ),
        );
      },
    );
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

  Future<void> _importDrinkingWater() async {
    final repo = getIt<WaterRepository>();
    setState(() => _saving = true);

    final files = await _pickMultipartFiles(
      allowedExtensions: ['xls', 'xlsx', 'zip'],
    );
    if (files.isEmpty) {
      setState(() => _saving = false);
      return;
    }

    final result = _importSurvey
        ? await repo.importDrinkingWaterSurvey(files: files)
        : await repo.importDrinkingWaterGeo(files: files, clear: false);
    setState(() => _saving = false);
    if (!mounted) return;

    if (result is Success<WaterImportResultEntity>) {
      final r = (result).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم استيراد بيانات مياه الشرب بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل استيراد بيانات مياه الشرب');
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
      if (r.ok) _loadImportStatus();
    } else if (result is Failure<WaterImportResultEntity>) {
      final e = (result).errorHandler;
      final msg = e.apiErrorModel.message ?? 'فشل استيراد بيانات مياه الشرب';
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

  Future<void> _save() async {
    if (_selectedStation == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'اختر محطة مياه الشرب أولاً',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
        ),
      );
      return;
    }

    final repo = getIt<WaterRepository>();
    setState(() => _saving = true);

    Map<String, dynamic>? payload;
    final stationRes =
        await repo.getDrinkingWaterStation(_selectedStation!.id);
    if (stationRes is Success<Map<String, dynamic>>) {
      payload = (stationRes).data;
    } else if (stationRes is Failure<Map<String, dynamic>>) {
      payload = null;
      final e = (stationRes).errorHandler;
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              e.apiErrorModel.message ?? 'فشل جلب بيانات المحطة',
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor: AppColors.red2,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
          ),
        );
      }
    }

    if (!mounted) return;
    if (payload == null) {
      setState(() => _saving = false);
      return;
    }

    applyFormToPayload(
      payload,
      stationId: _selectedStation!.id,
      registrationDate: _registrationDate,
      orgUnit: _orgUnitCtrl.text.trim(),
      values: _values,
      notOperatingReason: _notOperatingReasonCtrl.text,
    );

    final saveRes = await repo.saveDrinkingWaterStation(payload: payload);
    setState(() => _saving = false);
    if (!mounted) return;

    if (saveRes is Success<WaterImportResultEntity>) {
      final r = (saveRes).data;
      final msg = r.ok
          ? (r.messageAr ?? 'تم حفظ بيانات محطة مياه الشرب بنجاح')
          : (r.errorAr ?? r.errorEn ?? r.messageAr ?? 'فشل حفظ بيانات محطة مياه الشرب');
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
    } else if (saveRes is Failure<WaterImportResultEntity>) {
      final e = (saveRes).errorHandler;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.apiErrorModel.message ?? 'فشل حفظ بيانات محطة مياه الشرب',
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
