import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';
import '../repositories/water_rainfall_repository.dart';

class SaveRainfallDailyUseCase {
  final WaterRainfallRepository _repository;

  SaveRainfallDailyUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required DateTime observationDate,
    required String basinSlug,
    required String stationName,
    required String governorate,
    required double? precipitationMm,
    required String notes,
    int? stationId,
  }) {
    return _repository.saveRainfallDaily(
      observationDate: observationDate,
      basinSlug: basinSlug,
      stationName: stationName,
      governorate: governorate,
      precipitationMm: precipitationMm,
      notes: notes,
      stationId: stationId,
    );
  }
}

class ImportRainfallUseCase {
  final WaterRainfallRepository _repository;

  ImportRainfallUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required List<MultipartFile> files,
    required bool clear,
  }) {
    return _repository.importRainfall(files: files, clear: clear);
  }
}

class ClearRainfallUseCase {
  final WaterRainfallRepository _repository;

  ClearRainfallUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call() {
    return _repository.clearRainfall();
  }
}
