import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../../../core/widgets/excel_entry_bar.dart';
import '../../../../core/widgets/report_dates_chips.dart';
import '../../data/datasources/electricity_remote_data_source.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';
import '../utils/electricity_report_codec.dart';
import '../widgets/dynamic_rows_section.dart';
import '../widgets/electricity_daily_form.dart';
import '../widgets/electricity_header.dart';
import '../widgets/models/electricity_fields_data.dart';

class ElectricityScreen extends StatelessWidget {
  const ElectricityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ElectricityBloc(),
      child: const _ElectricityView(),
    );
  }
}

class _ElectricityView extends StatefulWidget {
  const _ElectricityView();

  @override
  State<_ElectricityView> createState() => _ElectricityViewState();
}

class _ElectricityViewState extends State<_ElectricityView> {
  // Flat value fields (generation indicators + fuel & gas + load & incidents)
  // all share one controller map, keyed by their unique field key.
  final Map<String, TextEditingController> _fieldCtrls = {
    for (final f in kAllElectricityMetricFields) f.key: TextEditingController(),
  };

  final Map<String, TextEditingController> _consumedCtrls = {
    for (final g in kGovernorates) g.code: TextEditingController(),
  };
  final Map<String, TextEditingController> _allocatedCtrls = {
    for (final g in kGovernorates) g.code: TextEditingController(),
  };
  final Map<String, TextEditingController> _tankCtrls = {
    for (final t in kFuelTanks) t.code: TextEditingController(),
  };
  final Map<String, TextEditingController> _tankMaxCtrls = {
    for (final t in kFuelTanks)
      t.code: TextEditingController(text: '${t.maxCapacity?.toInt() ?? ''}'),
  };
  final Map<String, TextEditingController> _hydraulicCtrls = {
    for (final dam in kHydraulicDams)
      for (final f in kHydraulicFields)
        '${dam.code}_${f.key}': TextEditingController(),
  };

  final _arabicNotesCtrl = TextEditingController();
  final _englishNotesCtrl = TextEditingController();
  final _maintKey = GlobalKey<DynamicRowsSectionState>();
  final _genIncKey = GlobalKey<DynamicRowsSectionState>();
  final _gridIncKey = GlobalKey<DynamicRowsSectionState>();
  List<String> _reportDates = const [];
  var _downloading = false;
  var _importing = false;

  @override
  void initState() {
    super.initState();
    _bootstrapDates();
  }

