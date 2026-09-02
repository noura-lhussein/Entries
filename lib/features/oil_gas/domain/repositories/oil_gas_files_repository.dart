import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';

abstract class OilGasFilesRepository {
  Future<ApiResult<Response<List<int>>>> downloadExecutiveTemplate({
    String? date,
  });

  Future<ApiResult<Map<String, dynamic>>> importExecutiveReport(
    MultipartFile file, {
    bool publish = true,
  });

  Future<ApiResult<Response<List<int>>>> exportReport({
    String? date,
    String? month,
    String period = 'day',
    String format = 'xlsx',
  });
}
