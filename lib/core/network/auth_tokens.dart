import 'package:dio/dio.dart';

/// Reads JWT access/refresh from a login/refresh payload or response headers.
/// Tokens are stored in FlutterSecureStorage and sent as Bearer — not cookies.
class AuthTokens {
  final String? access;
  final String? refresh;

  const AuthTokens({this.access, this.refresh});

  bool get hasAccess => access != null && access!.trim().isNotEmpty;

  AuthTokens merged(AuthTokens other) {
    return AuthTokens(
      access: _prefer(access, other.access),
      refresh: _prefer(refresh, other.refresh),
    );
  }

  static AuthTokens fromJson(dynamic data) {
    final map = _asMap(data);
    if (map == null) return const AuthTokens();

    var tokens = AuthTokens(
      access: _pick(map, _accessKeys),
      refresh: _pick(map, _refreshKeys),
    );
    for (final key in const ['tokens', 'data', 'result', 'payload']) {
      final nested = _asMap(map[key]);
      if (nested == null) continue;
      tokens = tokens.merged(
        AuthTokens(
          access: _pick(nested, _accessKeys),
          refresh: _pick(nested, _refreshKeys),
        ),
      );
    }
    return tokens;
  }

  static AuthTokens fromHeaders(Headers headers) {
    String? access = _bearer(headers.value('authorization'));
    access ??= headers.value('x-access-token');
    String? refresh = headers.value('x-refresh-token');

    final cookies = <String>[
      ...?headers.map['set-cookie'],
      ...?headers.map['Set-Cookie'],
    ];
    for (final raw in cookies) {
      final cookie = _parseCookie(raw);
      if (cookie == null) continue;
      final name = cookie.name.toLowerCase();
      final value = cookie.value;
      if (value.isEmpty) continue;
      if (_accessKeys.contains(name) ||
          (access == null && _looksLikeJwt(value))) {
        access ??= value;
      }
      if (_refreshKeys.contains(name)) {
        refresh ??= value;
      }
    }
    return AuthTokens(access: access, refresh: refresh);
  }

  static const _accessKeys = [
    'access',
    'access_token',
    'token',
    'jwt',
    'jwt_access',
  ];
  static const _refreshKeys = [
    'refresh',
    'refresh_token',
    'jwt_refresh',
  ];

  static String? _prefer(String? a, String? b) {
    if (a != null && a.trim().isNotEmpty) return a.trim();
    if (b != null && b.trim().isNotEmpty) return b.trim();
    return null;
  }

  static Map<String, dynamic>? _asMap(dynamic data) {
    if (data is Map<String, dynamic>) return data;
    if (data is Map) return Map<String, dynamic>.from(data);
    return null;
  }

  static String? _pick(Map<String, dynamic> map, List<String> keys) {
    for (final key in keys) {
      final value = map[key];
      if (value is String && value.trim().isNotEmpty) return value.trim();
    }
    return null;
  }

  static String? _bearer(String? raw) {
    if (raw == null) return null;
    final value = raw.trim();
    if (value.toLowerCase().startsWith('bearer ')) {
      return value.substring(7).trim();
    }
    if (value.toLowerCase().startsWith('jwt ')) {
      return value.substring(4).trim();
    }
    return _looksLikeJwt(value) ? value : null;
  }

  static bool _looksLikeJwt(String value) {
    final parts = value.split('.');
    return parts.length == 3 && parts.every((p) => p.isNotEmpty);
  }

  static ({String name, String value})? _parseCookie(String raw) {
    final first = raw.split(';').first;
    final eq = first.indexOf('=');
    if (eq <= 0) return null;
    return (
      name: first.substring(0, eq).trim(),
      value: first.substring(eq + 1).trim(),
    );
  }
}
