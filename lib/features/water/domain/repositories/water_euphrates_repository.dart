import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';

abstract class WaterEuphratesRepository {
  Future<ApiResult<Map<String, dynamic>?>> getEuphratesDaily(DateTime date);

  Future<ApiResult<WaterImportResultEntity>> saveEuphratesDaily({
    required Map<String, dynamic> payload,
  });

  Future<ApiResult<WaterImportResultEntity>> importEuphrates({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> clearEuphrates();
}
