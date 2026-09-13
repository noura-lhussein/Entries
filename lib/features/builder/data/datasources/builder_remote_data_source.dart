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

  Future<List<BuilderSubSection>> getSubSectionTree(int mainSectionId) async {
    final res = await _dio.get(
      ApiConstants.builderSubSectionTree,
      queryParameters: {'main_section': mainSectionId},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    final raw = res.data;
    final roots = raw is List ? raw : _unwrapList(raw);
    final out = <BuilderSubSection>[];
    void walk(Map node, int? parentId) {
      final children = node['children'];
      final childMaps = children is List
          ? children.whereType<Map>().toList()
          : const <Map>[];
      final flat = Map<String, dynamic>.from(node)
        ..remove('children')
        ..['parent'] = node['parent'] ?? parentId
        ..['children_count'] = childMaps.length
        ..['is_leaf'] = node['is_leaf'] ?? childMaps.isEmpty
        ..['main_section'] = node['main_section'] ?? mainSectionId;
      out.add(BuilderSubSection.fromJson(flat));
      final id = flat['id'];
      for (final child in childMaps) {
        walk(child, id is int ? id : int.tryParse('$id'));
      }
    }

    for (final node in roots.whereType<Map>()) {
      walk(node, null);
    }
    return out;
  }

  Future<List<BuilderNamedItem>> getUsers({int pageSize = 100}) async {
    final res = await _dio.get(
      ApiConstants.users,
      queryParameters: {'page_size': pageSize, 'limit': pageSize},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderNamedItem.fromUserJson(Map<String, dynamic>.from(e)))
        .where((e) => e.id > 0)
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

  Future<List<BuilderAttribute>> getAttributes() async {
    final res = await _dio.get(
      ApiConstants.builderAttributes,
      queryParameters: {'page_size': 1000},
      options: _soft(),
    );
    if (_missing(res)) return const [];
    return _unwrapList(res.data)
        .whereType<Map>()
        .map((e) => BuilderAttribute.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<InfoCellDetail> getInfoDetail(int id) async {
    final res = await _dio.get(
      ApiConstants.builderInfoDetail(id),
      options: _soft(),
    );
    if (_missing(res) || res.data is! Map) {
      throw StateError('تعذر تحميل الحقل');
    }
    return InfoCellDetail.fromJson(Map<String, dynamic>.from(res.data as Map));
  }

  Future<void> patchInfoValue(int id, String value) async {
    final res = await _dio.patch(
      ApiConstants.builderInfoById(id),
      data: {'value': value},
      options: _soft(),
    );
    if (_missing(res) || (res.statusCode ?? 500) >= 400) {
      throw StateError('تعذر حفظ الحقل');
    }
  }

  Future<void> createInfoValue({
    required int attributeId,
    required int subMainId,
    required String value,
    String? rowKey,
  }) async {
    final res = await _dio.post(
      ApiConstants.builderInfos,
      data: {
        'attribute': attributeId,
        'sub_main': subMainId,
        'value': value,
        if (rowKey != null && rowKey.trim().isNotEmpty) 'row_key': rowKey,
      },
      options: _soft(),
    );
    if (_missing(res) || (res.statusCode ?? 500) >= 400) {
      throw StateError('تعذر حفظ الحقل');
    }
  }

  Future<void> deleteInfoRow({String? rowKey, int? infoId}) async {
    if (rowKey != null && rowKey.trim().isNotEmpty) {
      final res = await _dio.post(
        ApiConstants.builderInfoDeleteRow,
        data: {'row_key': rowKey},
        options: _soft(),
      );
      if (_missing(res) || (res.statusCode ?? 500) >= 400) {
        throw StateError('تعذر حذف السجل');
      }
      return;
    }
    if (infoId == null) throw StateError('تعذر حذف السجل');
    final res = await _dio.delete(
      ApiConstants.builderInfoById(infoId),
      options: _soft(),
    );
    if (_missing(res) || (res.statusCode ?? 500) >= 400) {
      throw StateError('تعذر حذف السجل');
    }
  }

  Future<void> confirmInfoIds({
    required List<int> ids,
    required String status,
    String? note,
  }) async {
    if (ids.isEmpty) return;
    final res = await _dio.post(
      ApiConstants.builderInfoConfirmIds,
      data: {
        'ids': ids,
        'status': status,
        if (note != null) 'note': note,
      },
      options: _soft(),
    );
    if (_missing(res) || (res.statusCode ?? 500) >= 400) {
      throw StateError('تعذر تحديث التأكيد');
    }
  }

  Future<void> commitInfoNoteIds({
    required List<int> ids,
    required String note,
  }) async {
    if (ids.isEmpty) return;
    final res = await _dio.post(
      ApiConstants.builderInfoCommitNoteIds,
      data: {'ids': ids, 'note': note},
      options: _soft(),
    );
    if (_missing(res) || (res.statusCode ?? 500) >= 400) {
      throw StateError('تعذر حفظ الملاحظة');
    }
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
    int? titleCategoryId,
    int? attributeId,
    String? confirmed,
    String? search,
    String? from,
    String? to,
  }) async {
    final res = await _dio.get(
      ApiConstants.builderInfoRowCount,
      queryParameters: _infoQuery(
        titleId: titleId,
        mainSectionId: mainSectionId,
        subMainId: subMainId,
        userId: userId,
        titleCategoryId: titleCategoryId,
        attributeId: attributeId,
        confirmed: confirmed,
        search: search,
        from: from,
        to: to,
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
    int pageSize = 10,
    int? titleId,
    int? mainSectionId,
    int? subMainId,
    int? userId,
    int? titleCategoryId,
    int? attributeId,
    String? confirmed,
    String? search,
    String? from,
    String? to,
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
          titleCategoryId: titleCategoryId,
          attributeId: attributeId,
          confirmed: confirmed,
          search: search,
          from: from,
          to: to,
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
    int? titleCategoryId,
    int? attributeId,
    String? confirmed,
    String? search,
    String? from,
    String? to,
  }) {
    return {
      if (titleId != null) 'title_id': titleId,
      if (mainSectionId != null) 'main_section_id': mainSectionId,
      if (subMainId != null) 'sub_main_id': subMainId,
      if (userId != null) 'user': userId,
      if (titleCategoryId != null) 'title_category_id': titleCategoryId,
      if (attributeId != null) 'attribute_id': attributeId,
      if (confirmed != null && confirmed.isNotEmpty) 'confirmed': confirmed,
      if (search != null && search.trim().isNotEmpty) 'search': search.trim(),
      if (from != null && from.isNotEmpty) 'from': from,
      if (to != null && to.isNotEmpty) 'to': to,
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
