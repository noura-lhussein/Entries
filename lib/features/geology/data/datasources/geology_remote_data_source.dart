import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';
import '../../../../core/utils/open_downloaded_file.dart';

/// Geology / mining APIs — matches moe-portal GeologyApiService + GeologyAdminApiService.
class GeologyRemoteDataSource {
  final Dio _dio;
  const GeologyRemoteDataSource(this._dio);

  Future<Map<String, dynamic>> getDashboard({int? planYear}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.geologyDashboard,
      queryParameters: {
        if (planYear != null) 'plan_year': planYear,
      },
    );
    return res.data ?? const {};
  }

  Future<Response<List<int>>> downloadReport({
    required int planYear,
    String format = 'xlsx',
  }) async {
    final options = binaryDownloadOptions();
    try {
      return await _dio.get<List<int>>(
        ApiConstants.geologyReportExport,
        queryParameters: {
          'plan_year': planYear,
          'format': format,
        },
        options: options,
      );
    } on DioException {
      if (format == 'pdf') rethrow;
      return _dio.get<List<int>>(
        ApiConstants.geologyDailyReportExport,
        queryParameters: {'plan_year': planYear},
        options: options,
      );
    }
  }

  Future<Map<String, dynamic>> getDailyReport(String reportDate) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.geologyDailyReport,
      queryParameters: {'report_date': reportDate},
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> saveDailyReport(
    Map<String, dynamic> body,
  ) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.geologyDailyReport,
      data: body,
    );
    return res.data ?? const {};
  }

  Future<Response<List<int>>> downloadOreTemplate({int? planYear}) {
    return _dio.get<List<int>>(
      ApiConstants.geologyDailyReportTemplate,
      queryParameters: {
        if (planYear != null) 'plan_year': planYear,
      },
      options: binaryDownloadOptions(),
    );
  }

  Future<Response<List<int>>> exportOreProduction(int planYear) {
    return _dio.get<List<int>>(
      ApiConstants.geologyDailyReportExport,
      queryParameters: {'plan_year': planYear},
      options: binaryDownloadOptions(),
    );
  }

  Future<Map<String, dynamic>> importOreProduction(
    MultipartFile file, {
    bool publish = true,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConstants.geologyDailyReportImport,
      data: FormData.fromMap({
        'file': file,
        'publish': publish ? 'true' : 'false',
      }),
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> getAdminRegistry() async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.geologyAdminRegistry,
    );
    return res.data ?? const {};
  }

  Future<Map<String, dynamic>> listAdminResource(
    String slug, {
    int page = 1,
    String? search,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConstants.geologyAdminResource(slug),
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
      ApiConstants.geologyAdminResource(slug),
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
      '${ApiConstants.geologyAdminResource(slug)}$pk/',
      data: body,
    );
    return res.data ?? const {};
  }

  Future<void> deleteAdminResource(String slug, String pk) async {
    await _dio.delete('${ApiConstants.geologyAdminResource(slug)}$pk/');
  }
}
