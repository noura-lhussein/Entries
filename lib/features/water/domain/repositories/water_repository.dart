import 'package:dio/dio.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/entities/water_import_result_entity.dart';
import '../entities/water_lookups_entity.dart';

abstract class WaterRepository {
  Future<ApiResult<WaterLookupsEntity>> getWaterLookups();

  Future<ApiResult<Map<String, dynamic>>> getImportStatus();

  Future<ApiResult<WaterImportResultEntity>> saveDamDaily({
    required DateTime readingDate,
    required int? damId,
    required double? storageMcm,
    required String notes,
  });

  Future<ApiResult<WaterImportResultEntity>> saveRainfallDaily({
    required DateTime observationDate,
    required String basinSlug,
    required String stationName,
    required String governorate,
    required double? precipitationMm,
    required String notes,
    int? stationId,
  });

  Future<ApiResult<Map<String, dynamic>?>> getEuphratesDaily(DateTime date);

  Future<ApiResult<WaterImportResultEntity>> saveEuphratesDaily({
    required Map<String, dynamic> payload,
  });

  Future<ApiResult<Map<String, dynamic>>> getDrinkingWaterStation(int stationId);

  Future<ApiResult<WaterImportResultEntity>> saveDrinkingWaterStation({
    required Map<String, dynamic> payload,
  });

  Future<ApiResult<WaterImportResultEntity>> importRainfall({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> importDams({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> importEuphrates({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterGeo({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterSurvey({
    required List<MultipartFile> files,
  });

  Future<ApiResult<WaterImportResultEntity>> clearRainfall();

  Future<ApiResult<WaterImportResultEntity>> clearDamStorage();

  Future<ApiResult<WaterImportResultEntity>> clearEuphrates();

  Future<ApiResult<Response<List<int>>>> downloadTemplate(String kind);

  Future<ApiResult<Response<List<int>>>> exportDrinkingWaterSurvey();
}
