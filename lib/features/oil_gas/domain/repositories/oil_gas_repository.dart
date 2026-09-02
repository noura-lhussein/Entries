import 'oil_gas_dashboard_repository.dart';
import 'oil_gas_files_repository.dart';
import 'oil_gas_map_repository.dart';
import 'oil_gas_master_repository.dart';
import 'oil_gas_operations_repository.dart';
import 'oil_gas_report_repository.dart';
import 'oil_gas_targets_repository.dart';

abstract class OilGasRepository
    implements
        OilGasDashboardRepository,
        OilGasReportRepository,
        OilGasOperationsRepository,
        OilGasMasterRepository,
        OilGasFilesRepository,
        OilGasMapRepository,
        OilGasTargetsRepository {}