  Future<void> _bootstrapDates() async {
    try {
      final raw = await getIt<ElectricityRemoteDataSource>().getReportDates();
      final dates =
          raw.map((e) => e.toString()).where((e) => e.isNotEmpty).toList();
      if (!mounted || dates.isEmpty) return;
      final parsed = DateTime.tryParse(dates.first);
      setState(() => _reportDates = dates);
      if (parsed != null) {
        context.read<ElectricityBloc>().add(ReportDateChanged(parsed));
        await _loadReport(parsed);
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    for (final c in _fieldCtrls.values) {
      c.dispose();
    }
    for (final c in _consumedCtrls.values) {
      c.dispose();
    }
    for (final c in _allocatedCtrls.values) {
      c.dispose();
    }
    for (final c in _tankCtrls.values) {
      c.dispose();
    }
    for (final c in _tankMaxCtrls.values) {
      c.dispose();
    }
    for (final c in _hydraulicCtrls.values) {
      c.dispose();
    }
    _arabicNotesCtrl.dispose();
    _englishNotesCtrl.dispose();
    super.dispose();
  }

  Future<void> _downloadTemplate() async {
    setState(() => _downloading = true);
    try {
      final ds = getIt<ElectricityRemoteDataSource>();
      final date = fmtDate(context.read<ElectricityBloc>().state.reportDate);
      final res = await ds.downloadReportTemplate(date: date);
      final bytes = res.data;
      if (bytes == null || bytes.isEmpty) throw Exception('empty');
      await saveAndOpenBytes(
        bytes,
        filename: filenameFromResponse(res, 'electricity_daily_report_template.xlsx'),
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
      final ds = getIt<ElectricityRemoteDataSource>();
      final publish = context.read<ElectricityBloc>().state.publishAfterSave;
      final imported = await ds.importDailyReport(file, publish: publish);
      final dateStr = imported['report_date']?.toString();
      final parsed = dateStr == null ? null : DateTime.tryParse(dateStr);
      if (!mounted) return;
      if (parsed != null) {
        context.read<ElectricityBloc>().add(ReportDateChanged(parsed));
        await _loadReport(parsed);
      }
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

  Future<void> _loadReport(DateTime date) async {
    try {
      final ds = getIt<ElectricityRemoteDataSource>();
      final detail = await ds.getReportDetail(fmtDate(date));
      final applied = applyReportDetail(
        detail,
        fieldCtrls: _fieldCtrls,
        consumedCtrls: _consumedCtrls,
        allocatedCtrls: _allocatedCtrls,
        tankCtrls: _tankCtrls,
        tankMaxCtrls: _tankMaxCtrls,
        hydraulicCtrls: _hydraulicCtrls,
        arabicNotesCtrl: _arabicNotesCtrl,
        englishNotesCtrl: _englishNotesCtrl,
      );
      if (!mounted) return;
      final bloc = context.read<ElectricityBloc>();
      if (applied.peak != null) bloc.add(PeakTimeChanged(applied.peak!));
      bloc.add(DynamicRowsReplaced(
          DynamicSectionType.maintenance, applied.maintenanceRows));
      bloc.add(DynamicRowsReplaced(
          DynamicSectionType.generationIncidents,
          applied.generationIncidentRows));
      bloc.add(DynamicRowsReplaced(
          DynamicSectionType.lineIncidents, applied.gridIncidentRows));
      setState(() {});
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            userFacingErrorMessage(
              e,
              fallback: 'تعذر تحميل تقرير الكهرباء لهذا التاريخ',
            ),
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
        ),
      );
    }
  }

  void _onSave(ElectricityState state) {
    context.read<ElectricityBloc>().add(
          ReportSaveRequested(
            buildPayload(
              state: state,
              fieldCtrls: _fieldCtrls,
              consumedCtrls: _consumedCtrls,
              allocatedCtrls: _allocatedCtrls,
              tankCtrls: _tankCtrls,
              tankMaxCtrls: _tankMaxCtrls,
              hydraulicCtrls: _hydraulicCtrls,
              arabicNotesCtrl: _arabicNotesCtrl,
              englishNotesCtrl: _englishNotesCtrl,
              generationIncidentRows:
                  _genIncKey.currentState?.collectRows() ?? const [],
              gridIncidentRows:
                  _gridIncKey.currentState?.collectRows() ?? const [],
              maintenanceRows:
                  _maintKey.currentState?.collectRows() ?? const [],
            ),
          ),
        );
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<ElectricityBloc, ElectricityState>(
      listenWhen: (p, c) => p.saveStatus != c.saveStatus,
      listener: (context, state) {
        if (state.saveStatus == SaveStatus.success) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'تم حفظ التقرير اليومي بنجاح',
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
              ),
              backgroundColor: AppColors.forest1,
            ),
          );
        } else if (state.saveStatus == SaveStatus.failure) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'تعذر حفظ التقرير. تحقق من الاتصال وحاول مجدداً.',
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
              ),
              backgroundColor: AppColors.red2,
            ),
          );
        }
      },
      child: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const ElectricityHeader(),
              SizedBox(height: 14.h),
              ExcelEntryBar(
                hint:
                    'نزّل القالب، املأ القيم، ثم ارفع الملف لاستيراد التقرير.',
                downloading: _downloading,
                importing: _importing,
                onDownload: _downloadTemplate,
                onUpload: _importExcel,
              ),
              SizedBox(height: 14.h),
              if (_reportDates.isNotEmpty) ...[
                BlocBuilder<ElectricityBloc, ElectricityState>(
                  buildWhen: (p, c) => p.reportDate != c.reportDate,
                  builder: (context, state) => ReportDatesChips(
                    dates: _reportDates,
                    selected: fmtDate(state.reportDate),
                    accent: AppColors.successGreen,
                    onSelected: (d) {
                      final parsed = DateTime.tryParse(d);
                      if (parsed == null) return;
                      context
                          .read<ElectricityBloc>()
                          .add(ReportDateChanged(parsed));
                      _loadReport(parsed);
                    },
                  ),
                ),
                SizedBox(height: 14.h),
              ],
              ElectricityDailyForm(
                fieldCtrls: _fieldCtrls,
                consumedCtrls: _consumedCtrls,
                allocatedCtrls: _allocatedCtrls,
                tankCtrls: _tankCtrls,
                tankMaxCtrls: _tankMaxCtrls,
                hydraulicCtrls: _hydraulicCtrls,
                arabicNotesCtrl: _arabicNotesCtrl,
                englishNotesCtrl: _englishNotesCtrl,
                maintKey: _maintKey,
                genIncKey: _genIncKey,
                gridIncKey: _gridIncKey,
                onDateChanged: _loadReport,
                onSave: _onSave,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
