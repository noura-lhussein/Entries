import 'package:dio/dio.dart';

import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/repositories/electricity_repository.dart';
import '../datasources/electricity_remote_data_source.dart';

class ElectricityRepositoryImpl implements ElectricityRepository {
  final ElectricityRemoteDataSource _remote;

  ElectricityRepositoryImpl(this._remote);

  @override
  Future<ApiResult<Map<String, dynamic>>> getDashboard({
    String period = 'day',
    String? date,
    String? month,
  }) async {
    try {
      final res = await _remote.getDashboard(
        period: period,
        date: date,
        month: month,
      );
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> upsertDailyReport(
    Map<String, dynamic> payload,
  ) async {
    try {
      final res = await _remote.upsertDailyReport(payload);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getReportDetail(String date) async {
    try {
      final res = await _remote.getReportDetail(date);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<List<dynamic>>> getReportDates() async {
    try {
      final res = await _remote.getReportDates();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<List<dynamic>>> listReports() async {
    try {
      final res = await _remote.listReports();
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Response<List<int>>>> downloadReportTemplate({
    String? date,
  }) async {
    try {
      final res = await _remote.downloadReportTemplate(date: date);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> importDailyReport(
    MultipartFile file, {
    bool publish = true,
  }) async {
    try {
      final res = await _remote.importDailyReport(file, publish: publish);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Response<List<int>>>> exportReport({
    String? date,
    String? month,
    String period = 'day',
    String format = 'xlsx',
  }) async {
    try {
      final res = await _remote.exportReport(
        date: date,
        month: month,
        period: period,
        format: format,
      );
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getMapLayerGeoJson(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  }) async {
    try {
      final res = await _remote.getMapLayerGeoJson(
        layerId,
        governorate: governorate,
        district: district,
        subdistrict: subdistrict,
      );
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getTargetCoverage({
    String? date,
  }) async {
    try {
      final res = await _remote.getTargetCoverage(date: date);
      return ApiResult.success(res);
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }
}
