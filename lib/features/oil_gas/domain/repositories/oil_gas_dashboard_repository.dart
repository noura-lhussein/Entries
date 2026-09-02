import '../../../../core/network/api_result.dart';

abstract class OilGasDashboardRepository {
  Future<ApiResult<Map<String, dynamic>>> getDashboard({
    String period = 'day',
    String? date,
    String? month,
  });
}
