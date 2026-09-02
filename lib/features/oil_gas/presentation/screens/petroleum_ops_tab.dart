import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../bloc/ops/petroleum_ops_bloc.dart';
import '../bloc/ops/petroleum_ops_event.dart';
import '../bloc/ops/petroleum_ops_state.dart';
import '../utils/petroleum_snack.dart';
import '../widgets/oil_fields_table.dart';
import '../widgets/petroleum_dynamic_sections.dart';
import '../widgets/refineries_table.dart';

class PetroleumOpsTab extends StatelessWidget {
  const PetroleumOpsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) =>
          getIt<PetroleumOpsBloc>()..add(const PetroleumOpsStarted()),
      child: const _PetroleumOpsView(),
    );
  }
}

class _PetroleumOpsView extends StatefulWidget {
  const _PetroleumOpsView();

  @override
  State<_PetroleumOpsView> createState() => _PetroleumOpsViewState();
}

class _PetroleumOpsViewState extends State<_PetroleumOpsView> {
  final _fuelKey = GlobalKey<FuelStockSectionState>();
  final _exportsKey = GlobalKey<ExportsSectionState>();
  final _lossKey = GlobalKey<ProductionLossSectionState>();
  final _supplyKey = GlobalKey<GasSupplySectionState>();
  final _reqKey = GlobalKey<GasSupplySectionState>();
  Map<String, TextEditingController> _oilC = {};
  Map<String, TextEditingController> _gasC = {};
  Map<String, TextEditingController> _refC = {};

