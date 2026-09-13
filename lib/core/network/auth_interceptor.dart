import 'package:dio/dio.dart';

import 'api_constants.dart';
import 'dio_client.dart';
import 'jwt_util.dart';
import 'token_refresher.dart';

class AuthInterceptor extends Interceptor {
  final TokenRefresher tokenRefresher;
  final Dio dio;

  AuthInterceptor(this.tokenRefresher, this.dio);

  static const _retriedKey = 'auth_retried';

  bool _isAuthEndpoint(String path) {
    return path.contains(ApiConstants.login) ||
        path.contains(ApiConstants.refresh) ||
        path.contains(ApiConstants.csrf);
  }

  bool _isUsableJwt(String? token) {
    return token != null &&
        token.isNotEmpty &&
        JwtUtil.looksLikeJwt(token) &&
        !JwtUtil.isExpired(token);
  }

  void _stripBearer(RequestOptions options) {
    options.headers.remove('Authorization');
    options.headers.remove('authorization');
  }

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) {
    if (_isAuthEndpoint(options.path)) {
      _stripBearer(options);
      handler.next(options);
      return;
    }

    tokenRefresher.ensureAccessToken().then((token) {
      if (_isUsableJwt(token)) {
        options.headers['Authorization'] = 'Bearer $token';
      } else {
        // Empty/stale Bearer makes DRF JWT reject the request before cookies.
        _stripBearer(options);
        DioFactory.clearToken();
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

    tokenRefresher.ensureAccessToken(forceRefresh: true).then((token) async {
      if (!_isUsableJwt(token)) {
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
