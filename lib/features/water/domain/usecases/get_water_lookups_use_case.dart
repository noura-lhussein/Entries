import '../../../../core/network/api_result.dart';
import '../entities/water_lookups_entity.dart';
import '../repositories/water_repository.dart';

class GetWaterLookupsUseCase {
  final WaterRepository _repository;

  GetWaterLookupsUseCase(this._repository);

  Future<ApiResult<WaterLookupsEntity>> call() async {
    return await _repository.getWaterLookups();
  }
}
