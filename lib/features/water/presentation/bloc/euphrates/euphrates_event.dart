import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';

abstract class EuphratesEvent extends Equatable {
  const EuphratesEvent();

  @override
  List<Object?> get props => [];
}

class EuphratesStarted extends EuphratesEvent {
  const EuphratesStarted();
}

class EuphratesDailyModeToggled extends EuphratesEvent {
  const EuphratesDailyModeToggled(this.isDaily);
  final bool isDaily;

  @override
  List<Object?> get props => [isDaily];
}

class EuphratesDateChanged extends EuphratesEvent {
  const EuphratesDateChanged(this.date);
  final DateTime date;

  @override
  List<Object?> get props => [date];
}

class EuphratesSaveRequested extends EuphratesEvent {
  const EuphratesSaveRequested({
    required this.reportLabel,
    required this.tishreenInflow,
    required this.tishreenLevel,
    required this.tishreenStorage,
    required this.tishreenGeneration,
    required this.furatLevel,
    required this.furatStorage,
    required this.furatGeneration,
    required this.kadiranGeneration,
    required this.totalGeneration,
  });

  final String reportLabel;
  final String tishreenInflow;
  final String tishreenLevel;
  final String tishreenStorage;
  final String tishreenGeneration;
  final String furatLevel;
  final String furatStorage;
  final String furatGeneration;
  final String kadiranGeneration;
  final String totalGeneration;

  @override
  List<Object?> get props => [
        reportLabel,
        tishreenInflow,
        tishreenLevel,
        tishreenStorage,
        tishreenGeneration,
        furatLevel,
        furatStorage,
        furatGeneration,
        kadiranGeneration,
        totalGeneration,
      ];
}

class EuphratesImportRequested extends EuphratesEvent {
  const EuphratesImportRequested(this.files);
  final List<MultipartFile> files;

  @override
  List<Object?> get props => [files];
}

class EuphratesClearRequested extends EuphratesEvent {
  const EuphratesClearRequested();
}
