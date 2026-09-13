import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthSecureStorage {
  final FlutterSecureStorage _storage;

  AuthSecureStorage(this._storage);

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _sessionFlagKey = 'has_server_session';

  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshTokenKey);
  }

  Future<void> setHasServerSession(bool value) async {
    if (value) {
      await _storage.write(key: _sessionFlagKey, value: '1');
    } else {
      await _storage.delete(key: _sessionFlagKey);
    }
  }

  Future<bool> hasServerSession() async {
    return await _storage.read(key: _sessionFlagKey) == '1';
  }

  Future<void> deleteAccessToken() async {
    await _storage.delete(key: _accessTokenKey);
  }

  Future<void> deleteRefreshToken() async {
    await _storage.delete(key: _refreshTokenKey);
  }

  Future<void> deleteTokens() async {
    await deleteAccessToken();
    await deleteRefreshToken();
  }

  Future<void> clearAll() async {
    await deleteTokens();
    await _storage.delete(key: _sessionFlagKey);
  }
}
