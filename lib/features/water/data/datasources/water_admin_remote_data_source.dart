import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';
import '../../domain/entities/water_import_result_entity.dart';

class WaterAdminRemoteDataSource {
  final Dio _dio;

  const WaterAdminRemoteDataSource(this._dio);

  String _asIsoDate(DateTime d) {
    final y = d.year.toString().padLeft(4, '0');
    final m = d.month.toString().padLeft(2, '0');
    final day = d.day.toString().padLeft(2, '0');
    return '$y-$m-$day';
  }

  /// Backend expects `?payload=<json>` (FastAPI query field), matching 422
  /// `loc: [query, payload]` when the body alone is sent.
  Future<Response<Map<String, dynamic>>> _postWithPayload(
    String url,
    Map<String, dynamic> payload,
  ) {
    return _dio.post<Map<String, dynamic>>(
      url,
      queryParameters: {'payload': jsonEncode(payload)},
      data: payload,
    );
  }

  Future<Map<String, dynamic>> getImportStatus() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.waterImportStatus,
    );
    return res.data ?? const {};
  }

  Future<WaterImportResultEntity> saveDamDaily({
    required DateTime readingDate,
    required int? damId,
    required double? storageMcm,
    required String notes,
  }) async {
    final payload = {
      'reading_date': _asIsoDate(readingDate),
      'dam_id': damId,
      'storage_mcm': storageMcm,
      'notes': notes,
    };

    final res = await _postWithPayload(
      ApiConstants.waterDailyDamStorage,
      payload,
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<WaterImportResultEntity> saveRainfallDaily({
    required DateTime observationDate,
    required String basinSlug,
    required String stationName,
    required String governorate,
    required double? precipitationMm,
    required String notes,
    int? stationId,
  }) async {
    final payload = {
      'observation_date': _asIsoDate(observationDate),
      'basin_slug': basinSlug,
      'station_name': stationName,
      'governorate': governorate,
      'precipitation_mm': precipitationMm,
      'notes': notes,
      if (stationId != null) 'station_id': stationId,
    };

    final res = await _postWithPayload(
      ApiConstants.waterDailyRainfall,
      payload,
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<Map<String, dynamic>?> getEuphratesDaily(DateTime date) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.waterDailyEuphrates,
      queryParameters: {'date': _asIsoDate(date)},
    );
    return res.data?['reading'] as Map<String, dynamic>?;
  }

  Future<WaterImportResultEntity> saveEuphratesDaily({
    required Map<String, dynamic> payload,
  }) async {
    final res = await _postWithPayload(
      ApiConstants.waterDailyEuphrates,
      payload,
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<Map<String, dynamic>> getDrinkingWaterStation(int stationId) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.waterDailyDrinkingWater,
      queryParameters: {'station_id': stationId.toString()},
    );
    final station = res.data?['station'];
    if (station is Map<String, dynamic>) return station;
    return <String, dynamic>{};
  }

  Future<WaterImportResultEntity> saveDrinkingWaterStation({
    required Map<String, dynamic> payload,
  }) async {
    final res = await _postWithPayload(
      ApiConstants.waterDailyDrinkingWater,
      payload,
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<WaterImportResultEntity> clearRainfall() async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.waterClearRainfall,
      data: const {},
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<WaterImportResultEntity> clearDamStorage() async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.waterClearDams,
      data: const {},
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<WaterImportResultEntity> clearEuphrates() async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.waterClearEuphrates,
      data: const {},
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  /// Template kinds match moe-portal: rainfall | dams-metadata | dams-storage | euphrates | drinking-water-survey
  Future<Response<List<int>>> downloadTemplate(String kind) async {
    return _dio.get<List<int>>(
      ApiConstants.waterTemplates,
      queryParameters: {'kind': kind},
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Response<List<int>>> exportDrinkingWaterSurvey() async {
    return _dio.get<List<int>>(
      ApiConstants.waterExportDrinkingWaterSurvey,
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<WaterImportResultEntity> _postFiles({
    required String url,
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    final formData = FormData();
    for (final f in files) {
      formData.files.add(MapEntry('files', f));
    }
    formData.fields.add(MapEntry('clear', clear ? 'true' : 'false'));

    final res = await _dio.post<Map<String, dynamic>>(url, data: formData);
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<WaterImportResultEntity> importRainfall({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    return _postFiles(
      url: ApiConstants.waterImportRainfall,
      files: files,
      clear: clear,
    );
  }

  Future<WaterImportResultEntity> importDams({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    return _postFiles(
      url: ApiConstants.waterImportDams,
      files: files,
      clear: clear,
    );
  }

  Future<WaterImportResultEntity> importEuphrates({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    return _postFiles(
      url: ApiConstants.waterImportEuphrates,
      files: files,
      clear: clear,
    );
  }

  Future<WaterImportResultEntity> importDrinkingWaterGeo({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    return _postFiles(
      url: ApiConstants.waterImportDrinkingWaterGeo,
      files: files,
      clear: clear,
    );
  }

  Future<WaterImportResultEntity> importDrinkingWaterSurvey({
    required List<MultipartFile> files,
  }) async {
    final formData = FormData();
    for (final f in files) {
      formData.files.add(MapEntry('files', f));
    }
    formData.fields.add(const MapEntry('clear', 'false'));

    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.waterImportDrinkingWaterSurvey,
      data: formData,
    );
    return WaterImportResultEntity.fromJson(res.data ?? const {});
  }

  Future<Map<String, dynamic>> getAdminRegistry() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.waterRegistry,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> listAdminResource(
    String slug, {
    int page = 1,
    String? search,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.waterAdminResource(slug),
      queryParameters: {
        'page': page,
        if (search != null && search.isNotEmpty) 'search': search,
      },
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> createAdminResource(
    String slug,
    Map<String, dynamic> body,
  ) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.waterAdminResource(slug),
      data: body,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> updateAdminResource(
    String slug,
    String pk,
    Map<String, dynamic> body,
  ) async {
    final res = await _dio.patch<Map<String, dynamic>>(
      '${ApiConstants.waterAdminResource(slug)}$pk/',
      data: body,
    );
    return res.data ?? const {};
  }

  Future<void> deleteAdminResource(String slug, String pk) async {
    await _dio.delete('${ApiConstants.waterAdminResource(slug)}$pk/');
  }
}
