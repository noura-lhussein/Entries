import '../../../../core/network/api_result.dart';

abstract class OilGasReportRepository {
  Future<ApiResult<Map<String, dynamic>>> upsertDailyReport(
    Map<String, dynamic> payload,
  );

  Future<ApiResult<Map<String, dynamic>>> getReportDetail(String date);

  Future<ApiResult<List<dynamic>>> getReportDates();

  Future<ApiResult<List<dynamic>>> listReports();
}
