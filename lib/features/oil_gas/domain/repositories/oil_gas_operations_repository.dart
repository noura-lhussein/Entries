import '../../../../core/network/api_result.dart';

abstract class OilGasOperationsRepository {
  Future<ApiResult<Map<String, dynamic>>> upsertDailyOperations(
    Map<String, dynamic> payload,
  );

  Future<ApiResult<Map<String, dynamic>>> publishDay(String productionDate);
}
