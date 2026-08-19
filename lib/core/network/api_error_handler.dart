// ignore_for_file: constant_identifier_names, non_constant_identifier_names

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'api_error_model.dart';

enum DataSource {
  NO_CONTENT,
  BAD_REQUEST,
  FORBIDDEN,
  UNAUTORISED,
  NOT_FOUND,
  INTERNAL_SERVER_ERROR,
  CONNECT_TIMEOUT,
  CANCEL,
  RECIEVE_TIMEOUT,
  SEND_TIMEOUT,
  CACHE_ERROR,
  NO_INTERNET_CONNECTION,
  API_LOGIC_ERROR,
  DEFAULT,
}

class ResponseCode {
  static const int SUCCESS = 200; // success with data
  static const int NO_CONTENT = 201; // success with no data (no content)
  static const int BAD_REQUEST = 400; // failure, API rejected request
  static const int UNAUTORISED = 401; // failure, user is not authorised
  static const int FORBIDDEN = 403; //  failure, API rejected request
  static const int INTERNAL_SERVER_ERROR = 500; // failure, crash in server side
  static const int NOT_FOUND = 404; // failure, not found
  static const int API_LOGIC_ERROR = 422; // API , lOGIC ERROR

  // local status code
  static const int CONNECT_TIMEOUT = -1;
  static const int CANCEL = -2;
  static const int RECIEVE_TIMEOUT = -3;
  static const int SEND_TIMEOUT = -4;
  static const int CACHE_ERROR = -5;
  static const int NO_INTERNET_CONNECTION = -6;
  static const int DEFAULT = -7;
}

class ResponseMessage {
  static const String NO_CONTENT = 'نجح الطلب، لكن لا توجد بيانات للعرض.';
  static const String BAD_REQUEST =
      'الطلب غير صحيح. تحقق من المدخلات وحاول مرة أخرى.';
  static const String UNAUTORISED =
      'غير مصرح. يرجى تسجيل الدخول أو تحديث بيانات الدخول.';
  static const String FORBIDDEN = 'غير مسموح بالوصول لهذا المورد.';
  static const String INTERNAL_SERVER_ERROR =
      'خطأ في الخادم. حاول مرة أخرى لاحقاً أو تواصل مع الدعم.';
  static const String NOT_FOUND = 'المورد غير موجود. تحقق من الرابط أو المعرف.';

  // local status code
  static const String CONNECT_TIMEOUT =
      'انتهت مهلة الاتصال بالخادم. تحقق من اتصالك وحاول مرة أخرى.';
  static const String CANCEL = 'تم إلغاء الطلب.';
  static const String RECIEVE_TIMEOUT = 'انتهت مهلة انتظار استجابة الخادم.';
  static const String SEND_TIMEOUT = 'انتهت مهلة إرسال البيانات إلى الخادم.';
  static const String CACHE_ERROR = 'فشل استرجاع البيانات من التخزين المؤقت.';
  static const String NO_INTERNET_CONNECTION =
      'لا يوجد اتصال بالإنترنت. تحقق من الشبكة وحاول مرة أخرى.';
  static const String WEB_CONNECTION_ERROR =
      'تعذر اتصال المتصفح بالخادم. تحقق من CORS على السيرفر أو شهادة HTTPS أو عنوان API.';
  static const String DEFAULT = 'حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.';
  static const String API_LOGIC_ERROR =
      'فشل التحقق من البيانات. تحقق من المدخلات وحاول مرة أخرى.';
}

