import 'geology_dashboard_repository.dart';
import 'geology_files_repository.dart';
import 'geology_report_repository.dart';

abstract class GeologyRepository
    implements
        GeologyDashboardRepository,
        GeologyReportRepository,
        GeologyFilesRepository {}
