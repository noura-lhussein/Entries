import 'dart:async';

import 'package:dio/dio.dart';

import '../../features/auth/data/datasources/auth_secure_storage.dart';
import 'api_constants.dart';
import 'dio_client.dart';
import 'jwt_util.dart';

/// Single-flight access-token refresh (matches portal `refreshInFlight`).
class TokenRefresher {
  final AuthSecureStorage secureStorage;

  TokenRefresher(this.secureStorage);

  Future<String?>? _inFlight;

  /// Called after tokens are cleared due to an auth failure (not network).
  void Function()? onSessionInvalidated;

  var _invalidating = false;

  /// Returns a valid access token, refreshing when missing/expired.
  /// On auth failure, clears the session and invokes [onSessionInvalidated].
  Future<String?> ensureAccessToken({bool forceRefresh = false}) async {
    if (!forceRefresh) {
      final access = await secureStorage.getAccessToken();
      if (access != null &&
          access.isNotEmpty &&
          !JwtUtil.isExpired(access)) {
        return access;
      }
    }

    return refresh();
  }

  /// Shared refresh; concurrent callers await the same future.
  Future<String?> refresh() {
    return _inFlight ??= _doRefresh().whenComplete(() => _inFlight = null);
  }

  Future<String?> _doRefresh() async {
    final usedRefresh = await secureStorage.getRefreshToken();
    if (usedRefresh == null || usedRefresh.isEmpty) {
      final access = await secureStorage.getAccessToken();
      // Only treat as logged-out when we had a session that can no longer renew.
      if (access != null && access.isNotEmpty) {
        await _invalidateSession();
      }
      return null;
    }

    try {
      return await _requestRefresh(usedRefresh);
    } on DioException catch (e) {
      // Another request may have rotated refresh while we were in flight.
      final latest = await secureStorage.getRefreshToken();
      if (latest != null && latest.isNotEmpty && latest != usedRefresh) {
        try {
          return await _requestRefresh(latest);
        } on DioException catch (retryErr) {
          if (_isAuthFailure(retryErr)) {
            await _invalidateSession();
          }
          return null;
        } catch (_) {
          return null;
        }
      }

      // Prefer HTTP auth status over Dio type (e.g. unknown + 401 body).
      if (_isAuthFailure(e)) {
        await _invalidateSession();
      }
      // Network / transient: keep tokens so the session can retry later.
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<void> _invalidateSession() async {
    if (_invalidating) return;
    _invalidating = true;
    try {
      await secureStorage.clearAll();
      DioFactory.clearToken();
      onSessionInvalidated?.call();
    } finally {
      _invalidating = false;
    }
  }

  Future<String> _requestRefresh(String refreshToken) async {
    final refreshDio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 20),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    final response = await refreshDio.post<Map<String, dynamic>>(
      ApiConstants.refresh,
      data: {'refresh': refreshToken},
    );

    final data = response.data;
    final newAccess = data?['access']?.toString();
    final newRefresh = data?['refresh']?.toString();

    if (newAccess == null || newAccess.isEmpty) {
      throw StateError('Refresh response missing access token');
    }

    await secureStorage.saveAccessToken(newAccess);
    if (newRefresh != null && newRefresh.isNotEmpty) {
      await secureStorage.saveRefreshToken(newRefresh);
    }
    DioFactory.updateHeaderWithToken(newAccess);
    return newAccess;
  }

  static bool _isAuthFailure(DioException e) {
    final code = e.response?.statusCode;
    return code == 401 || code == 403;
  }
}
