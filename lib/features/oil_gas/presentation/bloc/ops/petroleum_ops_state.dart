import 'package:equatable/equatable.dart';

import '../../../domain/entities/oil_field_entity.dart';
import '../petroleum_feedback.dart';

class PetroleumOpsState extends Equatable {
  const PetroleumOpsState({
    required this.date,
    this.publish = true,
    this.masterLoading = true,
    this.masterError,
    this.fields = const [],
    this.refineries = const [],
    this.depots = const [],
    this.powerFacilities = const {},
    this.saving = false,
    this.feedback,
    this.formResetToken = 0,
  });

  factory PetroleumOpsState.initial() =>
      PetroleumOpsState(date: DateTime.now());

  final DateTime date;
  final bool publish;
  final bool masterLoading;
  final String? masterError;
  final List<OilField> fields;
  final List<String> refineries;
  final List<String> depots;
  final Map<String, String> powerFacilities;
  final bool saving;
  final PetroleumFeedback? feedback;
  final int formResetToken;

  PetroleumOpsState copyWith({
    DateTime? date,
    bool? publish,
    bool? masterLoading,
    String? masterError,
    bool clearMasterError = false,
    List<OilField>? fields,
    List<String>? refineries,
    List<String>? depots,
    Map<String, String>? powerFacilities,
    bool? saving,
    PetroleumFeedback? feedback,
    int? formResetToken,
  }) {
    return PetroleumOpsState(
      date: date ?? this.date,
      publish: publish ?? this.publish,
      masterLoading: masterLoading ?? this.masterLoading,
      masterError:
          clearMasterError ? masterError : (masterError ?? this.masterError),
      fields: fields ?? this.fields,
      refineries: refineries ?? this.refineries,
      depots: depots ?? this.depots,
      powerFacilities: powerFacilities ?? this.powerFacilities,
      saving: saving ?? this.saving,
      feedback: feedback ?? this.feedback,
      formResetToken: formResetToken ?? this.formResetToken,
    );
  }

  @override
  List<Object?> get props => [
        date,
        publish,
        masterLoading,
        masterError,
        fields,
        refineries,
        depots,
        powerFacilities,
        saving,
        feedback,
        formResetToken,
      ];
}
