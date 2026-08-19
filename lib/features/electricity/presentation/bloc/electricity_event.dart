import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';

/// The three "add row" tables on the electricity report
enum DynamicSectionType { maintenance, generationIncidents, lineIncidents }

class DynamicRow extends Equatable {
  final String id;
  final List<String> initialValues;
  const DynamicRow(this.id, [this.initialValues = const []]);
  @override
  List<Object?> get props => [id];
}

abstract class ElectricityEvent extends Equatable {
  const ElectricityEvent();
  @override
  List<Object?> get props => [];
}

class ElectricityStarted extends ElectricityEvent {
  const ElectricityStarted();
}

class DailyEntryToggled extends ElectricityEvent {
  final bool isDailyEntry;
  const DailyEntryToggled(this.isDailyEntry);
  @override
  List<Object?> get props => [isDailyEntry];
}

class ReportDateChanged extends ElectricityEvent {
  final DateTime date;
  const ReportDateChanged(this.date);
  @override
  List<Object?> get props => [date];
}

class PeakTimeChanged extends ElectricityEvent {
  final TimeOfDay time;
  const PeakTimeChanged(this.time);
  @override
  List<Object?> get props => [time];
}

class DynamicRowAdded extends ElectricityEvent {
  final DynamicSectionType section;
  const DynamicRowAdded(this.section);
  @override
  List<Object?> get props => [section];
}

class DynamicRowRemoved extends ElectricityEvent {
  final DynamicSectionType section;
  final String rowId;
  const DynamicRowRemoved(this.section, this.rowId);
  @override
  List<Object?> get props => [section, rowId];
}

class DynamicRowsReplaced extends ElectricityEvent {
  final DynamicSectionType section;
  final List<DynamicRow> rows;
  const DynamicRowsReplaced(this.section, this.rows);
  @override
  List<Object?> get props => [section, rows];
}

class PublishAfterSaveToggled extends ElectricityEvent {
  final bool value;
  const PublishAfterSaveToggled(this.value);
  @override
  List<Object?> get props => [value];
}

class ReportSaveRequested extends ElectricityEvent {
  final Map<String, dynamic> payload;
  const ReportSaveRequested(this.payload);
  @override
  List<Object?> get props => [payload];
}
