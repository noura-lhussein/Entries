import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';

/// Oil & Gas APIs — matches moe-portal [OilGasApiService].
class OilGasRemoteDataSource {
  final Dio _dio;
  const OilGasRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getDashboard({
    String period = 'day',
    String? date,
    String? month,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasDashboard,
      queryParameters: {
        'period': period,
        if (date != null) 'date': date,
        if (month != null) 'month': month,
      },
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> upsertDailyReport(
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.oilGasReportUpsert,
      data: payload,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> upsertDailyOperations(
    Map<String, dynamic> payload,
  ) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.oilGasOperationsDaily,
      data: payload,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getReportDetail(String date) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasReportDetail,
      queryParameters: {'date': date},
    );
    return res.data ?? const {};
  }

  Future<List<dynamic>> getReportDates() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasReportDates,
    );
    final dates = res.data?['dates'];
    return dates is List ? dates : const [];
  }

  Future<List<dynamic>> listReports() async {
    final res = await _dio.get(ApiConstants.oilGasReports);
    final data = res.data;
    if (data is List) return data;
    if (data is Map) {
      final results = data['results'] ?? data['items'] ?? data['reports'];
      if (results is List) return results;
    }
    return const [];
  }

  Future<Map<String, dynamic>> publishDay(String productionDate) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.oilGasOperationsPublish,
      data: {'production_date': productionDate},
    );
    return res.data ?? const {};
  }

  Future<List<dynamic>> listFields() async {
    final res = await _dio.get(ApiConstants.oilGasMasterFields);
    final data = res.data;
    return data is List ? data : const [];
  }

  Future<List<dynamic>> listRefineries() async {
    final res = await _dio.get(ApiConstants.oilGasMasterRefineries);
    final data = res.data;
    return data is List ? data : const [];
  }

  Future<List<dynamic>> listFacilities({
    String? sector,
    String? facilityType,
  }) async {
    final res = await _dio.get(
      ApiConstants.oilGasMasterFacilities,
      queryParameters: {
        if (sector != null) 'sector': sector,
        if (facilityType != null) 'facility_type': facilityType,
      },
    );
    final data = res.data;
    return data is List ? data : const [];
  }

  Future<Map<String, dynamic>> getMapLayerGeoJson(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasMapLayerGeoJson(layerId),
      queryParameters: {
        if (governorate != null && governorate.isNotEmpty)
          'governorate': governorate,
        if (district != null && district.isNotEmpty) 'district': district,
        if (subdistrict != null && subdistrict.isNotEmpty)
          'subdistrict': subdistrict,
      },
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getFieldTargetMatrix(String date) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasTargetsFields,
      queryParameters: {'date': date},
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getMonthlyRollup(
    String date, {
    String? scopeType,
    String? scopeCode,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasTargetsMonthly,
      queryParameters: {
        'date': date,
        if (scopeType != null) 'scope_type': scopeType,
        if (scopeCode != null) 'scope_code': scopeCode,
      },
    );
    return res.data ?? const {};
  }

  Future<List<dynamic>> getTargetCatalog() async {
    final res = await _dio.get(ApiConstants.oilGasTargetsCatalog);
    final data = res.data;
    return data is List ? data : const [];
  }

  Future<List<dynamic>> listTargets({
    String? metricKey,
    String? scopeType,
    String? scopeCode,
    String? periodStart,
  }) async {
    final res = await _dio.get(
      ApiConstants.oilGasTargets,
      queryParameters: {
        if (metricKey != null) 'metric_key': metricKey,
        if (scopeType != null) 'scope_type': scopeType,
        if (scopeCode != null) 'scope_code': scopeCode,
        if (periodStart != null) 'period_start': periodStart,
      },
    );
    final data = res.data;
    if (data is List) return data;
    if (data is Map) {
      final results = data['results'] ?? data['items'];
      if (results is List) return results;
    }
    return const [];
  }

  Future<Map<String, dynamic>> createTarget(Map<String, dynamic> body) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.oilGasTargets,
      data: body,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> updateTarget(
    int id,
    Map<String, dynamic> body,
  ) async {
    final res = await _dio.patch<Map<String, dynamic>>(
      '${ApiConstants.oilGasTargets}$id/',
      data: body,
    );
    return res.data ?? const {};
  }

  Future<void> deleteTarget(int id) async {
    await _dio.delete('${ApiConstants.oilGasTargets}$id/');
  }

  Future<Map<String, dynamic>> compareTargets({
    required String date,
    String? scopeType,
    String? scopeCode,
    String? metricKey,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasTargetsCompare,
      queryParameters: {
        'date': date,
        if (scopeType != null) 'scope_type': scopeType,
        if (scopeCode != null) 'scope_code': scopeCode,
        if (metricKey != null) 'metric_key': metricKey,
      },
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getTargetCoverage({String? date}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasTargetsCoverage,
      queryParameters: {
        if (date != null && date.isNotEmpty) 'date': date,
      },
    );
    return res.data ?? const {};
  }

  Future<Response<List<int>>> downloadExecutiveTemplate({String? date}) {
    return _dio.get<List<int>>(
      ApiConstants.oilGasReportTemplate,
      queryParameters: {
        if (date != null) 'date': date,
      },
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Map<String, dynamic>> importExecutiveReport(
    MultipartFile file, {
    bool publish = true,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.oilGasReportImport,
      data: FormData.fromMap({
        'file': file,
        'publish': publish ? 'true' : 'false',
      }),
    );
    return res.data ?? const {};
  }

  Future<Response<List<int>>> exportReport({
    String? date,
    String? month,
    String period = 'day',
    String format = 'xlsx',
  }) async {
    return _dio.get<List<int>>(
      ApiConstants.oilGasReportExport,
      queryParameters: {
        'period': period,
        'format': format,
        'date': ?date,
        'month': ?month,
      },
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Map<String, dynamic>> getAdminRegistry() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasAdminRegistry,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> listAdminResource(
    String slug, {
    int page = 1,
    String? search,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.oilGasAdminResource(slug),
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
      ApiConstants.oilGasAdminResource(slug),
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
      '${ApiConstants.oilGasAdminResource(slug)}$pk/',
      data: body,
    );
    return res.data ?? const {};
  }

  Future<void> deleteAdminResource(String slug, String pk) async {
    await _dio.delete('${ApiConstants.oilGasAdminResource(slug)}$pk/');
  }
}
