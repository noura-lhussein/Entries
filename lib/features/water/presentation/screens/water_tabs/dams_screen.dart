import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/di/injection.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/dams/dams_bloc.dart';
import '../../bloc/dams/dams_event.dart';
import '../../bloc/dams/dams_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_event.dart';
import '../../utils/water_import_status_stats.dart';
import '../../utils/water_snack.dart';
import '../../widgets/dams/dams_daily_form.dart';
import '../../widgets/dams/dams_import_panel.dart';
import '../../widgets/shared/water_tab_scaffold.dart';

class DamsScreen extends StatelessWidget {
  const DamsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) =>
              getIt<WaterLookupsBloc>()..add(const GetWaterLookupsStarted()),
        ),
        BlocProvider(
          create: (_) => getIt<DamsBloc>()..add(const DamsStarted()),
        ),
      ],
      child: const _DamsView(),
    );
  }
}

class _DamsView extends StatefulWidget {
  const _DamsView();

  @override
  State<_DamsView> createState() => _DamsViewState();
}

class _DamsViewState extends State<_DamsView> {
  final _storCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();

  @override
  void dispose() {
    _storCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<DamsBloc, DamsState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenWaterFeedback(context, null, state.feedback),
        ),
        BlocListener<DamsBloc, DamsState>(
          listenWhen: (p, c) => p.formResetToken != c.formResetToken,
          listener: (_, __) {
            _storCtrl.clear();
            _notesCtrl.clear();
          },
        ),
      ],
      child: WaterTabScaffold(
        children: [
          const GradientHeaderCard(
            title: 'معلومات السدود',
            subtitle: 'قراءات المخزون اليومية + ملفات .XLS السنوية',
            icon: Icons.water_damage_outlined,
          ),
          SizedBox(height: 12.h),
          BlocSelector<DamsBloc, DamsState, Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) =>
                StatsGrid(items: WaterImportStatusStats.dams(status)),
          ),
          SizedBox(height: 12.h),
          BlocSelector<DamsBloc, DamsState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => ToggleTabRow(
              isDailyEntry: isDaily,
              onChanged: (v) =>
                  context.read<DamsBloc>().add(DamsDailyModeToggled(v)),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<DamsBloc, DamsState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => isDaily
                ? DamsDailyForm(
                    storageController: _storCtrl,
                    notesController: _notesCtrl,
                  )
                : const DamsImportPanel(),
          ),
        ],
      ),
    );
  }
}
