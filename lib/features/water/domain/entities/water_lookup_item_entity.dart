import 'package:equatable/equatable.dart';

class WaterLookupItemEntity extends Equatable {
  final int id;
  final String name;
  /// Used by rainfall API: basin_slug / governorate values
  final String? slug;

  /// Used by rainfall when selecting a station: station.basin_slug / station.governorate
  final String? basinSlug;
  final String? governorate;

  const WaterLookupItemEntity({
    this.id = 0,
    this.name = '',
    this.slug,
    this.basinSlug,
    this.governorate,
  });

  @override
  List<Object?> get props => [id, name, slug, basinSlug, governorate];
}
