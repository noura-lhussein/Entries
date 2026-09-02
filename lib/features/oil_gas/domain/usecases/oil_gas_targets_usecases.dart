import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_targets_repository.dart';

class GetOilGasTargetCoverageUseCase {
  final OilGasTargetsRepository _repository;
  GetOilGasTargetCoverageUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call({String? date}) {
    return _repository.getTargetCoverage(date: date);
  }
}

class GetOilGasFieldTargetMatrixUseCase {
  final OilGasTargetsRepository _repository;
  GetOilGasFieldTargetMatrixUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(String date) {
    return _repository.getFieldTargetMatrix(date);
  }
}
