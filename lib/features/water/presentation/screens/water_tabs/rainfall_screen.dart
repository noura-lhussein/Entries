import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/di/injection.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/rainfall/rainfall_bloc.dart';
import '../../bloc/rainfall/rainfall_event.dart';
import '../../bloc/rainfall/rainfall_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_event.dart';
import '../../utils/water_import_status_stats.dart';
import '../../utils/water_snack.dart';
import '../../widgets/rainfall/rainfall_daily_form.dart';
import '../../widgets/rainfall/rainfall_import_panel.dart';
import '../../widgets/shared/water_tab_scaffold.dart';

class RainfallScreen extends StatelessWidget {
  const RainfallScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) =>
              getIt<WaterLookupsBloc>()..add(const GetWaterLookupsStarted()),
        ),
        BlocProvider(
          create: (_) => getIt<RainfallBloc>()..add(const RainfallStarted()),
        ),
      ],
      child: const _RainfallView(),
    );
  }
}

class _RainfallView extends StatefulWidget {
  const _RainfallView();

  @override
  State<_RainfallView> createState() => _RainfallViewState();
}

class _RainfallViewState extends State<_RainfallView> {
  final _rfCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();

  @override
  void dispose() {
    _rfCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<RainfallBloc, RainfallState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenWaterFeedback(context, null, state.feedback),
        ),
        BlocListener<RainfallBloc, RainfallState>(
          listenWhen: (p, c) => p.formResetToken != c.formResetToken,
          listener: (_, __) {
            _rfCtrl.clear();
            _notesCtrl.clear();
          },
        ),
      ],
      child: WaterTabScaffold(
        children: [
          const GradientHeaderCard(
            title: 'تحليل الهطول',
            subtitle: 'ملفات .xls لمحطات الأحواض أو إدخال يومي للمحطة',
            icon: Icons.grain_outlined,
          ),
          SizedBox(height: 12.h),
          BlocSelector<RainfallBloc, RainfallState, Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) => StatsGrid(
              crossAxisCount: 3,
              items: WaterImportStatusStats.rainfallTop(status),
            ),
          ),
          SizedBox(height: 8.h),
          BlocSelector<RainfallBloc, RainfallState, Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) => StatsGrid(
              items: WaterImportStatusStats.rainfallBottom(status),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<RainfallBloc, RainfallState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => ToggleTabRow(
              isDailyEntry: isDaily,
              onChanged: (v) => context
                  .read<RainfallBloc>()
                  .add(RainfallDailyModeToggled(v)),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<RainfallBloc, RainfallState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => isDaily
                ? RainfallDailyForm(
                    precipitationController: _rfCtrl,
                    notesController: _notesCtrl,
                  )
                : const RainfallImportPanel(),
          ),
        ],
      ),
    );
  }
}
