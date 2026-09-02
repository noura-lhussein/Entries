import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/dams/dams_bloc.dart';
import '../../bloc/dams/dams_event.dart';
import '../../bloc/dams/dams_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_state.dart';
import '../../../domain/entities/water_lookup_item_entity.dart';

class DamsDailyForm extends StatelessWidget {
  const DamsDailyForm({
    super.key,
    required this.storageController,
    required this.notesController,
  });

  final TextEditingController storageController;
  final TextEditingController notesController;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DamsBloc, DamsState>(
      buildWhen: (p, c) =>
          p.date != c.date ||
          p.selectedDam != c.selectedDam ||
          p.isBusy != c.isBusy,
      builder: (context, state) {
        return FormCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DatePickerField(
                label: 'التاريخ',
                initialDate: state.date,
                onDateChanged: (d) =>
                    context.read<DamsBloc>().add(DamsDateChanged(d)),
              ),
              SizedBox(height: 12.h),
              BlocConsumer<WaterLookupsBloc, WaterLookupsState>(
                listenWhen: (p, c) => c is WaterLookupsLoaded,
                listener: (context, lookupsState) {
                  if (lookupsState is WaterLookupsLoaded) {
                    context.read<DamsBloc>().add(
                          DamsEnsureSelection(lookupsState.lookups.dams),
                        );
                  }
                },
                builder: (context, lookupsState) {
                  if (lookupsState is WaterLookupsLoading) {
                    return const FieldShimmer(label: 'السد');
                  }
                  if (lookupsState is WaterLookupsError) {
                    return Text(
                      lookupsState.message,
                      style: const TextStyle(color: Colors.red),
                    );
                  }
                  final dams = lookupsState is WaterLookupsLoaded
                      ? lookupsState.lookups.dams
                      : const <WaterLookupItemEntity>[];
                  return AppDropdownField(
                    label: 'السد',
                    value: state.selectedDam?.name ?? '',
                    items: dams.map((e) => e.name).toList(),
                    onChanged: (v) {
                      context.read<DamsBloc>().add(
                            DamsDamSelected(
                              dams.firstWhere((e) => e.name == v),
                            ),
                          );
                    },
                  );
                },
              ),
              SizedBox(height: 12.h),
              AppTextField(
                label: 'المخزون (مليون م³)',
                controller: storageController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'مليون م³',
              ),
              SizedBox(height: 12.h),
              AppTextField(
                label: 'ملاحظات',
                controller: notesController,
                maxLines: 2,
              ),
              SizedBox(height: 14.h),
              const DuplicateNote(),
              SizedBox(height: 14.h),
              SaveButton(
                isLoading: state.isBusy,
                onPressed: () => context.read<DamsBloc>().add(
                      DamsSaveRequested(
                        storageText: storageController.text,
                        notes: notesController.text.trim(),
                      ),
                    ),
              ),
            ],
          ),
        );
      },
    );
  }
}
