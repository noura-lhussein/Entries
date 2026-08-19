import '../../domain/entities/water_lookups_entity.dart';
import 'water_lookup_item_model.dart';

class WaterLookupsModel extends WaterLookupsEntity {
  const WaterLookupsModel({
    required super.basins,
    required super.governorates,
    required super.dams,
    required super.stations,
    required super.drinkingWaterStations,
  });

  factory WaterLookupsModel.fromJson(Map<String, dynamic> json) {
    return WaterLookupsModel(
      basins: _parseList(json['basins']),
      governorates: _parseList(json['governorates']),
      dams: _parseList(json['dams']),
      stations: _parseList(json['stations']),
      drinkingWaterStations: _parseList(
        json['drinking_water_stations'] ?? json['drinkingWaterStations'],
      ),
    );
  }

  static List<WaterLookupItemModel> _parseList(dynamic data) {
    if (data is! List) return [];
    return data.map((item) {
      if (item is Map<String, dynamic>) {
        return WaterLookupItemModel.fromJson(item);
      } else if (item is String) {
        // Governorates come as string[] in moe-portal.
        return WaterLookupItemModel(id: 0, name: item, slug: item);
      }
      return const WaterLookupItemModel(id: 0, name: '');
    }).toList();
  }

  Map<String, dynamic> toJson() => {
        'basins': basins
            .map((e) => WaterLookupItemModel(id: e.id, name: e.name).toJson())
            .toList(),
        'governorates': governorates
            .map((e) => WaterLookupItemModel(id: e.id, name: e.name).toJson())
            .toList(),
        'dams': dams
            .map((e) => WaterLookupItemModel(id: e.id, name: e.name).toJson())
            .toList(),
        'stations': stations
            .map((e) => WaterLookupItemModel(id: e.id, name: e.name).toJson())
            .toList(),
        'drinking_water_stations': drinkingWaterStations
            .map((e) => WaterLookupItemModel(id: e.id, name: e.name).toJson())
            .toList(),
      };
}
