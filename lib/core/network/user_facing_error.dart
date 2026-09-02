import 'package:dio/dio.dart';

import 'api_error_handler.dart';

/// Human-readable Arabic message for network / API failures.
String userFacingErrorMessage(Object? error, {String? fallback}) {
  if (error == null) {
    return fallback ?? ResponseMessage.DEFAULT;
  }
  if (error is ErrorHandler) {
    return error.apiErrorModel.message ?? fallback ?? ResponseMessage.DEFAULT;
  }
  if (error is DioException) {
    if (error.response?.statusCode == 404) {
      return 'خدمة الإدخال غير متاحة على السيرفر حالياً.';
    }
    return ErrorHandler.handle(error).apiErrorModel.message ??
        fallback ??
        ResponseMessage.DEFAULT;
  }
  final text = error.toString().trim();
  if (text.isEmpty || text == 'Exception' || text.startsWith('Exception:')) {
    return fallback ?? ResponseMessage.DEFAULT;
  }
  // Avoid dumping raw Exception(...) to the UI.
  if (text.startsWith('DioException') || text.contains('SocketException')) {
    return ErrorHandler.handle(
          error is Exception ? error : Exception(text),
        ).apiErrorModel.message ??
        fallback ??
        ResponseMessage.DEFAULT;
  }
  return fallback ?? ResponseMessage.DEFAULT;
}
