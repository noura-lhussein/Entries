import 'package:dio/dio.dart';

import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/repositories/geology_repository.dart';
import '../datasources/geology_remote_data_source.dart';

class GeologyRepositoryImpl implements GeologyRepository {
  final GeologyRemoteDataSource _remote;
  GeologyRepositoryImpl(this._remote);

  Future<ApiResult<T>> _run<T>(Future<T> Function() body) async {
    try {
      return ApiResult.success(await body());
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getDashboard({int? planYear}) =>
      _run(() => _remote.getDashboard(planYear: planYear));

  @override
  Future<ApiResult<Map<String, dynamic>>> getDailyReport(String reportDate) =>
      _run(() => _remote.getDailyReport(reportDate));

  @override
  Future<ApiResult<Map<String, dynamic>>> saveDailyReport(
    Map<String, dynamic> body,
  ) =>
      _run(() => _remote.saveDailyReport(body));

  @override
  Future<ApiResult<Response<List<int>>>> downloadReport({
    required int planYear,
    String format = 'xlsx',
  }) =>
      _run(() => _remote.downloadReport(planYear: planYear, format: format));

  @override
  Future<ApiResult<Response<List<int>>>> downloadOreTemplate({int? planYear}) =>
      _run(() => _remote.downloadOreTemplate(planYear: planYear));

  @override
  Future<ApiResult<Response<List<int>>>> exportOreProduction(int planYear) =>
      _run(() => _remote.exportOreProduction(planYear));

  @override
  Future<ApiResult<Map<String, dynamic>>> importOreProduction(
    MultipartFile file, {
    bool publish = true,
  }) =>
      _run(() => _remote.importOreProduction(file, publish: publish));
}