extension DataSourceExtension on DataSource {
  ApiErrorModel getFailure() {
    switch (this) {
      case DataSource.NO_CONTENT:
        return ApiErrorModel(
          code: ResponseCode.NO_CONTENT,
          message: ResponseMessage.NO_CONTENT,
        );
      case DataSource.BAD_REQUEST:
        return ApiErrorModel(
          code: ResponseCode.BAD_REQUEST,
          message: ResponseMessage.BAD_REQUEST,
        );
      case DataSource.FORBIDDEN:
        return ApiErrorModel(
          code: ResponseCode.FORBIDDEN,
          message: ResponseMessage.FORBIDDEN,
        );
      case DataSource.UNAUTORISED:
        return ApiErrorModel(
          code: ResponseCode.UNAUTORISED,
          message: ResponseMessage.UNAUTORISED,
        );
      case DataSource.NOT_FOUND:
        return ApiErrorModel(
          code: ResponseCode.NOT_FOUND,
          message: ResponseMessage.NOT_FOUND,
        );
      case DataSource.INTERNAL_SERVER_ERROR:
        return ApiErrorModel(
          code: ResponseCode.INTERNAL_SERVER_ERROR,
          message: ResponseMessage.INTERNAL_SERVER_ERROR,
        );
      case DataSource.CONNECT_TIMEOUT:
        return ApiErrorModel(
          code: ResponseCode.CONNECT_TIMEOUT,
          message: ResponseMessage.CONNECT_TIMEOUT,
        );
      case DataSource.CANCEL:
        return ApiErrorModel(
          code: ResponseCode.CANCEL,
          message: ResponseMessage.CANCEL,
        );
      case DataSource.RECIEVE_TIMEOUT:
        return ApiErrorModel(
          code: ResponseCode.RECIEVE_TIMEOUT,
          message: ResponseMessage.RECIEVE_TIMEOUT,
        );
      case DataSource.SEND_TIMEOUT:
        return ApiErrorModel(
          code: ResponseCode.SEND_TIMEOUT,
          message: ResponseMessage.SEND_TIMEOUT,
        );
      case DataSource.CACHE_ERROR:
        return ApiErrorModel(
          code: ResponseCode.CACHE_ERROR,
          message: ResponseMessage.CACHE_ERROR,
        );
      case DataSource.NO_INTERNET_CONNECTION:
        return ApiErrorModel(
          code: ResponseCode.NO_INTERNET_CONNECTION,
          message: ResponseMessage.NO_INTERNET_CONNECTION,
        );
      case DataSource.API_LOGIC_ERROR:
        return ApiErrorModel(
          code: ResponseCode.API_LOGIC_ERROR,
          message: ResponseMessage.API_LOGIC_ERROR,
        );
      case DataSource.DEFAULT:
        return ApiErrorModel(
          code: ResponseCode.DEFAULT,
          message: ResponseMessage.DEFAULT,
        );
    }
  }
}

class ErrorHandler implements Exception {
  late ApiErrorModel apiErrorModel;

  ErrorHandler.handle(dynamic error) {
    if (error is DioException) {
      // dio error so its an error from response of the API or from dio itself
      apiErrorModel = _handleError(error);
    } else {
      apiErrorModel = DataSource.DEFAULT.getFailure();
    }
  }
}

ApiErrorModel _handleError(DioException error) {
  switch (error.type) {
    case DioExceptionType.connectionTimeout:
      return DataSource.CONNECT_TIMEOUT.getFailure();
    case DioExceptionType.sendTimeout:
      return DataSource.SEND_TIMEOUT.getFailure();
    case DioExceptionType.receiveTimeout:
      return DataSource.RECIEVE_TIMEOUT.getFailure();
    case DioExceptionType.badResponse:
      final response = error.response;
      final statusCode = response?.statusCode;
      if (statusCode != null && response != null) {
        switch (statusCode) {
          case ResponseCode.BAD_REQUEST:
            return _translateApiError(
              _parseResponseBody(response, DataSource.BAD_REQUEST),
              DataSource.BAD_REQUEST,
            );
          case ResponseCode.UNAUTORISED:
            return _translateApiError(
              _parseResponseBody(response, DataSource.UNAUTORISED),
              DataSource.UNAUTORISED,
            );
          case ResponseCode.FORBIDDEN:
            return _translateApiError(
              _parseResponseBody(response, DataSource.FORBIDDEN),
              DataSource.FORBIDDEN,
            );
          case ResponseCode.NOT_FOUND:
            return DataSource.NOT_FOUND.getFailure();
          case ResponseCode.INTERNAL_SERVER_ERROR:
            return DataSource.INTERNAL_SERVER_ERROR.getFailure();
          case ResponseCode.API_LOGIC_ERROR:
            return _translateApiError(
              _parseResponseBody(response, DataSource.API_LOGIC_ERROR),
              DataSource.API_LOGIC_ERROR,
            );
          default:
            return _translateApiError(
              _parseResponseBody(response, DataSource.DEFAULT),
              DataSource.DEFAULT,
            );
        }
      }
      return DataSource.DEFAULT.getFailure();
    case DioExceptionType.unknown:
      if (error.response?.statusCode != null && error.response != null) {
        return _translateApiError(
          _parseResponseBody(error.response!, DataSource.DEFAULT),
          DataSource.DEFAULT,
        );
      }
      return DataSource.DEFAULT.getFailure();
    case DioExceptionType.cancel:
      return DataSource.CANCEL.getFailure();
    case DioExceptionType.connectionError:
      if (kIsWeb) {
        return ApiErrorModel(
          code: ResponseCode.NO_INTERNET_CONNECTION,
          message: ResponseMessage.WEB_CONNECTION_ERROR,
        );
      }
      return DataSource.NO_INTERNET_CONNECTION.getFailure();
    case DioExceptionType.badCertificate:
      return DataSource.DEFAULT.getFailure();
  }
}

