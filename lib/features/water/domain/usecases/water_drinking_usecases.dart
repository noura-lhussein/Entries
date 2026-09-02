import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';
import '../repositories/water_drinking_repository.dart';

class GetDrinkingWaterStationUseCase {
  final WaterDrinkingRepository _repository;

  GetDrinkingWaterStationUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(int stationId) {
    return _repository.getDrinkingWaterStation(stationId);
  }
}

class SaveDrinkingWaterStationUseCase {
  final WaterDrinkingRepository _repository;

  SaveDrinkingWaterStationUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required Map<String, dynamic> payload,
  }) {
    return _repository.saveDrinkingWaterStation(payload: payload);
  }
}

class ImportDrinkingWaterGeoUseCase {
  final WaterDrinkingRepository _repository;

  ImportDrinkingWaterGeoUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required List<MultipartFile> files,
    required bool clear,
  }) {
    return _repository.importDrinkingWaterGeo(files: files, clear: clear);
  }
}

class ImportDrinkingWaterSurveyUseCase {
  final WaterDrinkingRepository _repository;

  ImportDrinkingWaterSurveyUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required List<MultipartFile> files,
  }) {
    return _repository.importDrinkingWaterSurvey(files: files);
  }
}
