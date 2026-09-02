import 'package:equatable/equatable.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';
import '../water_feedback.dart';

class RainfallState extends Equatable {
  const RainfallState({
    this.isDaily = true,
    required this.date,
    this.selectedStation,
    this.selectedBasin,
    this.selectedGov,
    this.importStatus,
    this.isBusy = false,
    this.feedback,
    this.formResetToken = 0,
  });

  factory RainfallState.initial() => RainfallState(date: DateTime.now());

  final bool isDaily;
  final DateTime date;
  final WaterLookupItemEntity? selectedStation;
  final WaterLookupItemEntity? selectedBasin;
  final WaterLookupItemEntity? selectedGov;
  final Map<String, dynamic>? importStatus;
  final bool isBusy;
  final WaterFeedback? feedback;
  final int formResetToken;

  RainfallState copyWith({
    bool? isDaily,
    DateTime? date,
    WaterLookupItemEntity? selectedStation,
    WaterLookupItemEntity? selectedBasin,
    WaterLookupItemEntity? selectedGov,
    bool replaceStationLookups = false,
    Map<String, dynamic>? importStatus,
    bool? isBusy,
    WaterFeedback? feedback,
    int? formResetToken,
  }) {
    return RainfallState(
      isDaily: isDaily ?? this.isDaily,
      date: date ?? this.date,
      selectedStation: replaceStationLookups
          ? selectedStation
          : (selectedStation ?? this.selectedStation),
      selectedBasin: replaceStationLookups
          ? selectedBasin
          : (selectedBasin ?? this.selectedBasin),
      selectedGov:
          replaceStationLookups ? selectedGov : (selectedGov ?? this.selectedGov),
      importStatus: importStatus ?? this.importStatus,
      isBusy: isBusy ?? this.isBusy,
      feedback: feedback ?? this.feedback,
      formResetToken: formResetToken ?? this.formResetToken,
    );
  }

  @override
  List<Object?> get props => [
        isDaily,
        date,
        selectedStation,
        selectedBasin,
        selectedGov,
        importStatus,
        isBusy,
        feedback,
        formResetToken,
      ];
}
