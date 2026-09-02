import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../repositories/electricity_files_repository.dart';

class DownloadElectricityReportTemplateUseCase {
  final ElectricityFilesRepository _repository;

  DownloadElectricityReportTemplateUseCase(this._repository);

  Future<ApiResult<Response<List<int>>>> call({String? date}) {
    return _repository.downloadReportTemplate(date: date);
  }
}

class ImportElectricityDailyReportUseCase {
  final ElectricityFilesRepository _repository;

  ImportElectricityDailyReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(
    MultipartFile file, {
    bool publish = true,
  }) {
    return _repository.importDailyReport(file, publish: publish);
  }
}

class ExportElectricityReportUseCase {
  final ElectricityFilesRepository _repository;

  ExportElectricityReportUseCase(this._repository);

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
