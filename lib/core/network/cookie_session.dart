import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

import 'api_constants.dart';

/// Persists Django session cookies (`sessionid`, `csrftoken`) across launches.
class CookieSession {
  CookieSession(this.jar);

  final CookieJar jar;

  static Future<CookieJar> createJar() async {
    try {
      final dir = await getApplicationSupportDirectory();
      return PersistCookieJar(
        persistSession: true,
        ignoreExpires: true,
        storage: FileStorage('${dir.path}/http_cookies'),
      );
    } catch (_) {
      return CookieJar();
    }
  }

  /// Save Set-Cookie from a login (or other) response so later API calls
  /// send `Cookie` on this device. JWT is still preferred when present.
  Future<void> saveFromResponse(Response response) async {
    final raw = <String>[
      ...?response.headers.map['set-cookie'],
      ...?response.headers.map['Set-Cookie'],
    ];
    if (raw.isEmpty) return;

    final cookies = <Cookie>[];
    for (final line in raw) {
      try {
        cookies.add(Cookie.fromSetCookieValue(line));
      } catch (_) {}
    }
    if (cookies.isEmpty) return;

    final requestUri = response.requestOptions.uri;
    final origins = <Uri>{
      requestUri,
      Uri.parse(ApiConstants.url),
      Uri.parse(ApiConstants.apiBaseUrl),
      Uri.parse(ApiConstants.reportApiBaseUrl),
    };

    for (final origin in origins) {
      final adapted = [
        for (final cookie in cookies) _adaptForMobile(cookie, origin),
      ];
      await jar.saveFromResponse(origin, adapted);
    }
  }

  Cookie _adaptForMobile(Cookie source, Uri origin) {
    final cookie = Cookie(source.name, source.value)
      ..path = source.path?.isNotEmpty == true ? source.path : '/'
      ..httpOnly = source.httpOnly
      ..expires = source.expires
      ..maxAge = source.maxAge;
    // HTTP LAN APIs cannot send cookies marked Secure.
    cookie.secure = origin.scheme == 'https' && source.secure;
    // IP hosts reject Domain= attributes meant for a hostname.
    if (!_isIpHost(origin.host)) {
      cookie.domain = source.domain;
    }
    return cookie;
  }

  static bool _isIpHost(String host) {
    final uri = Uri(host: host);
    return uri.host == host &&
        (RegExp(r'^\d{1,3}(\.\d{1,3}){3}$').hasMatch(host) ||
            host.contains(':'));
  }

  Future<bool> hasServerSession() async {
    final bases = <String>{
      ApiConstants.apiBaseUrl,
      ApiConstants.reportApiBaseUrl,
      ApiConstants.url,
    };
    for (final base in bases) {
      final uri = Uri.parse(base);
      final cookies = await jar.loadForRequest(uri);
      if (cookies.any(_isSessionCookie)) return true;
    }
    return false;
  }

  Future<({String? access, String? refresh})> readJwtCookies() async {
    String? access;
    String? refresh;
    final uri = Uri.parse(ApiConstants.apiBaseUrl);
    for (final cookie in await jar.loadForRequest(uri)) {
      final name = cookie.name.toLowerCase();
      if (name == 'access' || name == 'access_token' || name == 'jwt') {
        access = cookie.value;
      } else if (name == 'refresh' || name == 'refresh_token') {
        refresh = cookie.value;
      }
    }
    return (access: access, refresh: refresh);
  }

  Future<void> clear() => jar.deleteAll();

  static bool _isSessionCookie(Cookie cookie) {
    final name = cookie.name.toLowerCase();
    return name == 'sessionid' ||
        name == 'session' ||
        name.contains('sessionid');
  }
}
