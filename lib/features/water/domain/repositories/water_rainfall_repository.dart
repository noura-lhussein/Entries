import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';

abstract class WaterRainfallRepository {
  Future<ApiResult<WaterImportResultEntity>> saveRainfallDaily({
    required DateTime observationDate,
    required String basinSlug,
    required String stationName,
    required String governorate,
    required double? precipitationMm,
    required String notes,
    int? stationId,
  });

  Future<ApiResult<WaterImportResultEntity>> importRainfall({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> clearRainfall();
}
