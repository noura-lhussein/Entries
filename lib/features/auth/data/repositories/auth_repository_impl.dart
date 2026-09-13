import 'package:dio/dio.dart';
import '../../../../core/network/api_error_handler.dart';
import '../../../../core/network/api_result.dart';
import '../../../../core/network/api_constants.dart';
import '../../../../core/network/auth_tokens.dart';
import '../../../../core/network/cookie_session.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/network/jwt_util.dart';
import '../../../../core/network/token_refresher.dart';
import '../../../../core/utils/media_url.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_datasource.dart';
import '../datasources/auth_local_datasource.dart';
import '../datasources/auth_secure_storage.dart';
import '../models/login_response.dart';

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
      final response = await dio.post<dynamic>(
        ApiConstants.login,
        data: {
          'email': email,
          'username': email,
          'password': password,
        },
      );

      await cookieSession.saveFromResponse(response);

      final map = _asMap(response.data) ?? <String, dynamic>{};
      final parsed = LoginResponse.fromJson(map);
      final jwtCookies = await cookieSession.readJwtCookies();
      final tokens = AuthTokens(access: parsed.access, refresh: parsed.refresh)
          .merged(AuthTokens.fromHeaders(response.headers))
          .merged(
            AuthTokens(access: jwtCookies.access, refresh: jwtCookies.refresh),
          );

      await _persistTokens(tokens.access, tokens.refresh);
      await secureStorage.setHasServerSession(true);

      if (parsed.user != null) {
        await localDataSource.saveUser(parsed.user!);
      }

      final meResult = await fetchMe();
      if (meResult is Success<UserEntity>) {
        return ApiResult.success(meResult.data);
      }
      if (parsed.user != null) {
        return ApiResult.success(parsed.user!.toEntity());
      }
      return ApiResult.failure(ErrorHandler.handle('User data missing'));
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  Future<void> _persistTokens(String? access, String? refresh) async {
    final usableAccess = access != null &&
        access.isNotEmpty &&
        JwtUtil.looksLikeJwt(access) &&
        !JwtUtil.isExpired(access);
    final usableRefresh = refresh != null &&
        refresh.isNotEmpty &&
        JwtUtil.looksLikeJwt(refresh);

    if (usableAccess) {
      await secureStorage.saveAccessToken(access);
      DioFactory.updateHeaderWithToken(access);
    } else {
      await secureStorage.deleteAccessToken();
      DioFactory.clearToken();
    }
    if (usableRefresh) {
      await secureStorage.saveRefreshToken(refresh);
    } else {
      await secureStorage.deleteRefreshToken();
    }
  }

  Map<String, dynamic>? _asMap(dynamic data) {
    if (data is Map<String, dynamic>) return data;
    if (data is Map) return Map<String, dynamic>.from(data);
    return null;
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
  Future<ApiResult<UserEntity>> updateProfile({
    required int userId,
    required String firstName,
    required String lastName,
    required String email,
  }) async {
    try {
      await tokenRefresher.ensureAccessToken();
      final response = await dio.patch(
        ApiConstants.userById(userId),
        data: {
          'full_name': [firstName, lastName]
              .where((e) => e.trim().isNotEmpty)
              .join(' ')
              .trim(),
          'email': email,
        },
      );
      final parsed = _userFromBody(response.data);
      if (parsed != null) {
        await localDataSource.saveUser(parsed);
        final me = await fetchMe();
        if (me is Success<UserEntity>) return me;
        return ApiResult.success(parsed.toEntity());
      }
      final me = await fetchMe();
      if (me is Success<UserEntity>) return me;
      final cached = await getSavedUser();
      if (cached != null) {
        return ApiResult.success(
          cached.copyWith(
            firstName: firstName,
            lastName: lastName,
            email: email,
            fullName: [firstName, lastName]
                .where((e) => e.trim().isNotEmpty)
                .join(' '),
          ),
        );
      }
      return me;
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  @override
  Future<ApiResult<UserEntity>> updateProfilePhoto({
    required int userId,
    required String filePath,
  }) async {
    try {
      await tokenRefresher.ensureAccessToken();
      final filename = filePath.split(RegExp(r'[\\/]')).last;
      var uploadedUrl = await _patchUserPhotoFile(userId, filePath, filename);
      uploadedUrl ??= await _uploadThenPatchPhotoUrl(userId, filePath, filename);
      final photo = uploadedUrl ?? filePath;

      final me = await fetchMe();
      if (me is Success<UserEntity>) {
        final resolved =
            (me.data.photoUrl != null && me.data.photoUrl!.isNotEmpty)
                ? me.data.photoUrl!
                : photo;
        await _persistPhotoOnCachedUser(resolved);
        if (resolved != me.data.photoUrl) {
          return ApiResult.success(me.data.copyWith(photoUrl: resolved));
        }
        return me;
      }
      await _persistPhotoOnCachedUser(photo);
      final cached = await getSavedUser();
      if (cached != null) {
        return ApiResult.success(cached.copyWith(photoUrl: photo));
      }
      if (me is Failure<UserEntity>) return me;
      return ApiResult.failure(ErrorHandler.handle('تعذر تحديث الصورة'));
    } catch (error) {
      return ApiResult.failure(ErrorHandler.handle(error));
    }
  }

  Future<String?> _patchUserPhotoFile(
    int userId,
    String filePath,
    String filename,
  ) async {
    try {
      final file = await MultipartFile.fromFile(filePath, filename: filename);
      final response = await dio.patch(
        ApiConstants.userById(userId),
        data: FormData.fromMap({'photo': file}),
      );
      final parsed = _userFromBody(response.data);
      if (parsed != null) {
        await localDataSource.saveUser(parsed);
        return parsed.photoUrl;
      }
      return photoUrlFromJson(_asMap(response.data) ?? const {});
    } catch (_) {
      return null;
    }
  }

  Future<String?> _uploadThenPatchPhotoUrl(
    int userId,
    String filePath,
    String filename,
  ) async {
    try {
      final file = await MultipartFile.fromFile(filePath, filename: filename);
      final upload = await dio.post(
        ApiConstants.builderFormFileUpload,
        data: FormData.fromMap({'file': file, 'kind': 'image'}),
      );
      final url = _uploadUrl(upload.data);
      if (url == null || url.isEmpty) return null;
      await dio.patch(
        ApiConstants.userById(userId),
        data: {'photo': url},
      );
      return url;
    } catch (_) {
      return null;
    }
  }

  Future<void> _persistPhotoOnCachedUser(String url) async {
    final existing = await localDataSource.getUser();
    if (existing == null) return;
    await localDataSource.saveUser(
      UserResponse.fromJson({
        ...existing.toJson(),
        'photo': url,
      }),
    );
  }

  UserResponse? _userFromBody(dynamic data) {
    final map = _asMap(data);
    if (map == null) return null;
    if (map['id'] == null && map['username'] == null && map['email'] == null) {
      return null;
    }
    return UserResponse.fromJson(map);
  }

  String? _uploadUrl(dynamic data) {
    final map = _asMap(data);
    if (map == null) return null;
    final url = map['url']?.toString().trim();
    if (url != null && url.isNotEmpty) return url;
    return photoUrlFromJson(map);
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
    final hasAccess = access != null &&
        access.isNotEmpty &&
        JwtUtil.looksLikeJwt(access);
    final hasRefresh =
        refresh != null && refresh.isNotEmpty && JwtUtil.looksLikeJwt(refresh);

    if (access != null && access.isNotEmpty && !hasAccess) {
      await secureStorage.deleteAccessToken();
      DioFactory.clearToken();
    }

    if (hasAccess && !JwtUtil.isExpired(access)) {
      DioFactory.updateHeaderWithToken(access);
      return true;
    }
    if (hasRefresh) return true;
    DioFactory.clearToken();
    if (await cookieSession.hasServerSession()) return true;
    return secureStorage.hasServerSession();
  }

  @override
  Future<UserEntity?> getSavedUser() async {
    final userResponse = await localDataSource.getUser();
    return userResponse?.toEntity();
  }
}
