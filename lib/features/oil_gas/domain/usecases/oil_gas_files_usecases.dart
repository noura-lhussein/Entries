import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_files_repository.dart';

class DownloadOilGasExecutiveTemplateUseCase {
  final OilGasFilesRepository _repository;
  DownloadOilGasExecutiveTemplateUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call({String? date}) {
    return _repository.downloadExecutiveTemplate(date: date);
  }
}

class ImportOilGasExecutiveReportUseCase {
  final OilGasFilesRepository _repository;
  ImportOilGasExecutiveReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(
    MultipartFile file, {
    bool publish = true,
  }) {
    return _repository.importExecutiveReport(file, publish: publish);
  }
}

class ExportOilGasReportUseCase {
  final OilGasFilesRepository _repository;
  ExportOilGasReportUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call({
    String? date,
    String? month,
    String period = 'day',
    String format = 'xlsx',
  }) {
    return _repository.exportReport(
      date: date,
      month: month,
      period: period,
      format: format,
    );
  }
}
