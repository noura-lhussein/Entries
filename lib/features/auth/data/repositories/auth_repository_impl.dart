import 'package:dio/dio.dart';
import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../../../core/network/api_constants.dart';
import '../../../../core/network/cookie_session.dart';
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
  final CookieSession cookieSession;
  final Dio dio;

  AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
    required this.secureStorage,
    required this.tokenRefresher,
    required this.cookieSession,
    required this.dio,
  });

  @override
  Future<ApiResult<UserEntity>> login(String email, String password) async {
    try {
      final response = await remoteDataSource.login({
        'email': email,
        'username': email,
        'password': password,
      });

      await _persistCredentials(response.access, response.refresh);
      await _warmCsrfCookie();

      if (response.user != null) {
        await localDataSource.saveUser(response.user!);
      }

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

  Future<void> _persistCredentials(String? access, String? refresh) async {
    var accessToken = access;
    var refreshToken = refresh;
    final fromCookies = await cookieSession.readJwtCookies();
    accessToken ??= fromCookies.access;
    refreshToken ??= fromCookies.refresh;

    if (accessToken != null && accessToken.isNotEmpty) {
      await secureStorage.saveAccessToken(accessToken);
      DioFactory.updateHeaderWithToken(accessToken);
    }
    if (refreshToken != null && refreshToken.isNotEmpty) {
      await secureStorage.saveRefreshToken(refreshToken);
    }
    await secureStorage.setHasServerSession(true);
  }

  Future<void> _warmCsrfCookie() async {
    final client = DioFactory.dio;
    if (client == null) return;
    try {
      await client.get<dynamic>(ApiConstants.csrf);
    } catch (_) {
      // Optional on session APIs; csrftoken often arrives with login Set-Cookie.
    }
  }

  @override
  Future<ApiResult<UserEntity>> fetchMe() async {
    try {
      await tokenRefresher.ensureAccessToken();
      final user = await remoteDataSource.getMe();
      await localDataSource.saveUser(user);
      await secureStorage.setHasServerSession(true);
      return ApiResult.success(user.toEntity());
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<UserEntity>> updateProfile({
    required int userId,
    required String firstName,
    required String lastName,
    required String email,
  }) async {
    try {
      await tokenRefresher.ensureAccessToken();
      await dio.patch(
        ApiConstants.userById(userId),
        data: {
          'first_name': firstName,
          'last_name': lastName,
          'email': email,
        },
      );
      return await fetchMe();
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<void>> changePassword({
    required int userId,
    required String newPassword,
  }) async {
    try {
      await tokenRefresher.ensureAccessToken();
      await dio.patch(
        ApiConstants.userById(userId),
        data: {'password': newPassword},
      );
      return const ApiResult.success(null);
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
    await cookieSession.clear();
    DioFactory.clearToken();
  }

  @override
  Future<bool> isLoggedIn() async {
    final access = await secureStorage.getAccessToken();
    final refresh = await secureStorage.getRefreshToken();
    final hasAccess = access != null && access.isNotEmpty;
    final hasRefresh = refresh != null && refresh.isNotEmpty;
    if (hasAccess && !JwtUtil.isExpired(access)) return true;
    if (hasRefresh) return true;
    if (await cookieSession.hasServerSession()) return true;
    return secureStorage.hasServerSession();
  }

  @override
  Future<UserEntity?> getSavedUser() async {
    final userResponse = await localDataSource.getUser();
    return userResponse?.toEntity();
  }
}
