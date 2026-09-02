import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../../../core/widgets/excel_entry_bar.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../domain/entities/ore_product_option.dart';
import '../../domain/services/geology_ore_math.dart';
import '../../domain/utils/parse_geology_number.dart';
import '../bloc/ore/geology_ore_bloc.dart';
import '../bloc/ore/geology_ore_event.dart';
import '../bloc/ore/geology_ore_state.dart';
import '../utils/geology_snack.dart';
import '../widgets/geology_entry/geology_ore_form_models.dart';
import '../widgets/geology_entry/geology_ore_grouping.dart';
import '../widgets/geology_entry/geology_ore_section.dart';

class GeologyOreDailyScreen extends StatelessWidget {
  const GeologyOreDailyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) =>
          getIt<GeologyOreBloc>()..add(const GeologyOreStarted()),
      child: const _GeologyOreDailyView(),
    );
  }
}

class _GeologyOreDailyView extends StatefulWidget {
  const _GeologyOreDailyView();

  @override
  State<_GeologyOreDailyView> createState() => _GeologyOreDailyViewState();
}

class _GeologyOreDailyViewState extends State<_GeologyOreDailyView> {
  List<OreProductGroup> _groups = [OreProductGroup()];
  String _oreToAdd = '';

  @override
  void dispose() {
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

  void _onH1Changed(OreTypeLine line) {
    final pct = executionPct(
      parseGeologyNum(line.h1PlanCtrl.text),
      parseGeologyNum(line.h1ExecCtrl.text),
    );
    if (pct != null) line.pctCtrl.text = '$pct';
  }

  void _addOreGroup() {
    final found = findOreProduct(_oreToAdd);
    if (found == null) return;
    setState(() {
      _groups.add(OreProductGroup(
        productNameAr: found.nameAr,
        productNameEn: found.nameEn,
      ));
      _oreToAdd = '';
    });
  }

  void _removeOreGroup(int gi) {
    if (gi < 0 || gi >= _groups.length) return;
    setState(() {
      _groups.removeAt(gi).dispose();
      if (_groups.isEmpty) _groups.add(OreProductGroup());
    });
  }

  void _addTypeLine(int gi) {
    setState(() => _groups[gi].lines.add(OreTypeLine()));
  }

  void _removeTypeLine(int gi, int li) {
    final lines = _groups[gi].lines;
    if (li <= 0 || li >= lines.length) return;
    setState(() => lines.removeAt(li).dispose());
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
    context.read<GeologyOreBloc>().add(GeologyOreImportRequested(file));
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<GeologyOreBloc, GeologyOreState>(
          listenWhen: (p, c) => p.reportApplyToken != c.reportApplyToken,
          listener: (context, state) {
            final detail = state.reportDetail;
            setState(() {
              _replaceGroups(groupOreRows(
                detail == null ? const [] : extractGeologyOreRows(detail),
              ));
            });
          },
        ),
        BlocListener<GeologyOreBloc, GeologyOreState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenGeologyFeedback(context, state.feedback),
        ),
        BlocListener<GeologyOreBloc, GeologyOreState>(
          listenWhen: (p, c) => p.downloadedFile != c.downloadedFile,
          listener: (context, state) async {
            final res = state.downloadedFile;
            final bytes = res?.data;
            if (res == null || bytes == null || bytes.isEmpty) return;
            await saveAndOpenBytes(
              bytes,
              filename: filenameFromResponse(res, state.downloadFallbackName),
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
                title: 'إنتاج الخامات المعدنية',
                subtitle:
                    'إدخال المخطط والمنفذ والعقود والاحتياطي لكل خام',
                icon: Icons.diamond_outlined,
              ),
              SizedBox(height: 12.h),
              BlocBuilder<GeologyOreBloc, GeologyOreState>(
                buildWhen: (p, c) =>
                    p.downloading != c.downloading ||
                    p.importing != c.importing,
                builder: (context, state) => ExcelEntryBar(
                  hint:
                      'نزّل القالب، املأ القيم، ثم ارفع الملف لاستيراد إنتاج الخامات.',
                  downloading: state.downloading,
                  importing: state.importing,
                  onDownload: () => context.read<GeologyOreBloc>().add(
                        const GeologyOreDownloadTemplateRequested(),
                      ),
                  onExport: () => context
                      .read<GeologyOreBloc>()
                      .add(const GeologyOreExportRequested()),
                  onUpload: _pickImport,
                ),
              ),
              SizedBox(height: 12.h),
              BlocBuilder<GeologyOreBloc, GeologyOreState>(
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
                                    .read<GeologyOreBloc>()
                                    .add(const GeologyOreLoadRequested()),
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
              BlocBuilder<GeologyOreBloc, GeologyOreState>(
                buildWhen: (p, c) => p.date != c.date || p.loading != c.loading,
                builder: (context, state) => FormCard(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      DatePickerField(
                        key: ValueKey(geologyIsoDate(state.date)),
                        label: 'تاريخ التقرير',
                        initialDate: state.date,
                        onDateChanged: (d) => context
                            .read<GeologyOreBloc>()
                            .add(GeologyOreDateChanged(d)),
                      ),
                      if (state.loading) ...[
                        SizedBox(height: 8.h),
                        const LinearProgressIndicator(minHeight: 2),
                      ],
                    ],
                  ),
                ),
              ),
              SizedBox(height: 12.h),
              BlocSelector<GeologyOreBloc, GeologyOreState, int>(
                selector: (s) => s.planYear,
                builder: (context, planYear) => GeologyOreSection(
                  groups: _groups,
                  oreToAdd: _oreToAdd,
                  planYear: planYear,
                  onOreToAddChanged: (v) => setState(() => _oreToAdd = v),
                  onAddOreGroup: _addOreGroup,
                  onRemoveOreGroup: _removeOreGroup,
                  onAddTypeLine: _addTypeLine,
                  onRemoveTypeLine: _removeTypeLine,
                  onH1Changed: _onH1Changed,
                  onChanged: () => setState(() {}),
                ),
              ),
              SizedBox(height: 12.h),
              BlocSelector<GeologyOreBloc, GeologyOreState, bool>(
                selector: (s) => s.publish,
                builder: (context, publish) => FormCard(
                  child: InkWell(
                    onTap: () => context
                        .read<GeologyOreBloc>()
                        .add(GeologyOrePublishToggled(!publish)),
                    child: Row(children: [
                      Checkbox(
                        value: publish,
                        activeColor: AppColors.forest1,
                        onChanged: (v) => context
                            .read<GeologyOreBloc>()
                            .add(GeologyOrePublishToggled(v ?? true)),
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
              BlocSelector<GeologyOreBloc, GeologyOreState, bool>(
                selector: (s) => s.saving,
                builder: (context, saving) => SaveButton(
                  isLoading: saving,
                  label: 'حفظ التقرير اليومي',
                  onPressed: () => context.read<GeologyOreBloc>().add(
                        GeologyOreSaveRequested(flattenOreGroups(_groups)),
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
