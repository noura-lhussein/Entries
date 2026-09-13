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
import '../../features/oil_gas/data/repositories/oil_gas_repository_impl.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_dashboard_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_files_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_map_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_master_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_operations_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_report_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_repository.dart';
import '../../features/oil_gas/domain/repositories/oil_gas_targets_repository.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_dashboard_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_files_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_map_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_master_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_operations_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_report_usecases.dart';
import '../../features/oil_gas/domain/usecases/oil_gas_targets_usecases.dart';
import '../../features/oil_gas/presentation/bloc/ops/petroleum_ops_bloc.dart';
import '../../features/oil_gas/presentation/bloc/spc/spc_report_bloc.dart';
import '../../features/builder/data/datasources/builder_remote_data_source.dart';
import '../../features/builder/presentation/bloc/data_entry_bloc.dart';
import '../../features/builder/presentation/bloc/info_browse_bloc.dart';
import '../../features/profile/presentation/bloc/profile_bloc.dart';
import '../../features/electricity/data/datasources/electricity_remote_data_source.dart';
import '../../features/electricity/data/repositories/electricity_repository_impl.dart';
import '../../features/electricity/domain/repositories/electricity_coverage_repository.dart';
import '../../features/electricity/domain/repositories/electricity_dashboard_repository.dart';
import '../../features/electricity/domain/repositories/electricity_files_repository.dart';
import '../../features/electricity/domain/repositories/electricity_map_repository.dart';
import '../../features/electricity/domain/repositories/electricity_report_repository.dart';
import '../../features/electricity/domain/repositories/electricity_repository.dart';
import '../../features/electricity/domain/usecases/electricity_coverage_usecases.dart';
import '../../features/electricity/domain/usecases/electricity_dashboard_usecases.dart';
import '../../features/electricity/domain/usecases/electricity_files_usecases.dart';
import '../../features/electricity/domain/usecases/electricity_map_usecases.dart';
import '../../features/electricity/domain/usecases/electricity_report_usecases.dart';
import '../../features/electricity/presentation/bloc/electricity_bloc.dart';
import '../../features/geology/data/datasources/geology_remote_data_source.dart';
import '../../features/geology/data/repositories/geology_repository_impl.dart';
import '../../features/geology/domain/repositories/geology_dashboard_repository.dart';
import '../../features/geology/domain/repositories/geology_files_repository.dart';
import '../../features/geology/domain/repositories/geology_report_repository.dart';
import '../../features/geology/domain/repositories/geology_repository.dart';
import '../../features/geology/domain/usecases/geology_dashboard_usecases.dart';
import '../../features/geology/domain/usecases/geology_files_usecases.dart';
import '../../features/geology/domain/usecases/geology_report_usecases.dart';
import '../../features/geology/presentation/bloc/ore/geology_ore_bloc.dart';
import '../../features/water/data/repositories/water_repository_impl.dart';
import '../../features/water/domain/repositories/water_dams_repository.dart';
import '../../features/water/domain/repositories/water_drinking_repository.dart';
import '../../features/water/domain/repositories/water_euphrates_repository.dart';
import '../../features/water/domain/repositories/water_files_repository.dart';
import '../../features/water/domain/repositories/water_lookups_repository.dart';
import '../../features/water/domain/repositories/water_rainfall_repository.dart';
import '../../features/water/domain/repositories/water_repository.dart';
import '../../features/water/domain/usecases/get_water_lookups_use_case.dart';
import '../../features/water/domain/usecases/water_dams_usecases.dart';
import '../../features/water/domain/usecases/water_drinking_usecases.dart';
import '../../features/water/domain/usecases/water_euphrates_usecases.dart';
import '../../features/water/domain/usecases/water_files_usecases.dart';
import '../../features/water/domain/usecases/water_rainfall_usecases.dart';
import '../../features/water/presentation/bloc/dams/dams_bloc.dart';
import '../../features/water/presentation/bloc/drinking_water/drinking_water_bloc.dart';
import '../../features/water/presentation/bloc/euphrates/euphrates_bloc.dart';
import '../../features/water/presentation/bloc/rainfall/rainfall_bloc.dart';
import '../../features/water/presentation/bloc/water_lookups_bloc.dart';
import '../network/auth_interceptor.dart';
import '../network/cookie_session.dart';
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
  final reportDio = await DioFactory.getReportDio();
  getIt.registerLazySingleton(() => dio);

  // Data sources
  getIt.registerLazySingleton(() => AuthSecureStorage(getIt()));
  getIt.registerLazySingleton(() => CookieSession(DioFactory.cookieJar!));
  getIt.registerLazySingleton(() => TokenRefresher(getIt(), getIt()));
  getIt.registerLazySingleton(() => AuthLocalDataSource(getIt()));
  getIt.registerLazySingleton(() => AuthRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => WaterRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => WaterAdminRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => OilGasRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => ElectricityRemoteDataSource(getIt()));
  getIt.registerLazySingleton(() => BuilderRemoteDataSource(reportDio));
  getIt.registerLazySingleton(() => GeologyRemoteDataSource(getIt()));

  // Repository
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(
      remoteDataSource: getIt(),
      localDataSource: getIt(),
      secureStorage: getIt(),
      tokenRefresher: getIt(),
      cookieSession: getIt(),
      dio: getIt(),
    ),
  );
  getIt.registerLazySingleton<WaterRepository>(
    () => WaterRepositoryImpl(getIt(), getIt()),
  );
  getIt.registerLazySingleton<WaterLookupsRepository>(
    () => getIt<WaterRepository>(),
  );
  getIt.registerLazySingleton<WaterFilesRepository>(
    () => getIt<WaterRepository>(),
  );
  getIt.registerLazySingleton<WaterDamsRepository>(
    () => getIt<WaterRepository>(),
  );
  getIt.registerLazySingleton<WaterRainfallRepository>(
    () => getIt<WaterRepository>(),
  );
  getIt.registerLazySingleton<WaterEuphratesRepository>(
    () => getIt<WaterRepository>(),
  );
  getIt.registerLazySingleton<WaterDrinkingRepository>(
    () => getIt<WaterRepository>(),
  );

  getIt.registerLazySingleton<ElectricityRepository>(
    () => ElectricityRepositoryImpl(getIt()),
  );
  getIt.registerLazySingleton<ElectricityDashboardRepository>(
    () => getIt<ElectricityRepository>(),
  );
  getIt.registerLazySingleton<ElectricityReportRepository>(
    () => getIt<ElectricityRepository>(),
  );
  getIt.registerLazySingleton<ElectricityFilesRepository>(
    () => getIt<ElectricityRepository>(),
  );
  getIt.registerLazySingleton<ElectricityMapRepository>(
    () => getIt<ElectricityRepository>(),
  );
  getIt.registerLazySingleton<ElectricityCoverageRepository>(
    () => getIt<ElectricityRepository>(),
  );

  getIt.registerLazySingleton<OilGasRepository>(
    () => OilGasRepositoryImpl(getIt()),
  );
  getIt.registerLazySingleton<OilGasDashboardRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasReportRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasOperationsRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasMasterRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasFilesRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasMapRepository>(
    () => getIt<OilGasRepository>(),
  );
  getIt.registerLazySingleton<OilGasTargetsRepository>(
    () => getIt<OilGasRepository>(),
  );

  getIt.registerLazySingleton<GeologyRepository>(
    () => GeologyRepositoryImpl(getIt()),
  );
  getIt.registerLazySingleton<GeologyDashboardRepository>(
    () => getIt<GeologyRepository>(),
  );
  getIt.registerLazySingleton<GeologyReportRepository>(
    () => getIt<GeologyRepository>(),
  );
  getIt.registerLazySingleton<GeologyFilesRepository>(
    () => getIt<GeologyRepository>(),
  );

  // Use cases
  getIt.registerLazySingleton(() => LoginUseCase(getIt()));
  getIt.registerLazySingleton(() => LogoutUseCase(getIt()));
  getIt.registerLazySingleton(() => ClearLocalSessionUseCase(getIt()));
  getIt.registerLazySingleton(() => CheckAuthStatusUseCase(getIt()));
  getIt.registerLazySingleton(() => GetSavedUserUseCase(getIt()));
  getIt.registerLazySingleton(() => FetchMeUseCase(getIt()));
  getIt.registerLazySingleton(() => UpdateProfileUseCase(getIt()));
  getIt.registerLazySingleton(() => UpdateProfilePhotoUseCase(getIt()));
  getIt.registerLazySingleton(() => ChangePasswordUseCase(getIt()));
  getIt.registerLazySingleton(() => GetWaterLookupsUseCase(getIt()));
  getIt.registerLazySingleton(() => GetWaterImportStatusUseCase(getIt()));
  getIt.registerLazySingleton(() => DownloadWaterTemplateUseCase(getIt()));
  getIt.registerLazySingleton(() => ExportDrinkingWaterSurveyUseCase(getIt()));
  getIt.registerLazySingleton(() => SaveDamDailyUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportDamsUseCase(getIt()));
  getIt.registerLazySingleton(() => ClearDamStorageUseCase(getIt()));
  getIt.registerLazySingleton(() => SaveRainfallDailyUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportRainfallUseCase(getIt()));
  getIt.registerLazySingleton(() => ClearRainfallUseCase(getIt()));
  getIt.registerLazySingleton(() => GetEuphratesDailyUseCase(getIt()));
  getIt.registerLazySingleton(() => SaveEuphratesDailyUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportEuphratesUseCase(getIt()));
  getIt.registerLazySingleton(() => ClearEuphratesUseCase(getIt()));
  getIt.registerLazySingleton(() => GetDrinkingWaterStationUseCase(getIt()));
  getIt.registerLazySingleton(() => SaveDrinkingWaterStationUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportDrinkingWaterGeoUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportDrinkingWaterSurveyUseCase(getIt()));
  getIt.registerLazySingleton(() => GetElectricityDashboardUseCase(getIt()));
  getIt.registerLazySingleton(() => UpsertElectricityReportUseCase(getIt()));
  getIt.registerLazySingleton(() => GetElectricityReportDetailUseCase(getIt()));
  getIt.registerLazySingleton(() => GetElectricityReportDatesUseCase(getIt()));
  getIt.registerLazySingleton(() => ListElectricityReportsUseCase(getIt()));
  getIt.registerLazySingleton(
    () => DownloadElectricityReportTemplateUseCase(getIt()),
  );
  getIt.registerLazySingleton(() => ImportElectricityDailyReportUseCase(getIt()));
  getIt.registerLazySingleton(() => ExportElectricityReportUseCase(getIt()));
  getIt.registerLazySingleton(() => GetElectricityMapLayerUseCase(getIt()));
  getIt.registerLazySingleton(() => GetElectricityTargetCoverageUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasDashboardUseCase(getIt()));
  getIt.registerLazySingleton(() => UpsertOilGasReportUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasReportDetailUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasReportDatesUseCase(getIt()));
  getIt.registerLazySingleton(() => ListOilGasReportsUseCase(getIt()));
  getIt.registerLazySingleton(() => UpsertOilGasOperationsUseCase(getIt()));
  getIt.registerLazySingleton(() => PublishOilGasDayUseCase(getIt()));
  getIt.registerLazySingleton(() => LoadOilGasMasterUseCase(getIt()));
  getIt.registerLazySingleton(
    () => DownloadOilGasExecutiveTemplateUseCase(getIt()),
  );
  getIt.registerLazySingleton(() => ImportOilGasExecutiveReportUseCase(getIt()));
  getIt.registerLazySingleton(() => ExportOilGasReportUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasMapLayerUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasTargetCoverageUseCase(getIt()));
  getIt.registerLazySingleton(() => GetOilGasFieldTargetMatrixUseCase(getIt()));
  getIt.registerLazySingleton(() => GetGeologyDashboardUseCase(getIt()));
  getIt.registerLazySingleton(() => GetGeologyDailyReportUseCase(getIt()));
  getIt.registerLazySingleton(() => SaveGeologyDailyReportUseCase(getIt()));
  getIt.registerLazySingleton(() => DownloadGeologyReportUseCase(getIt()));
  getIt.registerLazySingleton(() => DownloadGeologyOreTemplateUseCase(getIt()));
  getIt.registerLazySingleton(() => ExportGeologyOreProductionUseCase(getIt()));
  getIt.registerLazySingleton(() => ImportGeologyOreProductionUseCase(getIt()));

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
  getIt.registerFactory(
    () => DamsBloc(
      getImportStatus: getIt(),
      saveDamDaily: getIt(),
      importDams: getIt(),
      clearDamStorage: getIt(),
    ),
  );
  getIt.registerFactory(
    () => RainfallBloc(
      getImportStatus: getIt(),
      saveRainfallDaily: getIt(),
      importRainfall: getIt(),
      clearRainfall: getIt(),
    ),
  );
  getIt.registerFactory(
    () => EuphratesBloc(
      getImportStatus: getIt(),
      getEuphratesDaily: getIt(),
      saveEuphratesDaily: getIt(),
      importEuphrates: getIt(),
      clearEuphrates: getIt(),
    ),
  );
  getIt.registerFactory(
    () => DrinkingWaterBloc(
      getImportStatus: getIt(),
      getStation: getIt(),
      saveStation: getIt(),
      importGeo: getIt(),
      importSurvey: getIt(),
    ),
  );
  getIt.registerFactory(
    () => ElectricityBloc(
      upsertReport: getIt(),
      getReportDetail: getIt(),
    ),
  );
  getIt.registerFactory(
    () => PetroleumOpsBloc(
      loadMaster: getIt(),
      upsertOperations: getIt(),
      publishDay: getIt(),
    ),
  );
  getIt.registerFactory(
    () => SpcReportBloc(
      getReportDates: getIt(),
      getReportDetail: getIt(),
      upsertReport: getIt(),
      downloadTemplate: getIt(),
      importReport: getIt(),
    ),
  );
  getIt.registerFactory(
    () => GeologyOreBloc(
      getDailyReport: getIt(),
      saveDailyReport: getIt(),
      downloadTemplate: getIt(),
      exportProduction: getIt(),
      importProduction: getIt(),
    ),
  );
  getIt.registerFactory(() => DataEntryBloc(getIt()));
  getIt.registerFactory(() => InfoBrowseBloc(getIt()));
  getIt.registerFactory(
    () => ProfileBloc(
      updateProfile: getIt(),
      updateProfilePhoto: getIt(),
      changePassword: getIt(),
    ),
  );

  getIt.registerLazySingleton(() => AuthListenable(getIt()));

  // When refresh is rejected (401/403), clear session and go to login.
  getIt<TokenRefresher>().onSessionInvalidated = () {
    getIt<AuthBloc>().add(const SessionExpired());
  };

  // Add Auth Interceptor after everything is registered
  final tokenRefresher = getIt<TokenRefresher>();
  dio.interceptors.insert(0, AuthInterceptor(tokenRefresher, dio));
  if (!identical(reportDio, dio)) {
    reportDio.interceptors.insert(0, AuthInterceptor(tokenRefresher, reportDio));
  }
}
