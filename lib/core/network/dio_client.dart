import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'api_constants.dart';
import 'selective_dio_logger.dart';

class DioFactory {
  DioFactory._();

  static Dio? dio;

  static Future<Dio> getDio() async {
    // Water/oil dashboards on this host often exceed 12s; keep connect tighter.
    const connectTimeout = Duration(seconds: 20);
    const receiveTimeout = Duration(seconds: 60);
    const sendTimeout = Duration(seconds: 30);

    if (dio == null) {
      dio = Dio(
        BaseOptions(
          baseUrl: ApiConstants.apiBaseUrl,
          connectTimeout: connectTimeout,
          receiveTimeout: receiveTimeout,
          sendTimeout: sendTimeout,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods":
                "POST, GET, OPTIONS, PUT, DELETE, HEAD",
          },
        ),
      );

      if (!kReleaseMode) {
        addDioInterceptor();
      }
    }

    return dio!;
  }

  static void addDioInterceptor() {
    // Truncates bulky endpoints (lookups/geojson/…) so they don't flood console.
    dio?.interceptors.add(SelectiveDioLogger());
  }

  static void updateHeaderWithToken(String? accessToken) {
    if (dio == null) return;
    if (accessToken == null || accessToken.isEmpty) {
      clearToken();
      return;
    }
    dio!.options.headers['Authorization'] = 'Bearer $accessToken';
  }

  static void clearToken() {
    dio?.options.headers.remove('Authorization');
  }

  static void updateHeaderWithLang(String? lang) {
    if (dio != null && lang != null) {
      dio!.options.headers['lang'] = lang;
    }
  }
}
