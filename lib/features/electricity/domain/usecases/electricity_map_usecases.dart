import '../../../../core/network/api_result.dart';
import '../repositories/electricity_map_repository.dart';

class GetElectricityMapLayerUseCase {
  final ElectricityMapRepository _repository;

  GetElectricityMapLayerUseCase(this._repository);

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
