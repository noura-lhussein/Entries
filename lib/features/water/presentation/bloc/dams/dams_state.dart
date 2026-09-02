import 'package:equatable/equatable.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';
import '../water_feedback.dart';

class DamsState extends Equatable {
  const DamsState({
    this.isDaily = true,
    required this.date,
    this.selectedDam,
    this.importStatus,
    this.isBusy = false,
    this.feedback,
    this.formResetToken = 0,
  });

  factory DamsState.initial() => DamsState(date: DateTime.now());

  final bool isDaily;
  final DateTime date;
  final WaterLookupItemEntity? selectedDam;
  final Map<String, dynamic>? importStatus;
  final bool isBusy;
  final WaterFeedback? feedback;
  final int formResetToken;

  DamsState copyWith({
    bool? isDaily,
    DateTime? date,
    WaterLookupItemEntity? selectedDam,
    Map<String, dynamic>? importStatus,
    bool? isBusy,
    WaterFeedback? feedback,
    int? formResetToken,
  }) {
    return DamsState(
      isDaily: isDaily ?? this.isDaily,
      date: date ?? this.date,
      selectedDam: selectedDam ?? this.selectedDam,
      importStatus: importStatus ?? this.importStatus,
      isBusy: isBusy ?? this.isBusy,
      feedback: feedback ?? this.feedback,
      formResetToken: formResetToken ?? this.formResetToken,
    );
  }

  @override
  List<Object?> get props => [
        isDaily,
        date,
        selectedDam,
        importStatus,
        isBusy,
        feedback,
        formResetToken,
      ];
}
