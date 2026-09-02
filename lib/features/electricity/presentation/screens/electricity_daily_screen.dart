import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';
import '../utils/electricity_form_controllers.dart';
import '../utils/electricity_report_codec.dart';
import '../widgets/dynamic_rows_section.dart';
import '../widgets/electricity_daily_form.dart';
import '../widgets/electricity_header.dart';

class ElectricityDailyScreen extends StatelessWidget {
  const ElectricityDailyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ElectricityBloc>()
        ..add(const ElectricityStarted())
        ..add(const LoadReportRequested()),
      child: const _ElectricityDailyView(),
    );
  }
}

class _ElectricityDailyView extends StatefulWidget {
  const _ElectricityDailyView();

  @override
  State<_ElectricityDailyView> createState() => _ElectricityDailyViewState();
}

class _ElectricityDailyViewState extends State<_ElectricityDailyView> {
  late final ElectricityFormControllers _ctrls;
  final _maintKey = GlobalKey<DynamicRowsSectionState>();
  final _genIncKey = GlobalKey<DynamicRowsSectionState>();
  final _gridIncKey = GlobalKey<DynamicRowsSectionState>();

  @override
  void initState() {
    super.initState();
    _ctrls = ElectricityFormControllers();
  }

  @override
  void dispose() {
    _ctrls.dispose();
    super.dispose();
  }

  void _applyDetail(Map<String, dynamic> detail) {
    final applied = applyReportDetail(
      detail,
      fieldCtrls: _ctrls.fieldCtrls,
      consumedCtrls: _ctrls.consumedCtrls,
      allocatedCtrls: _ctrls.allocatedCtrls,
      tankCtrls: _ctrls.tankCtrls,
      tankMaxCtrls: _ctrls.tankMaxCtrls,
      hydraulicCtrls: _ctrls.hydraulicCtrls,
      arabicNotesCtrl: _ctrls.arabicNotesCtrl,
      englishNotesCtrl: _ctrls.englishNotesCtrl,
    );
    final bloc = context.read<ElectricityBloc>();
    bloc.add(PeakTimeChanged(applied.peak));
    bloc.add(DynamicRowsReplaced(
      DynamicSectionType.maintenance,
      applied.maintenanceRows,
    ));
    bloc.add(DynamicRowsReplaced(
      DynamicSectionType.generationIncidents,
      applied.generationIncidentRows,
    ));
    bloc.add(DynamicRowsReplaced(
      DynamicSectionType.lineIncidents,
      applied.gridIncidentRows,
    ));
  }

  void _save(ElectricityState state) {
    context.read<ElectricityBloc>().add(
          ReportSaveRequested(
            buildPayload(
              state: state,
              fieldCtrls: _ctrls.fieldCtrls,
              consumedCtrls: _ctrls.consumedCtrls,
              allocatedCtrls: _ctrls.allocatedCtrls,
              tankCtrls: _ctrls.tankCtrls,
              tankMaxCtrls: _ctrls.tankMaxCtrls,
              hydraulicCtrls: _ctrls.hydraulicCtrls,
              arabicNotesCtrl: _ctrls.arabicNotesCtrl,
              englishNotesCtrl: _ctrls.englishNotesCtrl,
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
    return MultiBlocListener(
      listeners: [
        BlocListener<ElectricityBloc, ElectricityState>(
          listenWhen: (p, c) => p.reportApplyToken != c.reportApplyToken,
          listener: (context, state) {
            final detail = state.reportDetail;
            if (detail != null) _applyDetail(detail);
          },
        ),
        BlocListener<ElectricityBloc, ElectricityState>(
          listenWhen: (p, c) =>
              p.saveStatus != c.saveStatus &&
              (c.saveStatus == SaveStatus.success ||
                  c.saveStatus == SaveStatus.failure),
          listener: (context, state) {
            final ok = state.saveStatus == SaveStatus.success;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  ok
                      ? 'تم حفظ التقرير اليومي بنجاح'
                      : 'فشل حفظ التقرير اليومي',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
                ),
                backgroundColor: ok ? AppColors.forest1 : AppColors.red2,
                behavior: SnackBarBehavior.floating,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8.r),
                ),
              ),
            );
          },
        ),
      ],
      child: Directionality(
        textDirection: TextDirection.rtl,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(14.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const ElectricityHeader(),
              SizedBox(height: 12.h),
              ElectricityDailyForm(
                fieldCtrls: _ctrls.fieldCtrls,
                consumedCtrls: _ctrls.consumedCtrls,
                allocatedCtrls: _ctrls.allocatedCtrls,
                tankCtrls: _ctrls.tankCtrls,
                tankMaxCtrls: _ctrls.tankMaxCtrls,
                hydraulicCtrls: _ctrls.hydraulicCtrls,
                arabicNotesCtrl: _ctrls.arabicNotesCtrl,
                englishNotesCtrl: _ctrls.englishNotesCtrl,
                maintKey: _maintKey,
                genIncKey: _genIncKey,
                gridIncKey: _gridIncKey,
                onDateChanged: (_) => context
                    .read<ElectricityBloc>()
                    .add(const LoadReportRequested()),
                onSave: _save,
              ),
              SizedBox(height: 16.h),
            ],
          ),
        ),
      ),
    );
  }
}
