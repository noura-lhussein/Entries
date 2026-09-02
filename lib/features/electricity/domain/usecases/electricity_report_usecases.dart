import '../../../../core/network/api_result.dart';
import '../repositories/electricity_report_repository.dart';

class UpsertElectricityReportUseCase {
  final ElectricityReportRepository _repository;

  UpsertElectricityReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(Map<String, dynamic> payload) {
    return _repository.upsertDailyReport(payload);
  }
}

class GetElectricityReportDetailUseCase {
  final ElectricityReportRepository _repository;

  GetElectricityReportDetailUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(String date) {
    return _repository.getReportDetail(date);
  }
}

class GetElectricityReportDatesUseCase {
  final ElectricityReportRepository _repository;

  GetElectricityReportDatesUseCase(this._repository);

  Future<ApiResult<List<dynamic>>> call() {
    return _repository.getReportDates();
  }
}

class ListElectricityReportsUseCase {
  final ElectricityReportRepository _repository;

  ListElectricityReportsUseCase(this._repository);

  Future<ApiResult<List<dynamic>>> call() {
    return _repository.listReports();
  }
}
