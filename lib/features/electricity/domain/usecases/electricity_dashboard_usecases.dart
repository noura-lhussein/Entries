import '../../../../core/network/api_result.dart';
import '../repositories/electricity_dashboard_repository.dart';

class GetElectricityDashboardUseCase {
  final ElectricityDashboardRepository _repository;

  GetElectricityDashboardUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call({
    String period = 'day',
    String? date,
    String? month,
  }) {
    return _repository.getDashboard(period: period, date: date, month: month);
  }
}
