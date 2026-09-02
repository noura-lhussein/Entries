import '../../../../core/network/api_result.dart';
import '../repositories/geology_dashboard_repository.dart';

class GetGeologyDashboardUseCase {
  final GeologyDashboardRepository _repository;
  GetGeologyDashboardUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call({int? planYear}) {
    return _repository.getDashboard(planYear: planYear);
  }
}
