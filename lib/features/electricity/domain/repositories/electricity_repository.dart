import 'electricity_coverage_repository.dart';
import 'electricity_dashboard_repository.dart';
import 'electricity_files_repository.dart';
import 'electricity_map_repository.dart';
import 'electricity_report_repository.dart';

abstract class ElectricityRepository
    implements
        ElectricityDashboardRepository,
        ElectricityReportRepository,
        ElectricityFilesRepository,
        ElectricityMapRepository,
        ElectricityCoverageRepository {}