  void _rebuildControllers(PetroleumOpsState state) {
    for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
      c.dispose();
    }
    _oilC = {for (final f in state.fields) f.code: TextEditingController()};
    _gasC = {for (final f in state.fields) f.code: TextEditingController()};
    _refC = {
      for (final r in state.refineries)
        for (final k in ['benzin', 'diesel', 'fuel', 'lpg'])
          '${r}_$k': TextEditingController(),
    };
  }

  @override
  void dispose() {
    for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
      c.dispose();
    }
    super.dispose();
  }

  void _save() {
    context.read<PetroleumOpsBloc>().add(
          PetroleumOpsSaveRequested(
            oilTexts: {
              for (final e in _oilC.entries) e.key: e.value.text,
            },
            gasTexts: {
              for (final e in _gasC.entries) e.key: e.value.text,
            },
            refineryTexts: {
              for (final e in _refC.entries) e.key: e.value.text,
            },
            inventory: _fuelKey.currentState?.collect() ?? [],
            exports: _exportsKey.currentState?.collect() ?? [],
            losses: _lossKey.currentState?.collect() ?? [],
            supply: _supplyKey.currentState?.collect() ?? [],
            requirement: _reqKey.currentState?.collect() ?? [],
          ),
        );
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocListener(
      listeners: [
        BlocListener<PetroleumOpsBloc, PetroleumOpsState>(
          listenWhen: (p, c) =>
              p.fields != c.fields || p.refineries != c.refineries,
          listener: (context, state) {
            setState(() => _rebuildControllers(state));
          },
        ),
        BlocListener<PetroleumOpsBloc, PetroleumOpsState>(
          listenWhen: (p, c) => p.formResetToken != c.formResetToken,
          listener: (_, __) {
            for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
              c.clear();
            }
          },
        ),
        BlocListener<PetroleumOpsBloc, PetroleumOpsState>(
          listenWhen: (p, c) => p.feedback?.id != c.feedback?.id,
          listener: (context, state) =>
              listenPetroleumFeedback(context, state.feedback),
        ),
      ],
      child: SingleChildScrollView(
        padding: EdgeInsets.all(14.r),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const GradientHeaderCard(
              title: 'إدخال البيانات التشغيلية',
              subtitle: 'البيانات الفعلية اليومية للحقول والمصافي',
              icon: Icons.analytics_outlined,
            ),
            SizedBox(height: 12.h),
            BlocBuilder<PetroleumOpsBloc, PetroleumOpsState>(
              buildWhen: (p, c) =>
                  p.masterLoading != c.masterLoading ||
                  p.masterError != c.masterError,
              builder: (context, state) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (state.masterLoading)
                      const LinearProgressIndicator(minHeight: 2),
                    if (state.masterError != null) ...[
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
                                  state.masterError!,
                                  style: TextStyle(
                                    fontFamily: 'Cairo',
                                    fontSize: 12.sp,
                                    color: AppColors.red2,
                                  ),
                                ),
                              ),
                              TextButton(
                                onPressed: () => context
                                    .read<PetroleumOpsBloc>()
                                    .add(const PetroleumOpsStarted()),
                                child: const Text('إعادة'),
                              ),
                            ],
                          ),
                        ),
                      ),
                      SizedBox(height: 12.h),
                    ],
                  ],
                );
              },
            ),
            BlocSelector<PetroleumOpsBloc, PetroleumOpsState, DateTime>(
              selector: (s) => s.date,
              builder: (context, date) => FormCard(
                child: DatePickerField(
                  label: 'تاريخ الإنتاج',
                  initialDate: date,
                  onDateChanged: (d) => context
                      .read<PetroleumOpsBloc>()
                      .add(PetroleumOpsDateChanged(d)),
                ),
              ),
            ),
            SizedBox(height: 12.h),
            BlocBuilder<PetroleumOpsBloc, PetroleumOpsState>(
              buildWhen: (p, c) =>
                  p.fields != c.fields ||
                  p.refineries != c.refineries ||
                  p.depots != c.depots ||
                  p.powerFacilities != c.powerFacilities ||
                  p.publish != c.publish ||
                  p.saving != c.saving,
              builder: (context, state) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (state.fields.isNotEmpty)
                      OilFieldsTable(
                        oilCtrls: _oilC,
                        gasCtrls: _gasC,
                        fields: state.fields,
                      ),
                    if (state.fields.isNotEmpty) SizedBox(height: 12.h),
                    if (state.refineries.isNotEmpty)
                      RefineriesTable(
                        controllers: _refC,
                        refineries: state.refineries,
                      ),
                    if (state.refineries.isNotEmpty) SizedBox(height: 12.h),
                    FuelStockSection(key: _fuelKey, depots: state.depots),
                    SizedBox(height: 12.h),
                    ExportsSection(key: _exportsKey),
                    SizedBox(height: 12.h),
                    if (state.fields.isNotEmpty)
                      ProductionLossSection(
                        key: _lossKey,
                        fields: state.fields,
                      ),
                    if (state.fields.isNotEmpty) SizedBox(height: 12.h),
                    GasSupplySection(
                      key: _supplyKey,
                      title: 'إمداد الغاز للكهرباء',
                      hint: 'أضف صفاً لكل منشأة',
                      valueLabel: 'المورد',
                      valueUnit: 'MMscf',
                      facilities: state.powerFacilities,
                    ),
                    SizedBox(height: 12.h),
                    GasSupplySection(
                      key: _reqKey,
                      title: 'متطلبات غاز الكهرباء',
                      hint: 'أضف صفاً لكل منشأة',
                      valueLabel: 'المطلوب',
                      valueUnit: 'MMscf',
                      isRequirement: true,
                      facilities: state.powerFacilities,
                    ),
                    SizedBox(height: 12.h),
                    FormCard(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          InkWell(
                            onTap: () => context.read<PetroleumOpsBloc>().add(
                                  PetroleumOpsPublishToggled(!state.publish),
                                ),
                            borderRadius: BorderRadius.circular(6.r),
                            child: Row(children: [
                              Checkbox(
                                value: state.publish,
                                activeColor: AppColors.forest1,
                                onChanged: (v) =>
                                    context.read<PetroleumOpsBloc>().add(
                                          PetroleumOpsPublishToggled(
                                            v ?? true,
                                          ),
                                        ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(4.r),
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  'نشر التقرير وتحديث لوحة الوزير بعد الحفظ',
                                  style: TextStyle(
                                    fontFamily: 'Cairo',
                                    fontSize: 12.sp,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ),
                            ]),
                          ),
                          SizedBox(height: 12.h),
                          SaveButton(
                            isLoading: state.saving,
                            label: 'حفظ التقرير اليومي',
                            onPressed: _save,
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 16.h),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
