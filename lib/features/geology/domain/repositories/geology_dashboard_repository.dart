import '../../../../core/network/api_result.dart';

abstract class GeologyDashboardRepository {
  Future<ApiResult<Map<String, dynamic>>> getDashboard({int? planYear});
}
