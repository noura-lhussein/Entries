import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';

import 'api_constants.dart';

/// Sends Django CSRF token on mutating requests, matching report_moe cookies.
class CsrfInterceptor extends Interceptor {
  CsrfInterceptor(this.cookieJar);

  final CookieJar cookieJar;

  static const _unsafe = {'POST', 'PUT', 'PATCH', 'DELETE'};

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) {
    if (!_unsafe.contains(options.method.toUpperCase())) {
      handler.next(options);
      return;
    }

    cookieJar.loadForRequest(options.uri).then((cookies) {
      String? token;
      for (final cookie in cookies) {
        final name = cookie.name.toLowerCase();
        if (name == 'csrftoken' || name == 'csrf' || name == 'csrf-token') {
          token = cookie.value;
          break;
        }
      }
      if (token != null && token.isNotEmpty) {
        options.headers['X-CSRFToken'] = token;
      }
      options.headers.putIfAbsent('Referer', () => ApiConstants.url);
      handler.next(options);
    }).catchError((Object e, StackTrace st) {
      handler.reject(
        DioException(requestOptions: options, error: e, stackTrace: st),
      );
    });
  }
}
