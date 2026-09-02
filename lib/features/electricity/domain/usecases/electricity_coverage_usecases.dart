import '../../../../core/network/api_result.dart';
import '../repositories/electricity_coverage_repository.dart';

class GetElectricityTargetCoverageUseCase {
  final ElectricityCoverageRepository _repository;

  GetElectricityTargetCoverageUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call({String? date}) {
    return _repository.getTargetCoverage(date: date);
  }
}
