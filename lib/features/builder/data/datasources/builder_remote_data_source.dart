import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../models/builder_models.dart';

/// Treat 404 as a normal response so Dio does not throw (debugger / ANR).
Options _soft([Options? extra]) {
  final base = extra ?? Options();
  return base.copyWith(
    validateStatus: (status) {
      if (status == null) return false;
      if (status == 404) return true;
      return status >= 200 && status < 400;
    },
  );
}

bool _missing(Response res) => res.statusCode == 404;

class BuilderRemoteDataSource {
  final Dio _dio;
  const BuilderRemoteDataSource(this._dio);

  Future<List<BuilderNamedItem>> getMainSections() async {
    final res = await _dio.get(
      ApiConstants.builderMainSections,
      queryParameters: {'page_size': 1000},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapNamedList(res.data);
  }

  Future<List<BuilderSubSection>> getSubSections({int? mainSectionId}) async {
    final res = await _dio.get(
      ApiConstants.builderSubSections,
      queryParameters: {
        'page_size': 1000,
        if (mainSectionId != null) 'main_section': mainSectionId,
      },
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderSubSection.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderTitle>> getTitles() async {
    final res = await _dio.get(
      ApiConstants.builderTitles,
      queryParameters: {'page_size': 1000},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return sortBuilderTitles(
      _unwrapList(res.data)
          .whereType<Map>()
          .map((e) => BuilderTitle.fromJson(Map<String, dynamic>.from(e))),
    );
  }

  Future<UserBuilderPermissions> getPermissions() async {
    final res = await _dio.get(
      ApiConstants.builderPermissions,
      options: _soft(),
    );
    if (_missing(res)) return const UserBuilderPermissions();
    final data = res.data;
    if (data is Map<String, dynamic>) {
      return UserBuilderPermissions.fromJson(data);
    }
    if (data is Map) {
      return UserBuilderPermissions.fromJson(Map<String, dynamic>.from(data));
    }
    return const UserBuilderPermissions();
  }

  Future<FormSchemaPayload?> getFormSchema(int titleId) async {
    final res = await _dio.get(
      ApiConstants.builderFormSchema,
      queryParameters: {'title_id': titleId},
      options: _soft(),
    );
    if (_missing(res)) return null;
    final data = res.data;
    if (data is Map<String, dynamic>) return FormSchemaPayload.fromJson(data);
    if (data is Map) {
      return FormSchemaPayload.fromJson(Map<String, dynamic>.from(data));
    }
    return null;
  }

  Future<bool> submitReport({
    required int titleId,
    required int subMainId,
    required List<Map<String, dynamic>> attributeValues,
  }) async {
    final res = await _dio.post(
      ApiConstants.builderReportSubmit,
      data: {
        'title_id': titleId,
        'sub_main_id': subMainId,
        'attribute_values': attributeValues,
      },
      options: _soft(),
    );
    final code = res.statusCode ?? 0;
    return code >= 200 && code < 300;
  }

  Future<DateCheckResult> checkReportDate({
    required int titleId,
    required int subMainId,
    required String date,
    String? entityType,
    int? entityId,
  }) async {
    final res = await _dio.get(
      ApiConstants.builderCheckDate,
      queryParameters: {
        'title_id': titleId,
        'sub_main_id': subMainId,
        'date': date,
        if (entityType != null) 'entity_type': entityType,
        if (entityId != null) 'entity_id': entityId,
      },
      options: _soft(),
    );
    if (_missing(res)) return const DateCheckResult(duplicate: false);
    final data = res.data;
    if (data is Map<String, dynamic>) return DateCheckResult.fromJson(data);
    if (data is Map) {
      return DateCheckResult.fromJson(Map<String, dynamic>.from(data));
    }
    return const DateCheckResult(duplicate: false);
  }

  Future<List<BuilderNamedItem>> getTitleCategories() async {
    final res = await _dio.get(
      ApiConstants.builderTitleCategories,
      queryParameters: {'page_size': 1000},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapNamedList(res.data);
  }

  Future<int> getInfoRowCount({
    int? titleId,
    int? mainSectionId,
    int? subMainId,
    int? userId,
    String? confirmed,
    String? search,
  }) async {
    final res = await _dio.get(
      ApiConstants.builderInfoRowCount,
      queryParameters: _infoQuery(
        titleId: titleId,
        mainSectionId: mainSectionId,
        subMainId: subMainId,
        userId: userId,
        confirmed: confirmed,
        search: search,
      ),
      options: _soft(),
    );
    if (_missing(res)) return 0;
    final data = res.data;
    if (data is Map) {
      final n = data['count'];
      if (n is num) return n.toInt();
      return int.tryParse(n?.toString() ?? '') ?? 0;
    }
    return 0;
  }

  Future<PaginatedInfoRecords> queryInfoRows({
    int page = 1,
    int pageSize = 20,
    int? titleId,
    int? mainSectionId,
    int? subMainId,
    int? userId,
    String? confirmed,
    String? search,
  }) async {
    final res = await _dio.get(
      ApiConstants.builderInfoRows,
      queryParameters: {
        'page': page,
        'page_size': pageSize,
        ..._infoQuery(
          titleId: titleId,
          mainSectionId: mainSectionId,
          subMainId: subMainId,
          userId: userId,
          confirmed: confirmed,
          search: search,
        ),
      },
      options: _soft(),
    );
    if (_missing(res)) return const PaginatedInfoRecords();
    final list = _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => InfoRecord.fromJson(Map<String, dynamic>.from(e)))
        .toList();
    var count = list.length;
    final data = res.data;
    if (data is Map) {
      final n = data['count'];
      if (n is num) count = n.toInt();
      else count = int.tryParse(n?.toString() ?? '') ?? count;
    }
    return PaginatedInfoRecords(count: count, results: list);
  }

  Map<String, dynamic> _infoQuery({
    int? titleId,
    int? mainSectionId,
    int? subMainId,
    int? userId,
    String? confirmed,
    String? search,
  }) {
    return {
      if (titleId != null) 'title_id': titleId,
      if (mainSectionId != null) 'main_section_id': mainSectionId,
      if (subMainId != null) 'sub_main_id': subMainId,
      if (userId != null) 'user': userId,
      if (confirmed != null && confirmed.isNotEmpty) 'confirmed': confirmed,
      if (search != null && search.trim().isNotEmpty) 'search': search.trim(),
    };
  }

  Future<List<InfoHistoryRow>> getInfoRows({
    required int titleId,
    required int subMainId,
    int pageSize = 5,
  }) async {
    final res = await _dio.get(
      ApiConstants.builderInfoRows,
      queryParameters: {
        'title_id': titleId,
        'sub_main_id': subMainId,
        'page_size': pageSize,
        'page': 1,
      },
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => InfoHistoryRow.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderSelectOption>> getEntityOptions(String entityType) async {
    final res = await _dio.get(
      ApiConstants.builderEntityOptions(entityType),
      queryParameters: {'limit': 500},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderSelectOption.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderSelectOption>> getGovernorates() async {
    final res = await _dio.get(
      ApiConstants.builderGovernorates,
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getDistricts(int governorateId) async {
    final res = await _dio.get(
      ApiConstants.builderDistricts,
      queryParameters: {'governorate': governorateId},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getSubdistricts(int districtId) async {
    final res = await _dio.get(
      ApiConstants.builderSubdistricts,
      queryParameters: {'district': districtId},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getCommunities(int subdistrictId) async {
    final res = await _dio.get(
      ApiConstants.builderCommunities,
      queryParameters: {'subdistrict': subdistrictId},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _mapOptions(res.data);
  }

  Future<String> uploadFormFile(MultipartFile file, {required String kind}) async {
    final res = await _dio.post(
      ApiConstants.builderFormFileUpload,
      data: FormData.fromMap({'file': file, 'kind': kind}),
      options: _soft(),
    );
    if (_missing(res)) throw StateError('upload failed');
    final data = res.data;
    if (data is Map) {
      final url = data['url']?.toString();
      if (url != null && url.isNotEmpty) return url;
    }
    throw StateError('upload failed');
  }

  Future<Response<List<int>>> downloadExcelTemplate({
    required int titleId,
    int? subMainId,
  }) {
    return _dio.get<List<int>>(
      ApiConstants.builderExcelTemplate(titleId),
      queryParameters: {
        if (subMainId != null) 'sub_main_id': subMainId,
      },
      options: _soft(binaryDownloadOptions()),
    );
  }

  Future<ExcelImportResult> importExcel({
    required int titleId,
    required MultipartFile file,
    required int subMainId,
    bool dryRun = false,
  }) async {
    final res = await _dio.post(
      ApiConstants.builderExcelImport(titleId),
      queryParameters: {
        'sub_main_id': subMainId,
        if (dryRun) 'dry_run': 'true',
      },
      data: FormData.fromMap({
        'file': file,
        'sub_main_id': subMainId,
      }),
      options: _soft(),
    );
    if (_missing(res)) return const ExcelImportResult();
    final data = res.data;
    if (data is Map<String, dynamic>) return ExcelImportResult.fromJson(data);
    if (data is Map) {
      return ExcelImportResult.fromJson(Map<String, dynamic>.from(data));
    }
    return const ExcelImportResult();
  }

  List<BuilderNamedItem> _mapNamedList(dynamic data) => _unwrapList(data)
      .whereType<Map>()
      .map((e) => BuilderNamedItem.fromJson(Map<String, dynamic>.from(e)))
      .toList();

  List<BuilderSelectOption> _mapOptions(dynamic data) => _unwrapList(data)
      .whereType<Map>()
      .map((e) => BuilderSelectOption.fromJson(Map<String, dynamic>.from(e)))
      .toList();

  List<dynamic> _unwrapList(dynamic data) {
    if (data is List) return data;
    if (data is Map) {
      final results = data['results'] ?? data['items'] ?? data['data'];
      if (results is List) return results;
    }
    return const [];
  }
}
