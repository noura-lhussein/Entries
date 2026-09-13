import '../../../../core/network/api_result.dart';
import '../entities/user_entity.dart';

abstract class AuthRepository {
  Future<ApiResult<UserEntity>> login(String email, String password);
  Future<ApiResult<UserEntity>> fetchMe();
  Future<ApiResult<UserEntity>> updateProfile({
    required int userId,
    required String firstName,
    required String lastName,
    required String email,
  });
  Future<ApiResult<UserEntity>> updateProfilePhoto({
    required int userId,
    required String filePath,
  });
  Future<ApiResult<void>> changePassword({
    required int userId,
    required String newPassword,
  });
  Future<void> logout();
  /// Clears tokens and cached user without calling the API.
  Future<void> clearLocalSession();
  Future<bool> isLoggedIn();
  Future<UserEntity?> getSavedUser();
}
