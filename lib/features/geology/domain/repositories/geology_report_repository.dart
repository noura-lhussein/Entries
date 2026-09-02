import '../../../../core/network/api_result.dart';

abstract class GeologyReportRepository {
  Future<ApiResult<Map<String, dynamic>>> getDailyReport(String reportDate);

  Future<ApiResult<Map<String, dynamic>>> saveDailyReport(
    Map<String, dynamic> body,
  );
}
