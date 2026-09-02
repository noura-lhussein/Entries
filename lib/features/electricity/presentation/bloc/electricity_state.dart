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
  final bool loadingReport;
  final Map<String, dynamic>? reportDetail;
  final int reportApplyToken;

  const ElectricityState({
    this.isDailyEntry = true,
    required this.reportDate,
    this.peakTime,
    this.maintenanceRows = const [],
    this.generationIncidentRows = const [],
    this.lineIncidentRows = const [],
    this.publishAfterSave = true,
    this.saveStatus = SaveStatus.idle,
    this.loadingReport = false,
    this.reportDetail,
    this.reportApplyToken = 0,
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
    bool clearPeakTime = false,
    List<DynamicRow>? maintenanceRows,
    List<DynamicRow>? generationIncidentRows,
    List<DynamicRow>? lineIncidentRows,
    bool? publishAfterSave,
    SaveStatus? saveStatus,
    bool? loadingReport,
    Map<String, dynamic>? reportDetail,
    bool clearReportDetail = false,
    int? reportApplyToken,
  }) {
    return ElectricityState(
      isDailyEntry: isDailyEntry ?? this.isDailyEntry,
      reportDate: reportDate ?? this.reportDate,
      peakTime: clearPeakTime ? peakTime : (peakTime ?? this.peakTime),
      maintenanceRows: maintenanceRows ?? this.maintenanceRows,
      generationIncidentRows:
          generationIncidentRows ?? this.generationIncidentRows,
      lineIncidentRows: lineIncidentRows ?? this.lineIncidentRows,
      publishAfterSave: publishAfterSave ?? this.publishAfterSave,
      saveStatus: saveStatus ?? this.saveStatus,
      loadingReport: loadingReport ?? this.loadingReport,
      reportDetail:
          clearReportDetail ? reportDetail : (reportDetail ?? this.reportDetail),
      reportApplyToken: reportApplyToken ?? this.reportApplyToken,
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
        loadingReport,
        reportDetail,
        reportApplyToken,
      ];
}
