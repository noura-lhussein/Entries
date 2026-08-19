
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/main/presentation/screens/main_shell.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../di/injection.dart';
import '../models/user_model.dart';

import '../../features/auth/presentation/screens/splash_screen.dart';
import '../utils/auth_listenable.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  refreshListenable: getIt<AuthListenable>(),
  redirect: (context, state) {
    final authState = getIt<AuthBloc>().state;
    
    // Paths
    final bool isSplash = state.matchedLocation == '/';
    final bool isLoggingIn = state.matchedLocation == '/login';

    // 1. If checking auth (Initial/Loading), stay on Splash
    if (authState is AuthInitial
        // || authState is AuthLoading
    ) {
      return isSplash ? null : '/';
    }

    // 2. If authenticated, don't allow login or splash
    if (authState is AuthAuthenticated) {
      if (isLoggingIn || isSplash) return '/dashboard';
    }

    // 3. If unauthenticated, must be on login
    if (authState is AuthUnauthenticated) {
      if (!isLoggingIn) return '/login';
    }
    
    return null;
  },
  routes: [
    GoRoute(
      path: '/',
      name: 'splash',
      builder: (_, _) => const SplashScreen(),
    ),
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (_, _) => const LoginScreen(),
    ),
    GoRoute(
      path: '/dashboard',
      name: 'dashboard',
      builder: (_, state) {
        final authState = getIt<AuthBloc>().state;
        UserModel? user;
        if (authState is AuthAuthenticated) {
          user = authState.user.toUserModel();
        }
        return MainShell(user: user);
      },
    ),
  ],
);
