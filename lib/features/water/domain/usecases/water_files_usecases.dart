import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../repositories/water_files_repository.dart';

class GetWaterImportStatusUseCase {
  final WaterFilesRepository _repository;

  GetWaterImportStatusUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call() {
    return _repository.getImportStatus();
  }
}

class DownloadWaterTemplateUseCase {
  final WaterFilesRepository _repository;

  DownloadWaterTemplateUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call(String kind) {
    return _repository.downloadTemplate(kind);
  }
}

class ExportDrinkingWaterSurveyUseCase {
  final WaterFilesRepository _repository;

  ExportDrinkingWaterSurveyUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call() {
    return _repository.exportDrinkingWaterSurvey();
  }
}
