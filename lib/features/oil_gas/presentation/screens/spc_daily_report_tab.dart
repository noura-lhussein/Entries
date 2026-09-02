import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../../../core/widgets/excel_entry_bar.dart';
import '../../../../core/widgets/report_dates_chips.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../domain/utils/parse_oil_gas_number.dart';
import '../bloc/spc/spc_report_bloc.dart';
import '../bloc/spc/spc_report_event.dart';
import '../bloc/spc/spc_report_state.dart';
import '../utils/petroleum_snack.dart';
import '../widgets/models/petroleum_data.dart';
import '../widgets/spc_report_table.dart';

class SpcDailyReportTab extends StatelessWidget {
  const SpcDailyReportTab({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<SpcReportBloc>()..add(const SpcReportStarted()),
      child: const _SpcDailyReportView(),
    );
  }
}

class _SpcDailyReportView extends StatefulWidget {
  const _SpcDailyReportView();

  @override
  State<_SpcDailyReportView> createState() => _SpcDailyReportViewState();
}

class _SpcDailyReportViewState extends State<_SpcDailyReportView> {
  final _notesCtrl = TextEditingController();
  final Map<String, TextEditingController> _ctrls = {
    for (final r in kSpcRows) r.key: TextEditingController(),
  };

  @override
  void dispose() {
    _notesCtrl.dispose();
    for (final c in _ctrls.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _applyDetail(Map<String, dynamic> detail) {
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
  }

  Future<void> _pickImport() async {
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
    if (!mounted) return;
    context.read<SpcReportBloc>().add(SpcReportImportRequested(file));
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<SpcReportBloc, SpcReportState>(
          listenWhen: (p, c) => p.reportApplyToken != c.reportApplyToken,
          listener: (context, state) {
            final detail = state.reportDetail;
            if (detail != null) _applyDetail(detail);
          },
        ),
        BlocListener<SpcReportBloc, SpcReportState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenPetroleumFeedback(context, state.feedback),
        ),
        BlocListener<SpcReportBloc, SpcReportState>(
          listenWhen: (p, c) => p.downloadedFile != c.downloadedFile,
          listener: (context, state) async {
            final res = state.downloadedFile;
            final bytes = res?.data;
            if (res == null || bytes == null || bytes.isEmpty) return;
            await saveAndOpenBytes(
              bytes,
              filename: filenameFromResponse(
                res,
                'oil_gas_executive_report_template.xlsx',
              ),
            );
          },
        ),
      ],
      child: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.all(14.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const GradientHeaderCard(
                title: 'التقرير اليومي',
                subtitle:
                    'إدخال بيانات التقرير اليومي التنفيذي لقطاع البترول ومشتقاته',
                icon: Icons.oil_barrel_outlined,
              ),
              SizedBox(height: 12.h),
              BlocBuilder<SpcReportBloc, SpcReportState>(
                buildWhen: (p, c) =>
                    p.downloading != c.downloading ||
                    p.importing != c.importing,
                builder: (context, state) => ExcelEntryBar(
                  hint: 'نزّل القالب، املأ القيم، ثم ارفع الملف لاستيراد التقرير.',
                  downloading: state.downloading,
                  importing: state.importing,
                  onDownload: () => context
                      .read<SpcReportBloc>()
                      .add(const SpcReportDownloadTemplateRequested()),
                  onUpload: _pickImport,
                ),
              ),
              SizedBox(height: 12.h),
              BlocBuilder<SpcReportBloc, SpcReportState>(
                buildWhen: (p, c) =>
                    p.reportDates != c.reportDates || p.date != c.date,
                builder: (context, state) => ReportDatesChips(
                  dates: state.reportDates,
                  selected: oilGasIsoDate(state.date),
                  onSelected: (d) {
                    final parsed = DateTime.tryParse(d);
                    if (parsed == null) return;
                    context
                        .read<SpcReportBloc>()
                        .add(SpcReportDateChanged(parsed));
                  },
                ),
              ),
              BlocSelector<SpcReportBloc, SpcReportState, bool>(
                selector: (s) => s.reportDates.isNotEmpty,
                builder: (context, hasDates) =>
                    hasDates ? SizedBox(height: 12.h) : const SizedBox.shrink(),
              ),
              BlocBuilder<SpcReportBloc, SpcReportState>(
                buildWhen: (p, c) => p.loadError != c.loadError,
                builder: (context, state) {
                  if (state.loadError == null) return const SizedBox.shrink();
                  return Column(
                    children: [
                      Material(
                        color: AppColors.red2.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(10.r),
                        child: Padding(
                          padding: EdgeInsets.all(12.r),
                          child: Row(
                            children: [
                              Icon(Icons.error_outline,
                                  color: AppColors.red2, size: 20.r),
                              SizedBox(width: 8.w),
                              Expanded(
                                child: Text(
                                  state.loadError!,
                                  style: TextStyle(
                                    fontFamily: 'Cairo',
                                    fontSize: 12.sp,
                                    color: AppColors.red2,
                                  ),
                                ),
                              ),
                              TextButton(
                                onPressed: () => context
                                    .read<SpcReportBloc>()
                                    .add(const SpcReportLoadRequested()),
                                child: const Text('إعادة'),
                              ),
                            ],
                          ),
                        ),
                      ),
                      SizedBox(height: 12.h),
                    ],
                  );
                },
              ),
              BlocBuilder<SpcReportBloc, SpcReportState>(
                buildWhen: (p, c) => p.date != c.date || p.loading != c.loading,
                builder: (context, state) => FormCard(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      DatePickerField(
                        key: ValueKey(oilGasIsoDate(state.date)),
                        label: 'تاريخ التقرير',
                        initialDate: state.date,
                        onDateChanged: (d) => context
                            .read<SpcReportBloc>()
                            .add(SpcReportDateChanged(d)),
                      ),
                      if (state.loading) ...[
                        SizedBox(height: 8.h),
                        const LinearProgressIndicator(minHeight: 2),
                      ],
                      SizedBox(height: 8.h),
                      Text(
                        'الموضوع: التقرير اليومي لتاريخ ${state.date.day}/${state.date.month}/${state.date.year}',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              SizedBox(height: 12.h),
              BlocSelector<SpcReportBloc, SpcReportState, DateTime>(
                selector: (s) => s.date,
                builder: (context, date) =>
                    SpcReportTable(controllers: _ctrls, reportDate: date),
              ),
              SizedBox(height: 12.h),
              FormCard(
                child: AppTextField(
                  label: 'ملاحظات (عربي)',
                  controller: _notesCtrl,
                  maxLines: 4,
                ),
              ),
              SizedBox(height: 12.h),
              BlocSelector<SpcReportBloc, SpcReportState, bool>(
                selector: (s) => s.publish,
                builder: (context, publish) => FormCard(
                  child: InkWell(
                    onTap: () => context
                        .read<SpcReportBloc>()
                        .add(SpcReportPublishToggled(!publish)),
                    child: Row(children: [
                      Checkbox(
                        value: publish,
                        activeColor: AppColors.forest1,
                        onChanged: (v) => context
                            .read<SpcReportBloc>()
                            .add(SpcReportPublishToggled(v ?? true)),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(4.r),
                        ),
                      ),
                      Expanded(
                        child: Text(
                          'نشر التقرير بعد الحفظ',
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 12.sp,
                            color: AppColors.textPrimary,
                          ),
                        ),
                      ),
                    ]),
                  ),
                ),
              ),
              SizedBox(height: 12.h),
              BlocSelector<SpcReportBloc, SpcReportState, bool>(
                selector: (s) => s.saving,
                builder: (context, saving) => SaveButton(
                  isLoading: saving,
                  label: 'حفظ التقرير اليومي',
                  onPressed: () => context.read<SpcReportBloc>().add(
                        SpcReportSaveRequested(
                          metricTexts: {
                            for (final e in _ctrls.entries) e.key: e.value.text,
                          },
                          notesAr: _notesCtrl.text,
                        ),
                      ),
                ),
              ),
              SizedBox(height: 16.h),
            ],
          ),
        ),
      ),
    );
  }
}
