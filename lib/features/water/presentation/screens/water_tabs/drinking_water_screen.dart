import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/di/injection.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/drinking_water/drinking_water_bloc.dart';
import '../../bloc/drinking_water/drinking_water_event.dart';
import '../../bloc/drinking_water/drinking_water_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_event.dart';
import '../../utils/water_import_status_stats.dart';
import '../../utils/water_snack.dart';
import '../../widgets/drinking_water/drinking_water_daily_form.dart';
import '../../widgets/drinking_water/drinking_water_import_panel.dart';
import '../../widgets/shared/water_tab_scaffold.dart';

class DrinkingWaterScreen extends StatelessWidget {
  const DrinkingWaterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) =>
              getIt<WaterLookupsBloc>()..add(const GetWaterLookupsStarted()),
        ),
        BlocProvider(
          create: (_) =>
              getIt<DrinkingWaterBloc>()..add(const DrinkingWaterStarted()),
        ),
      ],
      child: const _DrinkingWaterView(),
    );
  }
}

class _DrinkingWaterView extends StatefulWidget {
  const _DrinkingWaterView();

  @override
  State<_DrinkingWaterView> createState() => _DrinkingWaterViewState();
}

class _DrinkingWaterViewState extends State<_DrinkingWaterView> {
  final _orgUnitCtrl = TextEditingController();
  final _notOperatingReasonCtrl = TextEditingController(text: 'سرقة وتخريب');

  @override
  void dispose() {
    _orgUnitCtrl.dispose();
    _notOperatingReasonCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<DrinkingWaterBloc, DrinkingWaterState>(
      listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
      listener: (context, state) =>
          listenWaterFeedback(context, null, state.feedback),
      child: WaterTabScaffold(
        children: [
          const GradientHeaderCard(
            title: 'محطات مياه الشرب',
            subtitle:
                'استورد السجل الجغرافي ثم استمارة TEI، أو عدّل محطة واحدة يدوياً',
            icon: Icons.local_drink_outlined,
          ),
          SizedBox(height: 12.h),
          BlocSelector<DrinkingWaterBloc, DrinkingWaterState,
              Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) => StatsGrid(
              crossAxisCount: 3,
              items: WaterImportStatusStats.drinkingTop(status),
            ),
          ),
          SizedBox(height: 8.h),
          BlocSelector<DrinkingWaterBloc, DrinkingWaterState,
              Map<String, dynamic>?>(
            selector: (s) => s.importStatus,
            builder: (context, status) => StatsGrid(
              crossAxisCount: 3,
              items: WaterImportStatusStats.drinkingBottom(status),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<DrinkingWaterBloc, DrinkingWaterState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => ToggleTabRow(
              isDailyEntry: isDaily,
              onChanged: (v) => context
                  .read<DrinkingWaterBloc>()
                  .add(DrinkingWaterDailyModeToggled(v)),
            ),
          ),
          SizedBox(height: 12.h),
          BlocSelector<DrinkingWaterBloc, DrinkingWaterState, bool>(
            selector: (s) => s.isDaily,
            builder: (context, isDaily) => isDaily
                ? DrinkingWaterDailyForm(
                    orgUnitController: _orgUnitCtrl,
                    notOperatingReasonController: _notOperatingReasonCtrl,
                  )
                : const DrinkingWaterImportPanel(),
          ),
        ],
      ),
    );
  }
}
