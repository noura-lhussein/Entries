import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_report_repository.dart';

class UpsertOilGasReportUseCase {
  final OilGasReportRepository _repository;
  UpsertOilGasReportUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(Map<String, dynamic> payload) {
    return _repository.upsertDailyReport(payload);
  }
}

class GetOilGasReportDetailUseCase {
  final OilGasReportRepository _repository;
  GetOilGasReportDetailUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(String date) {
    return _repository.getReportDetail(date);
  }
}

class GetOilGasReportDatesUseCase {
  final OilGasReportRepository _repository;
  GetOilGasReportDatesUseCase(this._repository);

  Future<ApiResult<List<dynamic>>> call() {
    return _repository.getReportDates();
  }
}

class ListOilGasReportsUseCase {
  final OilGasReportRepository _repository;
  ListOilGasReportsUseCase(this._repository);

  Future<ApiResult<List<dynamic>>> call() {
    return _repository.listReports();
  }
}
