import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';

/// Electricity APIs — matches moe-portal [ElectricityApiService].
class ElectricityRemoteDataSource {
  final Dio _dio;
  const ElectricityRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getDashboard({
    String period = 'day',
    String? date,
    String? month,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityDashboard,
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
      ApiConstants.electricityReportUpsert,
      data: payload,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getReportDetail(String date) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityReportDetail,
      queryParameters: {'date': date},
    );
    return res.data ?? const {};
  }

  Future<List<dynamic>> getReportDates() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityReportDates,
    );
    final dates = res.data?['dates'];
    return dates is List ? dates : const [];
  }

  Future<List<dynamic>> listReports() async {
    final res = await _dio.get(ApiConstants.electricityReports);
    final data = res.data;
    if (data is List) return data;
    if (data is Map) {
      final results = data['results'] ?? data['items'] ?? data['reports'];
      if (results is List) return results;
    }
    return const [];
  }

  Future<Map<String, dynamic>> getMapLayerGeoJson(
    String layerId, {
    String? governorate,
    String? district,
    String? subdistrict,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityMapLayerGeoJson(layerId),
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

  Future<Map<String, dynamic>> getTargetCoverage({String? date}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityTargetCoverage,
      queryParameters: {
        if (date != null && date.isNotEmpty) 'date': date,
      },
    );
    return res.data ?? const {};
  }

  Future<Response<List<int>>> downloadReportTemplate({String? date}) {
    return _dio.get<List<int>>(
      ApiConstants.electricityReportTemplate,
      queryParameters: {
        if (date != null) 'date': date,
      },
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Map<String, dynamic>> importDailyReport(
    MultipartFile file, {
    bool publish = true,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.electricityReportImport,
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
      ApiConstants.electricityReportExport,
      queryParameters: {
        'period': period,
        'format': format,
        if (date != null) 'date': date,
        if (month != null) 'month': month,
      },
      options: Options(responseType: ResponseType.bytes),
    );
  }

  Future<Map<String, dynamic>> getAdminRegistry() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityAdminRegistry,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> listAdminResource(
    String slug, {
    int page = 1,
    String? search,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.electricityAdminResource(slug),
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
      ApiConstants.electricityAdminResource(slug),
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
      '${ApiConstants.electricityAdminResource(slug)}$pk/',
      data: body,
    );
    return res.data ?? const {};
  }

  Future<void> deleteAdminResource(String slug, String pk) async {
    await _dio.delete('${ApiConstants.electricityAdminResource(slug)}$pk/');
  }
}
