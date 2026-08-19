import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/login_response.dart';

class AuthLocalDataSource {
  final SharedPreferences _prefs;

  AuthLocalDataSource(this._prefs);

  static const String _userKey = 'cached_user';

  Future<void> saveUser(UserResponse user) async {
    await _prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  Future<UserResponse?> getUser() async {
    final jsonString = _prefs.getString(_userKey);
    if (jsonString != null) {
      return UserResponse.fromJson(jsonDecode(jsonString));
    }
    return null;
  }

  Future<void> clearUser() async {
    await _prefs.remove(_userKey);
  }
}
