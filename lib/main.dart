import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'core/theme/app_theme.dart';
import 'core/utils/app_router.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';

import 'core/di/injection.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Keep the UI alive if a network 404 (or similar) is not awaited.
  WidgetsBinding.instance.platformDispatcher.onError = (error, stack) {
    if (error is DioException) {
      debugPrint(
        'Unhandled DioException ${error.response?.statusCode} '
        '${error.requestOptions.uri}',
      );
      return true;
    }
    return false;
  };
  await initInjection();
  // Force portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp, DeviceOrientation.portraitDown,
  ]);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  runApp(const EnergyMinistryApp());
}

class EnergyMinistryApp extends StatelessWidget {
  const EnergyMinistryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(390, 844), // iPhone 14 base
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (context, child) {
        return MultiBlocProvider(
          providers: [
            BlocProvider<AuthBloc>(
              lazy: false,
              create: (_) => getIt<AuthBloc>(),
            ),
          ],
          child: MaterialApp.router(
            title: 'وزارة الطاقة — قسم الإدخال',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.theme,
            routerConfig: appRouter,
            locale: const Locale('ar', 'SY'),
            supportedLocales: const [Locale('ar', 'SY'), Locale('en', 'US')],
            localeResolutionCallback: (_, __) => const Locale('ar', 'SY'),
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            builder: (ctx, widget) => Directionality(
              textDirection: TextDirection.rtl,
              child: widget ?? const SizedBox.shrink(),
            ),
          ),
        );
      },
    );
  }
}
