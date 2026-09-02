import 'package:equatable/equatable.dart';

import '../water_feedback.dart';

class EuphratesState extends Equatable {
  const EuphratesState({
    this.isDaily = true,
    required this.date,
    this.reading,
    this.importStatus,
    this.isBusy = false,
    this.feedback,
  });

  factory EuphratesState.initial() => EuphratesState(date: DateTime.now());

  final bool isDaily;
  final DateTime date;
  final Map<String, dynamic>? reading;
  final Map<String, dynamic>? importStatus;
  final bool isBusy;
  final WaterFeedback? feedback;

  EuphratesState copyWith({
    bool? isDaily,
    DateTime? date,
    Map<String, dynamic>? reading,
    bool clearReading = false,
    Map<String, dynamic>? importStatus,
    bool? isBusy,
    WaterFeedback? feedback,
  }) {
    return EuphratesState(
      isDaily: isDaily ?? this.isDaily,
      date: date ?? this.date,
      reading: clearReading ? reading : (reading ?? this.reading),
      importStatus: importStatus ?? this.importStatus,
      isBusy: isBusy ?? this.isBusy,
      feedback: feedback ?? this.feedback,
    );
  }

  @override
  List<Object?> get props => [
        isDaily,
        date,
        reading,
        importStatus,
        isBusy,
        feedback,
      ];
}
