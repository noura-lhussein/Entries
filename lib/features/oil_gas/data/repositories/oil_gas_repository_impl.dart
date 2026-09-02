import 'package:dio/dio.dart';

import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/repositories/oil_gas_repository.dart';
import '../datasources/oil_gas_remote_data_source.dart';

class OilGasRepositoryImpl implements OilGasRepository {
  final OilGasRemoteDataSource _remote;
  OilGasRepositoryImpl(this._remote);

  Future<ApiResult<T>> _run<T>(Future<T> Function() body) async {
    try {
      return ApiResult.success(await body());
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<Map<String, dynamic>>> getDashboard({
    String period = 'day',
    String? date,
    String? month,
  }) =>
      _run(() => _remote.getDashboard(period: period, date: date, month: month));

  @override
  Future<ApiResult<Map<String, dynamic>>> upsertDailyReport(
    Map<String, dynamic> payload,
  ) =>
      _run(() => _remote.upsertDailyReport(payload));

  @override
  Future<ApiResult<Map<String, dynamic>>> getReportDetail(String date) =>
      _run(() => _remote.getReportDetail(date));

  @override
  Future<ApiResult<List<dynamic>>> getReportDates() =>
      _run(() => _remote.getReportDates());

  @override
  Future<ApiResult<List<dynamic>>> listReports() =>
      _run(() => _remote.listReports());

  @override
  Future<ApiResult<Map<String, dynamic>>> upsertDailyOperations(
    Map<String, dynamic> payload,
  ) =>
      _run(() => _remote.upsertDailyOperations(payload));

  @override
  Future<ApiResult<Map<String, dynamic>>> publishDay(String productionDate) =>
      _run(() => _remote.publishDay(productionDate));

  @override
  Future<ApiResult<List<dynamic>>> listFields() =>
      _run(() => _remote.listFields());

  @override
  Future<ApiResult<List<dynamic>>> listRefineries() =>
      _run(() => _remote.listRefineries());

  @override
  Future<ApiResult<List<dynamic>>> listFacilities({
    String? sector,
    String? facilityType,
  }) =>
      _run(() => _remote.listFacilities(
            sector: sector,
            facilityType: facilityType,
          ));

  @override
  Future<ApiResult<Response<List<int>>>> downloadExecutiveTemplate({
    String? date,
  }) =>
      _run(() => _remote.downloadExecutiveTemplate(date: date));

  @override
  Future<ApiResult<Map<String, dynamic>>> importExecutiveReport(
    MultipartFile file, {
    bool publish = true,
  }) =>
      _run(() => _remote.importExecutiveReport(file, publish: publish));

  @override
  Future<ApiResult<Response<List<int>>>> exportReport({
    String? date,
    String? month,
    String period = 'day',
    String format = 'xlsx',
  }) =>
      _run(() => _remote.exportReport(
            date: date,
            month: month,
            period: period,
            format: format,
          ));

  @override
  Future<ApiResult<Map<String, dynamic>>> getMapLayerGeoJson(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  }) =>
      _run(() => _remote.getMapLayerGeoJson(
            layerId,
            governorate: governorate,
            district: district,
            subdistrict: subdistrict,
          ));

  @override
  Future<ApiResult<Map<String, dynamic>>> getFieldTargetMatrix(String date) =>
      _run(() => _remote.getFieldTargetMatrix(date));

  @override
  Future<ApiResult<Map<String, dynamic>>> getMonthlyRollup(
    String date, {
    String? scopeType,
    String? scopeCode,
  }) =>
      _run(() => _remote.getMonthlyRollup(
            date,
            scopeType: scopeType,
            scopeCode: scopeCode,
          ));

  @override
  Future<ApiResult<List<dynamic>>> getTargetCatalog() =>
      _run(() => _remote.getTargetCatalog());

  @override
  Future<ApiResult<List<dynamic>>> listTargets({
    String? metricKey,
    String? scopeType,
    String? scopeCode,
    String? periodStart,
  }) =>
      _run(() => _remote.listTargets(
            metricKey: metricKey,
            scopeType: scopeType,
            scopeCode: scopeCode,
            periodStart: periodStart,
          ));

  @override
  Future<ApiResult<Map<String, dynamic>>> createTarget(
    Map<String, dynamic> body,
  ) =>
      _run(() => _remote.createTarget(body));

  @override
  Future<ApiResult<Map<String, dynamic>>> updateTarget(
    int id,
    Map<String, dynamic> body,
  ) =>
      _run(() => _remote.updateTarget(id, body));

  @override
  Future<ApiResult<void>> deleteTarget(int id) =>
      _run(() => _remote.deleteTarget(id));

  @override
  Future<ApiResult<Map<String, dynamic>>> compareTargets({
    required String date,
    String? scopeType,
    String? scopeCode,
    String? metricKey,
  }) =>
      _run(() => _remote.compareTargets(
            date: date,
            scopeType: scopeType,
            scopeCode: scopeCode,
            metricKey: metricKey,
          ));

  @override
  Future<ApiResult<Map<String, dynamic>>> getTargetCoverage({String? date}) =>
      _run(() => _remote.getTargetCoverage(date: date));
}
