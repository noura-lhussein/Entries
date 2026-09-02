import '../../../../core/network/api_result.dart';

abstract class OilGasTargetsRepository {
  Future<ApiResult<Map<String, dynamic>>> getFieldTargetMatrix(String date);

  Future<ApiResult<Map<String, dynamic>>> getMonthlyRollup(
    String date, {
    String? scopeType,
    String? scopeCode,
  });

  Future<ApiResult<List<dynamic>>> getTargetCatalog();

  Future<ApiResult<List<dynamic>>> listTargets({
    String? metricKey,
    String? scopeType,
    String? scopeCode,
    String? periodStart,
  });

  Future<ApiResult<Map<String, dynamic>>> createTarget(
    Map<String, dynamic> body,
  );

  Future<ApiResult<Map<String, dynamic>>> updateTarget(
    int id,
    Map<String, dynamic> body,
  );

  Future<ApiResult<void>> deleteTarget(int id);

  Future<ApiResult<Map<String, dynamic>>> compareTargets({
    required String date,
    String? scopeType,
    String? scopeCode,
    String? metricKey,
  });

  Future<ApiResult<Map<String, dynamic>>> getTargetCoverage({String? date});
}
