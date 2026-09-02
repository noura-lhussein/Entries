import '../../domain/utils/parse_water_number.dart';

class EuphratesDailyPayloadMapper {
  const EuphratesDailyPayloadMapper._();

  static Map<String, dynamic> fromForm({
    required DateTime date,
    required String reportLabel,
    required String tishreenInflow,
    required String tishreenLevel,
    required String tishreenStorage,
    required String tishreenGeneration,
    required String furatLevel,
    required String furatStorage,
    required String furatGeneration,
    required String kadiranGeneration,
    required String totalGeneration,
  }) {
    return {
      'reading_date': waterIsoDate(date),
      'report_label': reportLabel.trim(),
      'inflow_jarabulus': parseWaterNumber(tishreenInflow),
      'tishreen_level_m': parseWaterNumber(tishreenLevel),
      'tishreen_storage_mcm': parseWaterNumber(tishreenStorage),
      'tishreen_outflow': null,
      'tishreen_generation_mwh': parseWaterNumber(tishreenGeneration),
      'furat_level_m': parseWaterNumber(furatLevel),
      'furat_storage_mcm': parseWaterNumber(furatStorage),
      'furat_outflow': null,
      'furat_generation_mwh': parseWaterNumber(furatGeneration),
      'kadiran_outflow': null,
      'kadiran_generation_mwh': parseWaterNumber(kadiranGeneration),
      'al_jalab_discharge': null,
      'total_generation_mwh': parseWaterNumber(totalGeneration),
    };
  }
}
