import '../../../../core/network/api_result.dart';
import '../repositories/geology_report_repository.dart';

class GetGeologyDailyReportUseCase {
  final GeologyReportRepository _repository;
  GetGeologyDailyReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(String reportDate) {
    return _repository.getDailyReport(reportDate);
  }
}

class SaveGeologyDailyReportUseCase {
  final GeologyReportRepository _repository;
  SaveGeologyDailyReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(Map<String, dynamic> body) {
    return _repository.saveDailyReport(body);
  }
}
