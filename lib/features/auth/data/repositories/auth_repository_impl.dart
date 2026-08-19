import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/jwt_util.dart';
import '../../../../core/network/token_refresher.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_datasource.dart';
import '../datasources/auth_local_datasource.dart';
import '../datasources/auth_secure_storage.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final AuthLocalDataSource localDataSource;
  final AuthSecureStorage secureStorage;
  final TokenRefresher tokenRefresher;

  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
    required this.secureStorage,
    required this.tokenRefresher,
  });

  @override
  Future<ApiResult<UserEntity>> login(String email, String password) async {
    try {
      final response = await remoteDataSource.login({
        'email': email,
        'password': password,
      });

      if (response.access != null) {
        await secureStorage.saveAccessToken(response.access!);
      }
      if (response.refresh != null) {
        await secureStorage.saveRefreshToken(response.refresh!);
      }
      if (response.user != null) {
        await localDataSource.saveUser(response.user!);
      }

      // Prefer /auth/me/ for full permissions (same as moe-portal).
      final meResult = await fetchMe();
      if (meResult is Success<UserEntity>) {
        return ApiResult.success(meResult.data);
      }
      if (response.user != null) {
        return ApiResult.success(response.user!.toEntity());
      }
      return ApiResult.failure(ErrorHandler.handle('User data missing'));
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<UserEntity>> fetchMe() async {
    try {
      await tokenRefresher.ensureAccessToken();
      final user = await remoteDataSource.getMe();
      await localDataSource.saveUser(user);
      return ApiResult.success(user.toEntity());
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<void> logout() async {
    try {
      await remoteDataSource.logout();
    } catch (_) {
      // Even if API logout fails, we should clear local data
    } finally {
      await clearLocalSession();
    }
  }

  @override
  Future<void> clearLocalSession() async {
    await secureStorage.clearAll();
    await localDataSource.clearUser();
    DioFactory.clearToken();
  }

  @override
  Future<bool> isLoggedIn() async {
    final access = await secureStorage.getAccessToken();
    final refresh = await secureStorage.getRefreshToken();
    final hasAccess = access != null && access.isNotEmpty;
    final hasRefresh = refresh != null && refresh.isNotEmpty;
    if (!hasAccess && !hasRefresh) return false;

    // Valid access, or refresh available to renew it.
    if (hasAccess && !JwtUtil.isExpired(access)) return true;
    return hasRefresh;
  }

  @override
  Future<UserEntity?> getSavedUser() async {
    final userResponse = await localDataSource.getUser();
    return userResponse?.toEntity();
  }
}
