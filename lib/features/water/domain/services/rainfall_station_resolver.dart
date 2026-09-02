import '../entities/water_lookup_item_entity.dart';

class RainfallStationResolver {
  const RainfallStationResolver._();

  static ({
    WaterLookupItemEntity? basin,
    WaterLookupItemEntity? governorate,
  }) resolve({
    required WaterLookupItemEntity station,
    required List<WaterLookupItemEntity> basins,
    required List<WaterLookupItemEntity> governorates,
  }) {
    WaterLookupItemEntity? basin;
    WaterLookupItemEntity? gov;
    if (station.basinSlug != null && station.basinSlug!.isNotEmpty) {
      for (final b in basins) {
        if (b.slug == station.basinSlug) {
          basin = b;
          break;
        }
      }
    }
    if (station.governorate != null && station.governorate!.isNotEmpty) {
      for (final g in governorates) {
        if (g.slug == station.governorate || g.name == station.governorate) {
          gov = g;
          break;
        }
      }
    }
    return (basin: basin, governorate: gov);
  }
}
