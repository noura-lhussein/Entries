part of 'auth_bloc.dart';

abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override List<Object?> get props => [];
}

class LoginRequested extends AuthEvent {
  final String email;
  final String password;
  final bool rememberMe;
  const LoginRequested({required this.email, required this.password, required this.rememberMe});
  @override List<Object?> get props => [email, password, rememberMe];
}

class LogoutRequested  extends AuthEvent { const LogoutRequested(); }
class SessionExpired   extends AuthEvent { const SessionExpired(); }
class CheckAuthStatus  extends AuthEvent { const CheckAuthStatus(); }
