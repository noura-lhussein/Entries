import 'package:dio/dio.dart';

import '../../../../core/network/api_constants.dart';
import '../models/builder_models.dart';

class BuilderRemoteDataSource {
  final Dio _dio;
  const BuilderRemoteDataSource(this._dio);

  Future<List<BuilderNamedItem>> getMainSections() async {
    final res = await _dio.get(ApiConstants.builderMainSections);
    return _mapNamedList(res.data);
  }

  Future<List<BuilderSubSection>> getSubSections({int? mainSectionId}) async {
    final res = await _dio.get(
      ApiConstants.builderSubSections,
      queryParameters: {
        'page_size': 1000,
        if (mainSectionId != null) 'main_section': mainSectionId,
      },
    );
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderSubSection.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderTitle>> getTitles() async {
    final res = await _dio.get(
      ApiConstants.builderTitles,
      queryParameters: {'page_size': 1000},
    );
    return sortBuilderTitles(
      _unwrapList(res.data)
          .whereType<Map>()
          .map((e) => BuilderTitle.fromJson(Map<String, dynamic>.from(e))),
    );
  }

  Future<UserBuilderPermissions> getPermissions() async {
    final res = await _dio.get(ApiConstants.builderPermissions);
    final data = res.data;
    if (data is Map<String, dynamic>) {
      return UserBuilderPermissions.fromJson(data);
    }
    if (data is Map) {
      return UserBuilderPermissions.fromJson(Map<String, dynamic>.from(data));
    }
    return const UserBuilderPermissions();
  }

  Future<FormSchemaPayload> getFormSchema(int titleId) async {
    final res = await _dio.get(
      ApiConstants.builderFormSchema,
      queryParameters: {'title_id': titleId},
    );
    final data = res.data;
    if (data is Map<String, dynamic>) return FormSchemaPayload.fromJson(data);
    if (data is Map) {
      return FormSchemaPayload.fromJson(Map<String, dynamic>.from(data));
    }
    throw StateError('invalid form schema');
  }

  Future<void> submitReport({
    required int titleId,
    required int subMainId,
    required List<Map<String, dynamic>> attributeValues,
  }) async {
    await _dio.post(
      ApiConstants.builderReportSubmit,
      data: {
        'title_id': titleId,
        'sub_main_id': subMainId,
        'attribute_values': attributeValues,
      },
    );
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
    );
    final data = res.data;
    if (data is Map<String, dynamic>) return DateCheckResult.fromJson(data);
    if (data is Map) {
      return DateCheckResult.fromJson(Map<String, dynamic>.from(data));
    }
    return const DateCheckResult(duplicate: false);
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
    );
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => InfoHistoryRow.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderSelectOption>> getEntityOptions(String entityType) async {
    final res = await _dio.get(
      ApiConstants.builderEntityOptions(entityType),
      queryParameters: {'limit': 500},
    );
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderSelectOption.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<List<BuilderSelectOption>> getGovernorates() async {
    final res = await _dio.get(ApiConstants.builderGovernorates);
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getDistricts(int governorateId) async {
    final res = await _dio.get(
      ApiConstants.builderDistricts,
      queryParameters: {'governorate': governorateId},
    );
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getSubdistricts(int districtId) async {
    final res = await _dio.get(
      ApiConstants.builderSubdistricts,
      queryParameters: {'district': districtId},
    );
    return _mapOptions(res.data);
  }

  Future<List<BuilderSelectOption>> getCommunities(int subdistrictId) async {
    final res = await _dio.get(
      ApiConstants.builderCommunities,
      queryParameters: {'subdistrict': subdistrictId},
    );
    return _mapOptions(res.data);
  }

  Future<String> uploadFormFile(MultipartFile file, {required String kind}) async {
    final res = await _dio.post(
      ApiConstants.builderFormFileUpload,
      data: FormData.fromMap({'file': file, 'kind': kind}),
    );
    final data = res.data;
    if (data is Map) {
      final url = data['url']?.toString();
      if (url != null && url.isNotEmpty) return url;
    }
    throw StateError('upload failed');
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
