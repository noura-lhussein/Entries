import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';
import '../repositories/water_dams_repository.dart';

class SaveDamDailyUseCase {
  final WaterDamsRepository _repository;

  SaveDamDailyUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required DateTime readingDate,
    required int? damId,
    required double? storageMcm,
    required String notes,
  }) {
    return _repository.saveDamDaily(
      readingDate: readingDate,
      damId: damId,
      storageMcm: storageMcm,
      notes: notes,
    );
  }
}

class ImportDamsUseCase {
  final WaterDamsRepository _repository;

  ImportDamsUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call({
    required List<MultipartFile> files,
    required bool clear,
  }) {
    return _repository.importDams(files: files, clear: clear);
  }
}

class ClearDamStorageUseCase {
  final WaterDamsRepository _repository;

  ClearDamStorageUseCase(this._repository);

  Future<ApiResult<WaterImportResultEntity>> call() {
    return _repository.clearDamStorage();
  }
}
