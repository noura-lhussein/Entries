import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../../domain/entities/water_lookup_item_entity.dart';
import '../../bloc/drinking_water/drinking_water_bloc.dart';
import '../../bloc/drinking_water/drinking_water_event.dart';
import '../../bloc/drinking_water/drinking_water_state.dart';
import '../../bloc/water_lookups_bloc.dart';
import '../../bloc/water_lookups_state.dart';
import 'drinking_energy_supply_section.dart';
import 'drinking_operation_status_section.dart';
import 'drinking_other_info_section.dart';
import 'drinking_station_definition_section.dart';
import 'drinking_station_type_section.dart';

class DrinkingWaterDailyForm extends StatelessWidget {
  const DrinkingWaterDailyForm({
    super.key,
    required this.orgUnitController,
    required this.notOperatingReasonController,
  });

  final TextEditingController orgUnitController;
  final TextEditingController notOperatingReasonController;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DrinkingWaterBloc, DrinkingWaterState>(
      buildWhen: (p, c) =>
          p.selectedStation != c.selectedStation ||
          p.registrationDate != c.registrationDate ||
          p.values != c.values ||
          p.isBusy != c.isBusy,
      builder: (context, state) {
        void onFieldChanged(String key, String value) {
          context
              .read<DrinkingWaterBloc>()
              .add(DrinkingWaterFieldChanged(key, value));
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            BlocConsumer<WaterLookupsBloc, WaterLookupsState>(
              listenWhen: (p, c) => c is WaterLookupsLoaded,
              listener: (context, lookupsState) {
                if (lookupsState is WaterLookupsLoaded) {
                  context.read<DrinkingWaterBloc>().add(
                        DrinkingWaterEnsureSelection(
                          lookupsState.lookups.drinkingWaterStations,
                        ),
                      );
                }
              },
              builder: (context, lookupsState) {
                if (lookupsState is WaterLookupsLoading) {
                  return const FieldShimmer(label: 'اختر محطة مياه الشرب');
                }
                if (lookupsState is WaterLookupsError) {
                  return Text(
                    lookupsState.message,
                    style: const TextStyle(color: Colors.red),
                  );
                }
                final stations = lookupsState is WaterLookupsLoaded
                    ? lookupsState.lookups.drinkingWaterStations
                    : const <WaterLookupItemEntity>[];
                return FormCard(
                  child: AppDropdownField(
                    label: 'اختر محطة مياه الشرب',
                    value: state.selectedStation?.name ?? '',
                    items: stations.map((e) => e.name).toList(),
                    onChanged: (v) {
                      if (v == null) return;
                      context.read<DrinkingWaterBloc>().add(
                            DrinkingWaterStationSelected(
                              stations.firstWhere((e) => e.name == v),
                            ),
                          );
                    },
                  ),
                );
              },
            ),
            SizedBox(height: 12.h),
            DrinkingStationDefinitionSection(
              stationName: state.selectedStation?.name ?? '',
              registrationDate: state.registrationDate,
              onDateChanged: (d) => context
                  .read<DrinkingWaterBloc>()
                  .add(DrinkingWaterDateChanged(d)),
              orgUnitController: orgUnitController,
            ),
            SizedBox(height: 12.h),
            DrinkingOperationStatusSection(
              values: state.values,
              onChanged: onFieldChanged,
              notOperatingReasonController: notOperatingReasonController,
            ),
            SizedBox(height: 12.h),
            DrinkingEnergySupplySection(
              values: state.values,
              onChanged: onFieldChanged,
            ),
            SizedBox(height: 12.h),
            DrinkingStationTypeSection(
              values: state.values,
              onChanged: onFieldChanged,
            ),
            SizedBox(height: 12.h),
            DrinkingOtherInfoSection(
              values: state.values,
              onChanged: onFieldChanged,
            ),
            SizedBox(height: 12.h),
            const DuplicateNote(),
            SizedBox(height: 12.h),
            SaveButton(
              label: 'حفظ بيانات المحطة',
              isLoading: state.isBusy,
              onPressed: () => context.read<DrinkingWaterBloc>().add(
                    DrinkingWaterSaveRequested(
                      orgUnit: orgUnitController.text,
                      notOperatingReason: notOperatingReasonController.text,
                    ),
                  ),
            ),
          ],
        );
      },
    );
  }
}
