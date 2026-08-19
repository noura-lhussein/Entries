import 'package:equatable/equatable.dart';
import 'water_lookup_item_entity.dart';

class WaterLookupsEntity extends Equatable {
  final List<WaterLookupItemEntity> basins;
  final List<WaterLookupItemEntity> governorates;
  final List<WaterLookupItemEntity> dams;
  final List<WaterLookupItemEntity> stations;
  final List<WaterLookupItemEntity> drinkingWaterStations;

  const WaterLookupsEntity({
    required this.basins,
    required this.governorates,
    required this.dams,
    required this.stations,
    required this.drinkingWaterStations,
  });

  factory WaterLookupsEntity.empty() => const WaterLookupsEntity(
        basins: [],
        governorates: [],
        dams: [],
        stations: [],
        drinkingWaterStations: [],
      );

  @override
  List<Object?> get props => [basins, governorates, dams, stations, drinkingWaterStations];
}
