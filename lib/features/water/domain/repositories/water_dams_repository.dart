import 'package:dio/dio.dart';

import '../../../../core/network/api_result.dart';
import '../entities/water_import_result_entity.dart';

abstract class WaterDamsRepository {
  Future<ApiResult<WaterImportResultEntity>> saveDamDaily({
    required DateTime readingDate,
    required int? damId,
    required double? storageMcm,
    required String notes,
  });

  Future<ApiResult<WaterImportResultEntity>> importDams({
    required List<MultipartFile> files,
    required bool clear,
  });

  Future<ApiResult<WaterImportResultEntity>> clearDamStorage();
}
