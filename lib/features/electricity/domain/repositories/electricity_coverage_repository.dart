import '../../../../core/network/api_result.dart';

abstract class ElectricityCoverageRepository {
  Future<ApiResult<Map<String, dynamic>>> getTargetCoverage({String? date});
}
