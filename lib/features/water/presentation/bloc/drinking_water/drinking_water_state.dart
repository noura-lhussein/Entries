import 'package:equatable/equatable.dart';

import '../../../domain/entities/water_lookup_item_entity.dart';
import '../water_feedback.dart';

class DrinkingWaterFormDefaults {
  DrinkingWaterFormDefaults._();

  static final DateTime registrationDate = DateTime(2026, 2, 14);

  static const Map<String, String> values = {
    'isWorking': 'لا',
    'buildingStatus': '3 - لا حاجة للتدخل',
    'previousRehab': 'لا',
    'safetyProcedures': 'لا',
    'rehabType': 'غير محدد',
    'waterHammerProtection': 'لا',
    'waterHammerEfficiency': 'غير محدد',
    'publicGrid': 'لا',
    'gridConnectionWorks': 'لا',
    'electricalConnectionEfficiency': '2 - يحتاج صيانة دورية',
    'transformerEfficiency': '3 - لا حاجة للتدخل',
    'panelEfficiency': '3 - لا حاجة للتدخل',
    'gridEnergyProductivity': '0%',
    'solarAvailable': 'لا',
    'solarProductivity': 'غير محدد',
    'solarSystemEfficiency': 'غير محدد',
    'generatorAvailable': 'نعم',
    'needsSolarInstallation': 'نعم',
    'solarSpaceAvailable': 'لا',
    'alternativeEnergy': 'لا',
    'pumpingStation': 'لا',
    'wellStation': 'لا',
    'treatmentStation': 'لا',
    'waterAnalysis': 'نعم',
    'waterTanks': 'لا',
    'labEquipment': 'غير محدد',
  };
}

class DrinkingWaterState extends Equatable {
  const DrinkingWaterState({
    this.isDaily = true,
    this.importSurvey = false,
    required this.registrationDate,
    this.selectedStation,
    required this.values,
    this.importStatus,
    this.isBusy = false,
    this.feedback,
  });

  factory DrinkingWaterState.initial() => DrinkingWaterState(
        registrationDate: DrinkingWaterFormDefaults.registrationDate,
        values: Map<String, String>.from(DrinkingWaterFormDefaults.values),
      );

  final bool isDaily;
  final bool importSurvey;
  final DateTime registrationDate;
  final WaterLookupItemEntity? selectedStation;
  final Map<String, String> values;
  final Map<String, dynamic>? importStatus;
  final bool isBusy;
  final WaterFeedback? feedback;

  DrinkingWaterState copyWith({
    bool? isDaily,
    bool? importSurvey,
    DateTime? registrationDate,
    WaterLookupItemEntity? selectedStation,
    Map<String, String>? values,
    Map<String, dynamic>? importStatus,
    bool? isBusy,
    WaterFeedback? feedback,
  }) {
    return DrinkingWaterState(
      isDaily: isDaily ?? this.isDaily,
      importSurvey: importSurvey ?? this.importSurvey,
      registrationDate: registrationDate ?? this.registrationDate,
      selectedStation: selectedStation ?? this.selectedStation,
      values: values ?? this.values,
      importStatus: importStatus ?? this.importStatus,
      isBusy: isBusy ?? this.isBusy,
      feedback: feedback ?? this.feedback,
    );
  }

  @override
  List<Object?> get props => [
        isDaily,
        importSurvey,
        registrationDate,
        selectedStation,
        values,
        importStatus,
        isBusy,
        feedback,
      ];
}
