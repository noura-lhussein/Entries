import '../../../../core/network/api_result.dart';
import '../entities/user_entity.dart';

abstract class AuthRepository {
  Future<ApiResult<UserEntity>> login(String email, String password);
  Future<ApiResult<UserEntity>> fetchMe();
  Future<void> logout();
  /// Clears tokens and cached user without calling the API.
  Future<void> clearLocalSession();
  Future<bool> isLoggedIn();
  Future<UserEntity?> getSavedUser();
}
