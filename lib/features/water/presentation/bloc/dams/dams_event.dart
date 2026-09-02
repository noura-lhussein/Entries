import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';

abstract class DamsEvent extends Equatable {
  const DamsEvent();

  @override
  List<Object?> get props => [];
}

class DamsStarted extends DamsEvent {
  const DamsStarted();
}

class DamsDailyModeToggled extends DamsEvent {
  const DamsDailyModeToggled(this.isDaily);
  final bool isDaily;

  @override
  List<Object?> get props => [isDaily];
}

class DamsDateChanged extends DamsEvent {
  const DamsDateChanged(this.date);
  final DateTime date;

  @override
  List<Object?> get props => [date];
}

class DamsDamSelected extends DamsEvent {
  const DamsDamSelected(this.dam);
  final WaterLookupItemEntity dam;

  @override
  List<Object?> get props => [dam];
}

class DamsEnsureSelection extends DamsEvent {
  const DamsEnsureSelection(this.dams);
  final List<WaterLookupItemEntity> dams;

  @override
  List<Object?> get props => [dams];
}

class DamsSaveRequested extends DamsEvent {
  const DamsSaveRequested({
    required this.storageText,
    required this.notes,
  });
  final String storageText;
  final String notes;

  @override
  List<Object?> get props => [storageText, notes];
}

class DamsImportRequested extends DamsEvent {
  const DamsImportRequested(this.files);
  final List<MultipartFile> files;

  @override
  List<Object?> get props => [files];
}

class DamsClearRequested extends DamsEvent {
  const DamsClearRequested();
}

class DamsImportStatusRequested extends DamsEvent {
  const DamsImportStatusRequested();
}
