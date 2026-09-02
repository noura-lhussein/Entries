import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';

abstract class DrinkingWaterEvent extends Equatable {
  const DrinkingWaterEvent();

  @override
  List<Object?> get props => [];
}

class DrinkingWaterStarted extends DrinkingWaterEvent {
  const DrinkingWaterStarted();
}

class DrinkingWaterDailyModeToggled extends DrinkingWaterEvent {
  const DrinkingWaterDailyModeToggled(this.isDaily);
  final bool isDaily;

  @override
  List<Object?> get props => [isDaily];
}

class DrinkingWaterImportSurveyToggled extends DrinkingWaterEvent {
  const DrinkingWaterImportSurveyToggled(this.importSurvey);
  final bool importSurvey;

  @override
  List<Object?> get props => [importSurvey];
}

class DrinkingWaterDateChanged extends DrinkingWaterEvent {
  const DrinkingWaterDateChanged(this.date);
  final DateTime date;

  @override
  List<Object?> get props => [date];
}

class DrinkingWaterStationSelected extends DrinkingWaterEvent {
  const DrinkingWaterStationSelected(this.station);
  final WaterLookupItemEntity station;

  @override
  List<Object?> get props => [station];
}

class DrinkingWaterEnsureSelection extends DrinkingWaterEvent {
  const DrinkingWaterEnsureSelection(this.stations);
  final List<WaterLookupItemEntity> stations;

  @override
  List<Object?> get props => [stations];
}

class DrinkingWaterFieldChanged extends DrinkingWaterEvent {
  const DrinkingWaterFieldChanged(this.key, this.value);
  final String key;
  final String value;

  @override
  List<Object?> get props => [key, value];
}

class DrinkingWaterSaveRequested extends DrinkingWaterEvent {
  const DrinkingWaterSaveRequested({
    required this.orgUnit,
    required this.notOperatingReason,
  });
  final String orgUnit;
  final String notOperatingReason;

  @override
  List<Object?> get props => [orgUnit, notOperatingReason];
}

class DrinkingWaterImportRequested extends DrinkingWaterEvent {
  const DrinkingWaterImportRequested(this.files);
  final List<MultipartFile> files;

  @override
  List<Object?> get props => [files];
}
