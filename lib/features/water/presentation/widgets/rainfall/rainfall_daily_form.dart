import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import '../../../domain/entities/water_lookup_item_entity.dart';
import '../../bloc/rainfall/rainfall_bloc.dart';
import '../../bloc/rainfall/rainfall_event.dart';
import '../../bloc/rainfall/rainfall_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_state.dart';
import '../shared/water_readonly_field.dart';

class RainfallDailyForm extends StatelessWidget {
  const RainfallDailyForm({
    super.key,
    required this.precipitationController,
    required this.notesController,
  });

  final TextEditingController precipitationController;
  final TextEditingController notesController;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        BlocBuilder<RainfallBloc, RainfallState>(
          buildWhen: (p, c) =>
              p.date != c.date ||
              p.selectedStation != c.selectedStation ||
              p.selectedBasin != c.selectedBasin ||
              p.selectedGov != c.selectedGov,
          builder: (context, state) {
            return FormCard(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DatePickerField(
                    label: 'التاريخ',
                    initialDate: state.date,
                    onDateChanged: (d) => context
                        .read<RainfallBloc>()
                        .add(RainfallDateChanged(d)),
                  ),
                  SizedBox(height: 12.h),
                  BlocBuilder<WaterLookupsBloc, WaterLookupsState>(
                    builder: (context, lookupsState) {
                      if (lookupsState is WaterLookupsLoading) {
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            const FieldShimmer(label: 'الحوض'),
                            SizedBox(height: 12.h),
                            const FieldShimmer(label: 'المحطة'),
                            SizedBox(height: 12.h),
                            const FieldShimmer(label: 'المحافظة'),
                          ],
                        );
                      }
                      if (lookupsState is WaterLookupsError) {
                        return Text(
                          lookupsState.message,
                          style: const TextStyle(color: Colors.red),
                        );
                      }
                      final basins = lookupsState is WaterLookupsLoaded
                          ? lookupsState.lookups.basins
                          : const <WaterLookupItemEntity>[];
                      final stations = lookupsState is WaterLookupsLoaded
                          ? lookupsState.lookups.stations
                          : const <WaterLookupItemEntity>[];
                      final governorates = lookupsState is WaterLookupsLoaded
                          ? lookupsState.lookups.governorates
                          : const <WaterLookupItemEntity>[];
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AppDropdownField(
                            label: 'المحطة',
                            value: state.selectedStation?.name ?? '',
                            items: stations.map((e) => e.name).toList(),
                            onChanged: (v) {
                              if (v == null) return;
                              context.read<RainfallBloc>().add(
                                    RainfallStationSelected(
                                      station: stations
                                          .firstWhere((e) => e.name == v),
                                      basins: basins,
                                      governorates: governorates,
                                    ),
                                  );
                            },
                          ),
                          SizedBox(height: 12.h),
                          WaterReadonlyField(
                            label: 'الحوض',
                            value: state.selectedBasin?.name ?? '—',
                          ),
                          SizedBox(height: 12.h),
                          WaterReadonlyField(
                            label: 'المحافظة',
                            value: state.selectedGov?.name ??
                                state.selectedStation?.governorate ??
                                '—',
                          ),
                        ],
                      );
                    },
                  ),
                  SizedBox(height: 12.h),
                  AppTextField(
                    label: 'الهطول (ملم)',
                    controller: precipitationController,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    suffixText: 'ملم',
                  ),
                  SizedBox(height: 12.h),
                  AppTextField(
                    label: 'ملاحظات',
                    controller: notesController,
                    maxLines: 2,
                  ),
                  SizedBox(height: 8.h),
                  Text(
                    'يُملأ الحوض والمحافظة تلقائياً عند اختيار المحطة.',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 11.sp,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            );
          },
        ),
        SizedBox(height: 12.h),
        const DuplicateNote(),
        SizedBox(height: 12.h),
        BlocSelector<RainfallBloc, RainfallState, bool>(
          selector: (s) => s.isBusy,
          builder: (context, isBusy) => SaveButton(
            isLoading: isBusy,
            onPressed: () => context.read<RainfallBloc>().add(
                  RainfallSaveRequested(
                    precipitationText: precipitationController.text,
                    notes: notesController.text.trim(),
                  ),
                ),
          ),
        ),
      ],
    );
  }
}
