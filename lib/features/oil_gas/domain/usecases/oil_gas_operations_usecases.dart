import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_operations_repository.dart';

class UpsertOilGasOperationsUseCase {
  final OilGasOperationsRepository _repository;
  UpsertOilGasOperationsUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(Map<String, dynamic> payload) {
    return _repository.upsertDailyOperations(payload);
  }
}

class PublishOilGasDayUseCase {
  final OilGasOperationsRepository _repository;
  PublishOilGasDayUseCase(this._repository);

  Future<ApiResult<Map<String, dynamic>>> call(String productionDate) {
    return _repository.publishDay(productionDate);
  }
}
