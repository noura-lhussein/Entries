import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';

abstract class GeologyFilesRepository {
  Future<ApiResult<Response<List<int>>>> downloadReport({
    required int planYear,
    String format = 'xlsx',
  });

  Future<ApiResult<Response<List<int>>>> downloadOreTemplate({int? planYear});

  Future<ApiResult<Response<List<int>>>> exportOreProduction(int planYear);

  Future<ApiResult<Map<String, dynamic>>> importOreProduction(
    MultipartFile file, {
    bool publish = true,
  });
}
