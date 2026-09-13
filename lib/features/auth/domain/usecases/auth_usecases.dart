import '../../../../core/network/api_result.dart';
import '../entities/user_entity.dart';
import '../repositories/auth_repository.dart';

class LoginUseCase {
  final AuthRepository repository;

  LoginUseCase(this.repository);

  Future<ApiResult<UserEntity>> call(String email, String password) {
    return repository.login(email, password);
  }
}

class LogoutUseCase {
  final AuthRepository repository;

  LogoutUseCase(this.repository);

  Future<void> call() {
    return repository.logout();
  }
}

class ClearLocalSessionUseCase {
  final AuthRepository repository;

  ClearLocalSessionUseCase(this.repository);

  Future<void> call() {
    return repository.clearLocalSession();
  }
}

class CheckAuthStatusUseCase {
  final AuthRepository repository;

  CheckAuthStatusUseCase(this.repository);

  Future<bool> call() {
    return repository.isLoggedIn();
  }
}

class GetSavedUserUseCase {
  final AuthRepository repository;

  GetSavedUserUseCase(this.repository);

  Future<UserEntity?> call() {
    return repository.getSavedUser();
  }
}

class FetchMeUseCase {
  final AuthRepository repository;

  FetchMeUseCase(this.repository);

  Future<ApiResult<UserEntity>> call() {
    return repository.fetchMe();
  }
}

class UpdateProfileUseCase {
  final AuthRepository repository;
  UpdateProfileUseCase(this.repository);

  Future<ApiResult<UserEntity>> call({
    required int userId,
    required String firstName,
    required String lastName,
    required String email,
  }) {
    return repository.updateProfile(
      userId: userId,
      firstName: firstName,
      lastName: lastName,
      email: email,
    );
  }
}

class UpdateProfilePhotoUseCase {
  final AuthRepository repository;
  UpdateProfilePhotoUseCase(this.repository);

  Future<ApiResult<UserEntity>> call({
    required int userId,
    required String filePath,
  }) {
    return repository.updateProfilePhoto(userId: userId, filePath: filePath);
  }
}

class ChangePasswordUseCase {
  final AuthRepository repository;
  ChangePasswordUseCase(this.repository);

  Future<ApiResult<void>> call({
    required int userId,
    required String newPassword,
  }) {
    return repository.changePassword(userId: userId, newPassword: newPassword);
  }
}
