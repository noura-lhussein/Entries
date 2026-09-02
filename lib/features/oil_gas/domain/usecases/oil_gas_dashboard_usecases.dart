import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_dashboard_repository.dart';

class GetOilGasDashboardUseCase {
  final OilGasDashboardRepository _repository;
  GetOilGasDashboardUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call({
    String period = 'day',
    String? date,
    String? month,
  }) {
    return _repository.getDashboard(period: period, date: date, month: month);
  }
}
