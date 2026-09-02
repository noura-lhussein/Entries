import 'package:bloc/bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/entities/user_entity.dart';
import '../../domain/usecases/auth_usecases.dart';

part 'auth_event.dart';
part 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final LoginUseCase loginUseCase;
  final LogoutUseCase logoutUseCase;
  final ClearLocalSessionUseCase clearLocalSessionUseCase;
  final CheckAuthStatusUseCase checkAuthStatusUseCase;
  final GetSavedUserUseCase getSavedUserUseCase;
  final FetchMeUseCase fetchMeUseCase;

  AuthBloc({
    required this.loginUseCase,
    required this.logoutUseCase,
    required this.clearLocalSessionUseCase,
    required this.checkAuthStatusUseCase,
    required this.getSavedUserUseCase,
    required this.fetchMeUseCase,
  }) : super(const AuthInitial()) {
    on<LoginRequested>(_onLogin);
    on<LogoutRequested>(_onLogout);
    on<SessionExpired>(_onSessionExpired);
    on<CheckAuthStatus>(_onCheck);
    on<UserUpdated>(_onUserUpdated);

    // Automatically check status on creation
    add(const CheckAuthStatus());
  }

  Future<void> _onLogin(LoginRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    
    final result = await loginUseCase(event.email, event.password);
    
    result.when(
      success: (user) {
        emit(AuthAuthenticated(user: user));
      },
      failure: (error) {
        emit(AuthError(message: error.apiErrorModel.message ?? 'حدث خطأ ما'));
      },
    );
  }

  Future<void> _onLogout(LogoutRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    await logoutUseCase();
    emit(const AuthUnauthenticated());
  }

  Future<void> _onSessionExpired(
    SessionExpired event,
    Emitter<AuthState> emit,
  ) async {
    if (state is AuthUnauthenticated) return;
    await clearLocalSessionUseCase();
    emit(const AuthUnauthenticated());
  }

  Future<void> _onCheck(CheckAuthStatus event, Emitter<AuthState> emit) async {
    try {
      final isLoggedIn = await checkAuthStatusUseCase();
      if (!isLoggedIn) {
        emit(const AuthUnauthenticated());
        return;
      }

      final me = await fetchMeUseCase();
      if (me is Success<UserEntity>) {
        emit(AuthAuthenticated(user: me.data));
        return;
      }

      // Refresh/auth may have cleared the session while /me was running.
      final stillLoggedIn = await checkAuthStatusUseCase();
      if (!stillLoggedIn) {
        await clearLocalSessionUseCase();
        emit(const AuthUnauthenticated());
        return;
      }

      // Keep the user inside the app on transient /me issues while tokens remain.
      final cached = await getSavedUserUseCase();
      if (cached != null) {
        emit(AuthAuthenticated(user: cached));
        return;
      }
      emit(const AuthUnauthenticated());
    } catch (e) {
      final stillLoggedIn = await checkAuthStatusUseCase();
      if (!stillLoggedIn) {
        await clearLocalSessionUseCase();
        emit(const AuthUnauthenticated());
        return;
      }
      final cached = await getSavedUserUseCase();
      if (cached != null) {
        emit(AuthAuthenticated(user: cached));
        return;
      }
      emit(const AuthUnauthenticated());
    }
  }

  void _onUserUpdated(UserUpdated event, Emitter<AuthState> emit) {
    emit(AuthAuthenticated(user: event.user));
  }
}
