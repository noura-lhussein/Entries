import 'package:cookie_jar/cookie_jar.dart';
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

  Future<bool> hasServerSession() async {
    final bases = <String>{
      ApiConstants.apiBaseUrl,
      ApiConstants.reportApiBaseUrl,
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
