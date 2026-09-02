import '../../../../core/network/api_result.dart';
import '../entities/water_lookups_entity.dart';
import '../repositories/water_lookups_repository.dart';

class GetWaterLookupsUseCase {
  final WaterLookupsRepository _repository;

  GetWaterLookupsUseCase(this._repository);

  Future<ApiResult<WaterLookupsEntity>> call() {
    return _repository.getWaterLookups();
  }
}
