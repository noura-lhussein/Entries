import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';

abstract class SpcReportEvent extends Equatable {
  const SpcReportEvent();
  @override
  List<Object?> get props => [];
}

class SpcReportStarted extends SpcReportEvent {
  const SpcReportStarted();
}

class SpcReportDateChanged extends SpcReportEvent {
  const SpcReportDateChanged(this.date);
  final DateTime date;
  @override
  List<Object?> get props => [date];
}

class SpcReportPublishToggled extends SpcReportEvent {
  const SpcReportPublishToggled(this.value);
  final bool value;
  @override
  List<Object?> get props => [value];
}

class SpcReportLoadRequested extends SpcReportEvent {
  const SpcReportLoadRequested();
}

class SpcReportSaveRequested extends SpcReportEvent {
  const SpcReportSaveRequested({
    required this.metricTexts,
    required this.notesAr,
  });
  final Map<String, String> metricTexts;
  final String notesAr;
  @override
  List<Object?> get props => [metricTexts, notesAr];
}

class SpcReportDownloadTemplateRequested extends SpcReportEvent {
  const SpcReportDownloadTemplateRequested();
}

class SpcReportImportRequested extends SpcReportEvent {
  const SpcReportImportRequested(this.file);
  final MultipartFile file;
  @override
  List<Object?> get props => [file];
}
