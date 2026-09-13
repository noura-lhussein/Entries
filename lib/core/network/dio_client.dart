import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:flutter/foundation.dart';

import 'api_constants.dart';
import 'cookie_session.dart';
import 'csrf_interceptor.dart';
import 'jwt_util.dart';
import 'selective_dio_logger.dart';

class DioFactory {
  DioFactory._();

  static Dio? dio;
  static Dio? reportDio;
  static CookieJar? cookieJar;

  static const _connectTimeout = Duration(seconds: 20);
  static const _receiveTimeout = Duration(seconds: 60);
  static const _sendTimeout = Duration(seconds: 30);

  static Future<CookieJar> _ensureCookieJar() async {
    cookieJar ??= await CookieSession.createJar();
    return cookieJar!;
  }

  static Future<Dio> getDio() async {
    if (dio != null) return dio!;
    await _ensureCookieJar();
    dio = _create(ApiConstants.apiBaseUrl);
    return dio!;
  }

  /// Dio for report_moe builder APIs. Same instance as [getDio] when origins match.
  static Future<Dio> getReportDio() async {
    if (!ApiConstants.usesSeparateReportApi) {
      return getDio();
    }
    if (reportDio != null) return reportDio!;
    await _ensureCookieJar();
    reportDio = _create(ApiConstants.reportApiBaseUrl);
    return reportDio!;
  }

  static Dio _create(String baseUrl) {
    final jar = cookieJar!;
    final client = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: _connectTimeout,
        receiveTimeout: _receiveTimeout,
        sendTimeout: _sendTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );
    client.interceptors.add(CookieManager(jar));
    client.interceptors.add(CsrfInterceptor(jar));
    if (!kReleaseMode) {
      client.interceptors.add(SelectiveDioLogger());
    }
    return client;
  }

  /// Attach Bearer only for a real JWT. Empty/stale `Authorization` makes
  /// Django REST skip session cookies and return 401.
  static void updateHeaderWithToken(String? accessToken) {
    final token = accessToken?.trim() ?? '';
    if (token.isEmpty ||
        !JwtUtil.looksLikeJwt(token) ||
        JwtUtil.isExpired(token)) {
      clearToken();
      return;
    }
    for (final client in [dio, reportDio]) {
      if (client == null) continue;
      client.options.headers['Authorization'] = 'Bearer $token';
    }
  }

  static void clearToken() {
    for (final client in [dio, reportDio]) {
      client?.options.headers.remove('Authorization');
    }
  }

  static void updateHeaderWithLang(String? lang) {
    if (lang == null) return;
    for (final client in [dio, reportDio]) {
      client?.options.headers['lang'] = lang;
    }
  }
}
