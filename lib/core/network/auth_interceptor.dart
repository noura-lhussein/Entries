import 'package:dio/dio.dart';

import 'api_constants.dart';
import 'token_refresher.dart';

class AuthInterceptor extends Interceptor {
  final TokenRefresher tokenRefresher;
  final Dio dio;

  AuthInterceptor(this.tokenRefresher, this.dio);

  static const _retriedKey = 'auth_retried';

  bool _isAuthEndpoint(String path) {
    return path.contains(ApiConstants.login) ||
        path.contains(ApiConstants.refresh);
  }

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) {
    if (_isAuthEndpoint(options.path)) {
      handler.next(options);
      return;
    }

    tokenRefresher.ensureAccessToken().then((token) {
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      handler.next(options);
    }).catchError((Object e, StackTrace st) {
      handler.reject(
        DioException(
          requestOptions: options,
          error: e,
          stackTrace: st,
        ),
      );
    });
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final alreadyRetried = err.requestOptions.extra[_retriedKey] == true;
    if (err.response?.statusCode != 401 ||
        alreadyRetried ||
        _isAuthEndpoint(err.requestOptions.path)) {
      handler.next(err);
      return;
    }

    // Force refresh then retry once. Session invalidation (→ login) is handled
    // by TokenRefresher when refresh is rejected with 401/403.
    tokenRefresher.ensureAccessToken(forceRefresh: true).then((token) async {
      if (token == null || token.isEmpty) {
        handler.next(err);
        return;
      }

      final options = err.requestOptions;
      options.headers['Authorization'] = 'Bearer $token';
      options.extra[_retriedKey] = true;
      try {
        final retryResponse = await dio.fetch(options);
        handler.resolve(retryResponse);
      } catch (e) {
        if (e is DioException) {
          handler.next(e);
        } else {
          handler.next(err);
        }
      }
    }).catchError((Object _) {
      handler.next(err);
    });
  }
}
