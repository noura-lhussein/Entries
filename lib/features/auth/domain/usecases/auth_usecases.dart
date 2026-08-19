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
