import 'package:equatable/equatable.dart';

import '../../../../core/network/api_result.dart';
import '../../domain/entities/water_import_result_entity.dart';

class WaterFeedback extends Equatable {
  WaterFeedback({
    required this.message,
    required this.isSuccess,
  }) : id = DateTime.now().microsecondsSinceEpoch;

  final int id;
  final String message;
  final bool isSuccess;

  @override
  List<Object?> get props => [id, message, isSuccess];
}

WaterFeedback feedbackFromImportResult(
  ApiResult<WaterImportResultEntity> result, {
  required String successFallback,
  required String failureFallback,
}) {
  return result.when(
    success: (r) => WaterFeedback(
      message: r.resolveMessage(
        successFallback: successFallback,
        failureFallback: failureFallback,
      ),
      isSuccess: r.ok,
    ),
    failure: (e) => WaterFeedback(
      message: e.apiErrorModel.message ?? failureFallback,
      isSuccess: false,
    ),
  );
}

WaterFeedback feedbackFromClearResult(
  ApiResult<WaterImportResultEntity> result,
) {
  return result.when(
    success: (r) => WaterFeedback(
      message: r.messageAr ?? (r.ok ? 'تم المسح' : 'فشل المسح'),
      isSuccess: r.ok,
    ),
    failure: (_) => WaterFeedback(message: 'فشل المسح', isSuccess: false),
  );
}
