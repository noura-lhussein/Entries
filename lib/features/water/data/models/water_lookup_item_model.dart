import '../../domain/entities/water_lookup_item_entity.dart';

class WaterLookupItemModel extends WaterLookupItemEntity {
  const WaterLookupItemModel({
    super.id,
    super.name,
    super.slug,
    super.basinSlug,
    super.governorate,
  });

  factory WaterLookupItemModel.fromJson(Map<String, dynamic> json) {
    return WaterLookupItemModel(
      id: _parseInt(json['id']),
      slug: json['slug']?.toString(),
      basinSlug: json['basin_slug']?.toString(),
      governorate: json['governorate']?.toString(),
      name: _bestName(json),
    );
  }

  static String _bestName(Map<String, dynamic> json) {
    final name = json['name'];
    if (name != null && name.toString().trim().isNotEmpty) return name.toString();

    final nameAr = json['name_ar'];
    if (nameAr != null && nameAr.toString().trim().isNotEmpty) return nameAr.toString();

    final nameEn = json['name_en'];
    if (nameEn != null && nameEn.toString().trim().isNotEmpty) return nameEn.toString();

    final stationCode = json['station_code'];
    if (stationCode != null && stationCode.toString().trim().isNotEmpty) return stationCode.toString();

    final governorate = json['governorate'];
    if (governorate != null && governorate.toString().trim().isNotEmpty) return governorate.toString();

    return '';
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    if (value is double) return value.toInt();
    return 0;
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'slug': slug,
        'basin_slug': basinSlug,
        'governorate': governorate,
      };
}
