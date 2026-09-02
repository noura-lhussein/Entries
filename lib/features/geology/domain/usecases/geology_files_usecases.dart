import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../repositories/geology_files_repository.dart';

class DownloadGeologyReportUseCase {
  final GeologyFilesRepository _repository;
  DownloadGeologyReportUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call({
    required int planYear,
    String format = 'xlsx',
  }) {
    return _repository.downloadReport(planYear: planYear, format: format);
  }
}

class DownloadGeologyOreTemplateUseCase {
  final GeologyFilesRepository _repository;
  DownloadGeologyOreTemplateUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call({int? planYear}) {
    return _repository.downloadOreTemplate(planYear: planYear);
  }
}

class ExportGeologyOreProductionUseCase {
  final GeologyFilesRepository _repository;
  ExportGeologyOreProductionUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call(int planYear) {
    return _repository.exportOreProduction(planYear);
  }
}

class ImportGeologyOreProductionUseCase {
  final GeologyFilesRepository _repository;
  ImportGeologyOreProductionUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(
    MultipartFile file, {
    bool publish = true,
  }) {
    return _repository.importOreProduction(file, publish: publish);
  }
}
