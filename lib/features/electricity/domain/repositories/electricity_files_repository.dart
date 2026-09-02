import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';

abstract class ElectricityFilesRepository {
  Future<ApiResult<Response<List<int>>>> downloadReportTemplate({String? date});

  Future<ApiResult<Map<String, dynamic>>> importDailyReport(
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
