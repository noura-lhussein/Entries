import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';
import '../repositories/water_euphrates_repository.dart';

class GetEuphratesDailyUseCase {
  final WaterEuphratesRepository _repository;

  GetEuphratesDailyUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>?>> call(DateTime date) {
    return _repository.getEuphratesDaily(date);
  }
}

class SaveEuphratesDailyUseCase {
  final WaterEuphratesRepository _repository;

  SaveEuphratesDailyUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required Map<String, dynamic> payload,
  }) {
    return _repository.saveEuphratesDaily(payload: payload);
  }
}

class ImportEuphratesUseCase {
  final WaterEuphratesRepository _repository;

  ImportEuphratesUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required List<MultipartFile> files,
    required bool clear,
  }) {
    return _repository.importEuphrates(files: files, clear: clear);
  }
}

class ClearEuphratesUseCase {
  final WaterEuphratesRepository _repository;

  ClearEuphratesUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call() {
    return _repository.clearEuphrates();
  }
}
