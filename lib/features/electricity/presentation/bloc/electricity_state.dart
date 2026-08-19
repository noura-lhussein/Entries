import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

import 'electricity_event.dart';

enum SaveStatus { idle, saving, failure, success }

class ElectricityState extends Equatable {
  final bool isDailyEntry;
  final DateTime reportDate;
  final TimeOfDay? peakTime;
  final List<DynamicRow> maintenanceRows;
  final List<DynamicRow> generationIncidentRows;
  final List<DynamicRow> lineIncidentRows;
  final bool publishAfterSave;
  final SaveStatus saveStatus;

  const ElectricityState({
    this.isDailyEntry = true,
    required this.reportDate,
    this.peakTime,
    this.maintenanceRows = const [],
    this.generationIncidentRows = const [],
    this.lineIncidentRows = const [],
    this.publishAfterSave = true,
    this.saveStatus = SaveStatus.idle,
  });

  factory ElectricityState.initial() =>
      ElectricityState(reportDate: DateTime.now());

  List<DynamicRow> rowsFor(DynamicSectionType type) {
    switch (type) {
      case DynamicSectionType.maintenance:
        return maintenanceRows;
      case DynamicSectionType.generationIncidents:
        return generationIncidentRows;
      case DynamicSectionType.lineIncidents:
        return lineIncidentRows;
    }
  }

  ElectricityState copyWith({
    bool? isDailyEntry,
    DateTime? reportDate,
    TimeOfDay? peakTime,
    List<DynamicRow>? maintenanceRows,
    List<DynamicRow>? generationIncidentRows,
    List<DynamicRow>? lineIncidentRows,
    bool? publishAfterSave,
    SaveStatus? saveStatus,
  }) {
    return ElectricityState(
      isDailyEntry: isDailyEntry ?? this.isDailyEntry,
      reportDate: reportDate ?? this.reportDate,
      peakTime: peakTime ?? this.peakTime,
      maintenanceRows: maintenanceRows ?? this.maintenanceRows,
      generationIncidentRows:
          generationIncidentRows ?? this.generationIncidentRows,
      lineIncidentRows: lineIncidentRows ?? this.lineIncidentRows,
      publishAfterSave: publishAfterSave ?? this.publishAfterSave,
      saveStatus: saveStatus ?? this.saveStatus,
    );
  }

  @override
  List<Object?> get props => [
        isDailyEntry,
        reportDate,
        peakTime,
        maintenanceRows,
        generationIncidentRows,
        lineIncidentRows,
        publishAfterSave,
        saveStatus,
      ];
}
