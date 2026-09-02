import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';

abstract class WaterDrinkingRepository {
  Future<ApiResult<Map<String, dynamic>>> getDrinkingWaterStation(int stationId);

  Future<ApiResult<WaterImportResultEntity>> saveDrinkingWaterStation({
    required Map<String, dynamic> payload,
  });

  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterGeo({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterSurvey({
    required List<MultipartFile> files,
  });
}
