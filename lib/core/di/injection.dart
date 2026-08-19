import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../features/auth/data/datasources/auth_datasource.dart';
import '../../features/auth/data/datasources/auth_local_datasource.dart';
import '../../features/auth/data/datasources/auth_secure_storage.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/domain/usecases/auth_usecases.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/water/data/datasources/water_remote_data_source.dart';
import '../../features/water/data/datasources/water_admin_remote_data_source.dart';
import '../../features/oil_gas/data/datasources/oil_gas_remote_data_source.dart';
import '../../features/builder/data/datasources/builder_remote_data_source.dart';
import '../../features/builder/presentation/bloc/data_entry_bloc.dart';
import '../../features/electricity/data/datasources/electricity_remote_data_source.dart';
import '../../features/geology/data/datasources/geology_remote_data_source.dart';
import '../../features/water/data/repositories/water_repository_impl.dart';
import '../../features/water/domain/repositories/water_repository.dart';
import '../../features/water/domain/usecases/get_water_lookups_use_case.dart';
import '../../features/water/presentation/bloc/water_lookups_bloc.dart';
import '../network/auth_interceptor.dart';
import '../network/dio_client.dart';
import '../network/token_refresher.dart';
import '../utils/auth_listenable.dart';

final getIt = GetIt.instance;

Future<void> initInjection() async {
  // External
  final sharedPrefs = await SharedPreferences.getInstance();
  getIt.registerLazySingleton(() => sharedPrefs);
  getIt.registerLazySingleton(() => const FlutterSecureStorage());

  // Core
  final dio = await DioFactory.getDio();
  getIt.registerLazySingleton(() => dio);

  // Data sources
  getIt.registerLazySingleton(() => AuthSecureStorage(getIt()));
  getIt.registerLazySingleton(() => TokenRefresher(getIt()));
  getIt.registerLazySingleton(() => AuthLocalDataSource(getIt()));
  getIt.registerLazySingleton(() => AuthRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => WaterRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => WaterAdminRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => OilGasRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => ElectricityRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => BuilderRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => GeologyRemoteDataSource(getIt()));

  // Repository
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(
      remoteDataSource: getIt(),
      localDataSource: getIt(),
      secureStorage: getIt(),
      tokenRefresher: getIt(),
    ),
  );
  getIt.registerLazySingleton<WaterRepository>(
    () => WaterRepositoryImpl(getIt(), getIt()),
  );

  // Use cases
  getIt.registerLazySingleton(() => LoginUseCase(getIt()));
  getIt.registerLazySingleton(() => LogoutUseCase(getIt()));
  getIt.registerLazySingleton(() => ClearLocalSessionUseCase(getIt()));
  getIt.registerLazySingleton(() => CheckAuthStatusUseCase(getIt()));
  getIt.registerLazySingleton(() => GetSavedUserUseCase(getIt()));
  getIt.registerLazySingleton(() => FetchMeUseCase(getIt()));
  getIt.registerLazySingleton(() => GetWaterLookupsUseCase(getIt()));

  // BLoC
  getIt.registerLazySingleton(
    () => AuthBloc(
      loginUseCase: getIt(),
      logoutUseCase: getIt(),
      clearLocalSessionUseCase: getIt(),
      checkAuthStatusUseCase: getIt(),
      getSavedUserUseCase: getIt(),
      fetchMeUseCase: getIt(),
    ),
  );

  getIt.registerFactory(
    () => WaterLookupsBloc(
      getWaterLookupsUseCase: getIt(),
    ),
  );
  getIt.registerFactory(() => DataEntryBloc(getIt()));

  getIt.registerLazySingleton(() => AuthListenable(getIt()));

  // When refresh is rejected (401/403), clear session and go to login.
  getIt<TokenRefresher>().onSessionInvalidated = () {
    getIt<AuthBloc>().add(const SessionExpired());
  };

  // Add Auth Interceptor after everything is registered
  dio.interceptors.add(AuthInterceptor(getIt<TokenRefresher>(), dio));
}