ApiErrorModel _parseResponseBody(
  Response<dynamic> response,
  DataSource fallback,
) {
  final data = response.data;
  if (data is Map<String, dynamic>) {
    try {
      return ApiErrorModel.fromJson(data);
    } catch (_) {
      return fallback.getFailure();
    }
  }
  if (data is Map) {
    try {
      return ApiErrorModel.fromJson(Map<String, dynamic>.from(data));
    } catch (_) {
      return fallback.getFailure();
    }
  }
  return fallback.getFailure();
}

ApiErrorModel _translateApiError(
  ApiErrorModel apiErrorModel,
  DataSource fallback,
) {
  final translatedMessage = _translateBackendMessage(
    apiErrorModel.message,
    fallback,
  );
  final message = translatedMessage ?? apiErrorModel.message;

  if (message != null && message.trim().isNotEmpty) {
    return ApiErrorModel(
      code: apiErrorModel.code ?? fallback.getFailure().code,
      message: message,
      data: apiErrorModel.data,
      errors: apiErrorModel.errors,
    );
  }

  if (apiErrorModel.errors != null && apiErrorModel.errors!.isNotEmpty) {
    final details = _formatBackendErrors(apiErrorModel.errors!);
    if (details.isNotEmpty) {
      return ApiErrorModel(
        code: apiErrorModel.code ?? fallback.getFailure().code,
        message: details,
        data: apiErrorModel.data,
        errors: apiErrorModel.errors,
      );
    }
  }

  return fallback.getFailure();
}

String? _translateBackendMessage(String? message, DataSource fallback) {
  if (message == null || message.trim().isEmpty) return null;

  final trimmed = message.trim();
  final normalized = trimmed.toLowerCase();
  final translations = <String, String>{
    'unauthenticated.': 'غير مصرح. يرجى تسجيل الدخول.',
    'unauthorized.': 'غير مصرح. يرجى تسجيل الدخول.',
    'forbidden.': 'غير مسموح بالوصول. ليس لديك صلاحية.',
    'not found.': 'المورد غير موجود. تحقق من الرابط أو المعرف.',
    'not found': 'المورد غير موجود. تحقق من الرابط أو المعرف.',
    'the given data was invalid.': 'البيانات غير صحيحة. تحقق من المدخلات.',
    'validation failed': 'فشل التحقق من البيانات. تحقق من المدخلات.',
    'internal server error': 'خطأ في الخادم. حاول مرة أخرى لاحقاً.',
    'service unavailable': 'الخدمة غير متاحة حالياً. حاول مرة أخرى لاحقاً.',
    'timeout': 'انتهت مهلة الاتصال بالخادم. حاول مرة أخرى.',
    'check your internet connection': 'تحقق من اتصال الإنترنت وحاول مرة أخرى.',
    'failed': 'فشل الطلب. حاول مرة أخرى.',
    'no active account found with the given credentials':
        'البريد الإلكتروني أو كلمة المرور غير صحيحة.',
    'unable to log in with provided credentials.':
        'البريد الإلكتروني أو كلمة المرور غير صحيحة.',
    'unable to log in with provided credentials':
        'البريد الإلكتروني أو كلمة المرور غير صحيحة.',
    'invalid credentials': 'بيانات الدخول غير صحيحة.',
    'user account is disabled.': 'تم تعطيل هذا الحساب.',
    'user account is disabled': 'تم تعطيل هذا الحساب.',
  };

  if (translations.containsKey(normalized)) {
    return translations[normalized]!;
  }

  // Keep server wording when it already carries a clear login/auth message.
  // Do NOT replace every 401 with a generic "غير مصرح".
  if ((fallback == DataSource.BAD_REQUEST ||
          fallback == DataSource.API_LOGIC_ERROR) &&
      normalized.contains('invalid') &&
      !normalized.contains('credential')) {
    return 'البيانات غير صحيحة. تحقق من المدخلات.';
  }

  return trimmed;
}

String _formatBackendErrors(Map<String, dynamic> errors) {
  final messages = <String>[];
  for (final entry in errors.entries) {
    final value = entry.value;
    if (value is List && value.isNotEmpty) {
      messages.add(value.first.toString());
    } else if (value != null) {
      messages.add(value.toString());
    }
  }
  return messages.join('\n');
}

class ApiInternalStatus {
  static const int SUCCESS = 0;
  static const int FAILURE = 1;
}
