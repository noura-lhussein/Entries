import 'dart:convert';

/// JWT helpers matching moe-portal `jwt.util.ts`.
abstract final class JwtUtil {
  static int? expiryMs(String token) {
    try {
      final parts = token.split('.');
      if (parts.length < 2) return null;
      final normalized = base64Url.normalize(parts[1]);
      final json = jsonDecode(utf8.decode(base64Url.decode(normalized)));
      if (json is! Map || json['exp'] == null) return null;
      final exp = json['exp'];
      if (exp is int) return exp * 1000;
      if (exp is num) return exp.toInt() * 1000;
      return int.tryParse(exp.toString()) != null
          ? int.parse(exp.toString()) * 1000
          : null;
    } catch (_) {
      return null;
    }
  }

  /// Treat as expired [skewMs] before real expiry (default 30s, same as portal).
  static bool isExpired(String token, {int skewMs = 30000}) {
    if (!looksLikeJwt(token)) return true;
    final exp = expiryMs(token);
    if (exp == null) return true;
    return DateTime.now().millisecondsSinceEpoch >= exp - skewMs;
  }

  static bool looksLikeJwt(String token) {
    final parts = token.trim().split('.');
    return parts.length == 3 && parts.every((p) => p.isNotEmpty);
  }
}
