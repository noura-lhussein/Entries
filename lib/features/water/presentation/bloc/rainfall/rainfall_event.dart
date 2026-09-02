import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';

abstract class RainfallEvent extends Equatable {
  const RainfallEvent();

  @override
  List<Object?> get props => [];
}

class RainfallStarted extends RainfallEvent {
  const RainfallStarted();
}

class RainfallDailyModeToggled extends RainfallEvent {
  const RainfallDailyModeToggled(this.isDaily);
  final bool isDaily;

  @override
  List<Object?> get props => [isDaily];
}

class RainfallDateChanged extends RainfallEvent {
  const RainfallDateChanged(this.date);
  final DateTime date;

  @override
  List<Object?> get props => [date];
}

class RainfallStationSelected extends RainfallEvent {
  const RainfallStationSelected({
    required this.station,
    required this.basins,
    required this.governorates,
  });
  final WaterLookupItemEntity station;
  final List<WaterLookupItemEntity> basins;
  final List<WaterLookupItemEntity> governorates;

  @override
  List<Object?> get props => [station, basins, governorates];
}

class RainfallSaveRequested extends RainfallEvent {
  const RainfallSaveRequested({
    required this.precipitationText,
    required this.notes,
  });
  final String precipitationText;
  final String notes;

  @override
  List<Object?> get props => [precipitationText, notes];
}

class RainfallImportRequested extends RainfallEvent {
  const RainfallImportRequested(this.files);
  final List<MultipartFile> files;

  @override
  List<Object?> get props => [files];
}

class RainfallClearRequested extends RainfallEvent {
  const RainfallClearRequested();
}
