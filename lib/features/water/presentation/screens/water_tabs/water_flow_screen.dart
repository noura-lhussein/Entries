import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/di/injection.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/euphrates/euphrates_bloc.dart';
import '../../bloc/euphrates/euphrates_event.dart';
import '../../bloc/euphrates/euphrates_state.dart';
import '../../utils/water_import_status_stats.dart';
import '../../utils/water_snack.dart';
import '../../widgets/euphrates/euphrates_daily_form.dart';
import '../../widgets/euphrates/euphrates_import_panel.dart';
import '../../widgets/shared/water_tab_scaffold.dart';

class WaterFlowScreen extends StatelessWidget {
  const WaterFlowScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<EuphratesBloc>()..add(const EuphratesStarted()),
      child: const _WaterFlowView(),
    );
  }
}

class _WaterFlowView extends StatefulWidget {
  const _WaterFlowView();

  @override
  State<_WaterFlowView> createState() => _WaterFlowViewState();
}

class _WaterFlowViewState extends State<_WaterFlowView> {
  final _titleCtrl = TextEditingController();
  final _tInCtrl = TextEditingController();
  final _tLvlCtrl = TextEditingController();
  final _tStorCtrl = TextEditingController();
  final _tGenCtrl = TextEditingController();
  final _fLvlCtrl = TextEditingController();
  final _fStorCtrl = TextEditingController();
  final _fGenCtrl = TextEditingController();
  final _kGenCtrl = TextEditingController();
  final _totCtrl = TextEditingController();

  @override
  void dispose() {
    for (final c in [
      _titleCtrl,
      _tInCtrl,
      _tLvlCtrl,
      _tStorCtrl,
      _tGenCtrl,
      _fLvlCtrl,
      _fStorCtrl,
      _fGenCtrl,
      _kGenCtrl,
      _totCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  void _applyReading(Map<String, dynamic>? reading) {
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
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<EuphratesBloc, EuphratesState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenWaterFeedback(context, null, state.feedback),
        ),
        BlocListener<EuphratesBloc, EuphratesState>(
          listenWhen: (p, c) => p.reading != c.reading,
          listener: (_, state) => _applyReading(state.reading),
        ),
      ],
      child: WaterTabScaffold(
        children: [
          const GradientHeaderCard(
            title: 'سلسلة سدود الفرات',
            subtitle:
                'قراءات الوارد والمنسوب والتوليد لسدود تشرين والفرات وكديران',
            icon: Icons.waves_outlined,
          ),
          SizedBox(height: 12.h),
          BlocSelector<EuphratesBloc, EuphratesState, Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) =>
                StatsGrid(items: WaterImportStatusStats.euphrates(status)),
          ),
          SizedBox(height: 12.h),
          BlocSelector<EuphratesBloc, EuphratesState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => ToggleTabRow(
              isDailyEntry: isDaily,
              onChanged: (v) => context
                  .read<EuphratesBloc>()
                  .add(EuphratesDailyModeToggled(v)),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<EuphratesBloc, EuphratesState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => isDaily
                ? EuphratesDailyForm(
                    titleController: _titleCtrl,
                    tishreenInflowController: _tInCtrl,
                    tishreenLevelController: _tLvlCtrl,
                    tishreenStorageController: _tStorCtrl,
                    tishreenGenerationController: _tGenCtrl,
                    furatLevelController: _fLvlCtrl,
                    furatStorageController: _fStorCtrl,
                    furatGenerationController: _fGenCtrl,
                    kadiranGenerationController: _kGenCtrl,
                    totalController: _totCtrl,
                  )
                : const EuphratesImportPanel(),
          ),
        ],
      ),
    );
  }
}
