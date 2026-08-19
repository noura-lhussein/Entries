import 'package:dio/dio.dart';
import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/entities/water_import_result_entity.dart';
import '../../domain/entities/water_lookups_entity.dart';
import '../../domain/repositories/water_repository.dart';
import '../datasources/water_admin_remote_data_source.dart';
import '../datasources/water_remote_data_source.dart';

class WaterRepositoryImpl implements WaterRepository {
  final WaterRemoteDataSource _remoteDataSource;
  final WaterAdminRemoteDataSource _adminDataSource;

  WaterRepositoryImpl(
    this._remoteDataSource,
    this._adminDataSource,
  );

  @override
  Future<ApiResult<WaterLookupsEntity>> getWaterLookups() async {
    try {
      final response = await _remoteDataSource.getWaterLookups();
      return ApiResult.success(response);
    } catch (error) {
      print(error);
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getImportStatus() async {
    try {
      final res = await _adminDataSource.getImportStatus();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> saveDamDaily({
    required DateTime readingDate,
    required int? damId,
    required double? storageMcm,
    required String notes,
  }) async {
    try {
      final res = await _adminDataSource.saveDamDaily(
        readingDate: readingDate,
        damId: damId,
        storageMcm: storageMcm,
        notes: notes,
      );
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> saveRainfallDaily({
    required DateTime observationDate,
    required String basinSlug,
    required String stationName,
    required String governorate,
    required double? precipitationMm,
    required String notes,
    int? stationId,
  }) async {
    try {
      final res = await _adminDataSource.saveRainfallDaily(
        observationDate: observationDate,
        basinSlug: basinSlug,
        stationName: stationName,
        governorate: governorate,
        precipitationMm: precipitationMm,
        notes: notes,
        stationId: stationId,
      );
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>?>> getEuphratesDaily(DateTime date) async {
    try {
      final res = await _adminDataSource.getEuphratesDaily(date);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> saveEuphratesDaily({
    required Map<String, dynamic> payload,
  }) async {
    try {
      final res = await _adminDataSource.saveEuphratesDaily(payload: payload);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getDrinkingWaterStation(int stationId) async {
    try {
      final res = await _adminDataSource.getDrinkingWaterStation(stationId);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> saveDrinkingWaterStation({
    required Map<String, dynamic> payload,
  }) async {
    try {
      final res = await _adminDataSource.saveDrinkingWaterStation(payload: payload);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> importRainfall({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    try {
      final res = await _adminDataSource.importRainfall(files: files, clear: clear);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> importDams({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    try {
      final res = await _adminDataSource.importDams(files: files, clear: clear);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> importEuphrates({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    try {
      final res = await _adminDataSource.importEuphrates(files: files, clear: clear);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterGeo({
    required List<MultipartFile> files,
    required bool clear,
  }) async {
    try {
      final res = await _adminDataSource.importDrinkingWaterGeo(files: files, clear: clear);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> importDrinkingWaterSurvey({
    required List<MultipartFile> files,
  }) async {
    try {
      final res = await _adminDataSource.importDrinkingWaterSurvey(files: files);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> clearRainfall() async {
    try {
      final res = await _adminDataSource.clearRainfall();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> clearDamStorage() async {
    try {
      final res = await _adminDataSource.clearDamStorage();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<WaterImportResultEntity>> clearEuphrates() async {
    try {
      final res = await _adminDataSource.clearEuphrates();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Response<List<int>>>> downloadTemplate(String kind) async {
    try {
      final res = await _adminDataSource.downloadTemplate(kind);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Response<List<int>>>> exportDrinkingWaterSurvey() async {
    try {
      final res = await _adminDataSource.exportDrinkingWaterSurvey();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }
}
