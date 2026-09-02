import '../../../../core/network/api_result.dart';
import '../entities/water_lookups_entity.dart';

abstract class WaterLookupsRepository {
  Future<ApiResult<WaterLookupsEntity>> getWaterLookups();
}
