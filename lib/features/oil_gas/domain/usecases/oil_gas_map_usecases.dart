import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_map_repository.dart';

class GetOilGasMapLayerUseCase {
  final OilGasMapRepository _repository;
  GetOilGasMapLayerUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  }) {
    return _repository.getMapLayerGeoJson(
      layerId,
      governorate: governorate,
      district: district,
      subdistrict: subdistrict,
    );
  }
}
