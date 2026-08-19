class ApiConstants {
  static const String version = '1.0.0';
  static const url = String.fromEnvironment(
    'API_ORIGIN',
  //   defaultValue: 'http://192.168.88.19:8000',
   defaultValue: 'https://admin-moed.moenergy.gov.sy',
  );

  /// Angular moe-portal origin (3D Cesium UI). Not the Django API host.
  static const portalUrl = String.fromEnvironment(
    'PORTAL_ORIGIN',
    defaultValue: 'https://moed.moenergy.gov.sy',
  );

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '$url/api/',
  );
  static const String imageBaseUrl = '$url/storage/app/public/';
  static const String imageBaseUrlAlt = '$url/storage/';

  /// Portal sector query slugs (match moe-portal SectorSlug).
  static const String sectorWater = 'water-resources';
  static const String sectorOilGas = 'oil-gas';
  static const String sectorElectricity = 'electricity';
  static const String sectorMineral = 'mineral-resources';

  // ── Auth ─────────────────────────────────────────────────────────────────
  static const String login = 'v1/auth/login/';
  static const String refresh = 'v1/auth/refresh/';
  static const String logout = 'v1/auth/logout/';
  static const String me = 'v1/auth/me/';

  // ── Water — Admin (data entry / imports) ─────────────────────────────────
  static const String waterAdminBase = 'v1/water/admin';
  static const String waterLookups = '$waterAdminBase/lookups/';
  static const String waterImportStatus = '$waterAdminBase/imports/status/';
  static const String waterRegistry = '$waterAdminBase/registry/';

  static const String waterDailyDamStorage = '$waterAdminBase/daily/dam-storage/';
  static const String waterDailyRainfall = '$waterAdminBase/daily/rainfall/';
  static const String waterDailyEuphrates = '$waterAdminBase/daily/euphrates/';
  static const String waterDailyDrinkingWater =
      '$waterAdminBase/daily/drinking-water/';

  static const String waterImportRainfall = '$waterAdminBase/imports/rainfall/';
  static const String waterImportDams = '$waterAdminBase/imports/dams/';
  static const String waterImportEuphrates = '$waterAdminBase/imports/euphrates/';
  static const String waterImportDrinkingWaterGeo =
      '$waterAdminBase/imports/drinking-water/geo/';
  static const String waterImportDrinkingWaterSurvey =
      '$waterAdminBase/imports/drinking-water/survey/';

  static const String waterClearRainfall =
      '$waterAdminBase/imports/rainfall/clear/';
  static const String waterClearDams = '$waterAdminBase/imports/dams/clear/';
  static const String waterClearEuphrates =
      '$waterAdminBase/imports/euphrates/clear/';

  static const String waterTemplates = '$waterAdminBase/templates/';
  static const String waterExportDrinkingWaterSurvey =
      '$waterAdminBase/exports/drinking-water/survey/';

  // ── Water — Portal dashboards (viewer) ───────────────────────────────────
  static const String waterBase = 'v1/water';
  static const String waterRainfallDashboard = '$waterBase/rainfall/dashboard/';
  static const String waterDamsDashboard = '$waterBase/dams/dashboard/';
  static const String waterDamsMapCatalog = '$waterBase/dams/map-catalog/';
  static const String waterEuphratesDashboard =
      '$waterBase/dams/euphrates/dashboard/';
  static const String waterDrinkingWaterDashboard =
      '$waterBase/drinking-water/dashboard/';
  static const String waterDrinkingWaterStations =
      '$waterBase/drinking-water/stations/';
  static const String waterReportExport = '$waterBase/reports/export/';

  // ── Oil & Gas ────────────────────────────────────────────────────────────
  static const String oilGasBase = 'v1/oil-gas';
  static const String oilGasAdminBase = '$oilGasBase/admin';
  static const String oilGasDashboard = '$oilGasBase/dashboard/';
  static const String oilGasReportDates = '$oilGasBase/report-dates/';
  static const String oilGasReports = '$oilGasBase/reports/';
  static const String oilGasReportDetail = '$oilGasBase/reports/detail/';
  static const String oilGasReportExport = '$oilGasBase/reports/export/';
  static const String oilGasReportUpsert = '$oilGasBase/reports/upsert/';
  static const String oilGasOperationsDaily = '$oilGasBase/operations/daily/';
  static const String oilGasOperationsPublish =
      '$oilGasBase/operations/publish/';
  static const String oilGasMasterFields = '$oilGasBase/master/fields/';
  static const String oilGasMasterFacilities =
      '$oilGasBase/master/facilities/';
  static const String oilGasMasterRefineries =
      '$oilGasBase/master/refineries/';
  static const String oilGasMapLayers = '$oilGasBase/map-layers';
  static const String oilGasTargets = '$oilGasBase/targets/';
  static const String oilGasTargetsCatalog = '$oilGasBase/targets/catalog/';
  static const String oilGasTargetsCompare = '$oilGasBase/targets/compare/';
  static const String oilGasTargetsFields = '$oilGasBase/targets/fields/';
  static const String oilGasTargetsMonthly = '$oilGasBase/targets/monthly/';
  static const String oilGasTargetsCoverage = '$oilGasBase/targets/coverage/';
  static const String oilGasAdminRegistry = '$oilGasAdminBase/registry/';

  // ── Electricity ──────────────────────────────────────────────────────────
  static const String electricityBase = 'v1/electricity';
  static const String electricityAdminBase = '$electricityBase/admin';
  static const String electricityDashboard = '$electricityBase/dashboard/';
  static const String electricityReportDates = '$electricityBase/report-dates/';
  static const String electricityReports = '$electricityBase/reports/';
  static const String electricityReportDetail =
      '$electricityBase/reports/detail/';
  static const String electricityReportExport =
      '$electricityBase/reports/export/';
  static const String electricityReportUpsert =
      '$electricityBase/reports/upsert/';
  static const String electricityMapLayers = '$electricityBase/map-layers';
  static const String electricityTargetCoverage =
      '$electricityBase/targets/coverage/';
  static const String electricityAdminRegistry =
      '$electricityAdminBase/registry/';

  // ── Geology / Mining ─────────────────────────────────────────────────────
  static const String geologyBase = 'v1/geology';
  static const String geologyAdminBase = '$geologyBase/admin';
  static const String geologyDashboard = '$geologyBase/dashboard/';
  static const String geologyReportExport = '$geologyBase/reports/export/';
  static const String geologyAdminRegistry = '$geologyAdminBase/registry/';
  static const String geologyDailyReport = '$geologyAdminBase/daily-report/';
  static const String geologyDailyReportTemplate =
      '$geologyAdminBase/daily-report/template/';
  static const String geologyDailyReportExport =
      '$geologyAdminBase/daily-report/export/';
  static const String geologyDailyReportImport =
      '$geologyAdminBase/daily-report/import/';
  static const String oilGasReportTemplate = '$oilGasBase/reports/template/';
  static const String oilGasReportImport = '$oilGasBase/reports/import/';
  static const String electricityReportTemplate =
      '$electricityBase/reports/template/';
  static const String electricityReportImport =
      '$electricityBase/reports/import/';

  // ── GIS ──────────────────────────────────────────────────────────────────
  static const String gisBase = 'v1/gis';
  static const String gisAdminLayers = '$gisBase/admin-layers/';
  static const String gisWaterLayers = '$gisBase/water-layers/';
  static const String gisGeologyLayers = '$gisBase/geology-layers/';
  static const String gisGeologyInfo = '$gisBase/geology-info/';
  static const String gisSpringsMapCatalog = '$gisBase/springs/map-catalog/';
  static const String gisFilters = '$gisBase/filters';

  // ── Datasets (data portal) ───────────────────────────────────────────────
  static const String datasetsBase = 'v1/datasets/';
  static const String datasetsMeta = '${datasetsBase}meta/';

  static String oilGasMapLayerGeoJson(String layerId) =>
      '$oilGasMapLayers/$layerId/geojson/';

  static String electricityMapLayerGeoJson(String layerId) =>
      '$electricityMapLayers/$layerId/geojson/';

  static String gisAdminLayerGeoJson(String layerId) =>
      '$gisAdminLayers$layerId/geojson/';

  static String gisWaterLayerGeoJson(String layerId) =>
      '$gisWaterLayers$layerId/geojson/';

  static String gisGeologyLayerGeoJson(String layerId) =>
      '$gisGeologyLayers$layerId/geojson/';

  static String gisFilterOptions(String filterKey) =>
      '$gisFilters/$filterKey/';

  static String datasetsDetail(int id) => '$datasetsBase$id/';
  static String datasetsPreview(int id) => '$datasetsBase$id/preview/';
  static String datasetsDownload(int id) => '$datasetsBase$id/download/';
  static String datasetsSpatialLayers(int id) =>
      '$datasetsBase$id/spatial-layers/';
  static String datasetsRecordDownload(int id) =>
      '$datasetsBase$id/record-download/';

  static String waterAdminResource(String slug) =>
      '$waterAdminBase/$slug/';
  static String oilGasAdminResource(String slug) =>
      '$oilGasAdminBase/$slug/';
  static String electricityAdminResource(String slug) =>
      '$electricityAdminBase/$slug/';
  static String geologyAdminResource(String slug) =>
      '$geologyAdminBase/$slug/';
}

class ApiErrors {
  static const String badRequestError = 'badRequestError';
  static const String noContent = 'noContent';
  static const String forbiddenError = 'forbiddenError';
  static const String unauthorizedError = 'unauthorizedError';
  static const String notFoundError = 'notFoundError';
  static const String conflictError = 'conflictError';

  static const String internalServerError = 'internalServerError';
  static const String usnknownError = 'unknownError';
  static const String timeoutError = 'timeoutError';
  static const String defaultError = 'defaultError';
  static const String cacheError = 'cacheError';
  static const String noInternetError = 'checkInternetConnectiondialog';
  static const String loadingMessage = 'loading_message';
  static const String retryAgainMessage = 'retry_again_message';
  static const String ok = 'Ok';
}
