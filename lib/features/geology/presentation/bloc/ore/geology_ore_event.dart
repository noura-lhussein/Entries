import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';

abstract class GeologyOreEvent extends Equatable {
  const GeologyOreEvent();
  @override
  List<Object?> get props => [];
}

class GeologyOreStarted extends GeologyOreEvent {
  const GeologyOreStarted();
}

class GeologyOreDateChanged extends GeologyOreEvent {
  const GeologyOreDateChanged(this.date);
  final DateTime date;
  @override
  List<Object?> get props => [date];
}

class GeologyOrePublishToggled extends GeologyOreEvent {
  const GeologyOrePublishToggled(this.value);
  final bool value;
  @override
  List<Object?> get props => [value];
}

class GeologyOreLoadRequested extends GeologyOreEvent {
  const GeologyOreLoadRequested();
}

class GeologyOreSaveRequested extends GeologyOreEvent {
  const GeologyOreSaveRequested(this.rows);
  final List<Map<String, dynamic>> rows;
  @override
  List<Object?> get props => [rows];
}

class GeologyOreDownloadTemplateRequested extends GeologyOreEvent {
  const GeologyOreDownloadTemplateRequested();
}

class GeologyOreExportRequested extends GeologyOreEvent {
  const GeologyOreExportRequested();
}

class GeologyOreImportRequested extends GeologyOreEvent {
  const GeologyOreImportRequested(this.file);
  final MultipartFile file;
  @override
  List<Object?> get props => [file];
}
