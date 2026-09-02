import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';

abstract class WaterFilesRepository {
  Future<ApiResult<Map<String, dynamic>>> getImportStatus();

  Future<ApiResult<Response<List<int>>>> downloadTemplate(String kind);

  Future<ApiResult<Response<List<int>>>> exportDrinkingWaterSurvey();
}
