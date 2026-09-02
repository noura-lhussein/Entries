import '../../../../core/network/api_result.dart';

abstract class OilGasMapRepository {
  Future<ApiResult<Map<String, dynamic>>> getMapLayerGeoJson(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  });
}
