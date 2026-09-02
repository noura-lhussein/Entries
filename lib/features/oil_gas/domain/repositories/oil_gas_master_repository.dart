import '../../../../core/network/api_result.dart';

abstract class OilGasMasterRepository {
  Future<ApiResult<List<dynamic>>> listFields();

  Future<ApiResult<List<dynamic>>> listRefineries();

  Future<ApiResult<List<dynamic>>> listFacilities({
    String? sector,
    String? facilityType,
  });
}
