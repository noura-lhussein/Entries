import '../../../../core/network/api_result.dart';
import '../repositories/oil_gas_master_repository.dart';
import '../services/oil_gas_master_parser.dart';

class LoadOilGasMasterUseCase {
  final OilGasMasterRepository _repository;
  LoadOilGasMasterUseCase(this._repository);

  Future<ApiResult<OilGasMasterSnapshot>> call() async {
    final fieldsRes = await _repository.listFields();
    if (fieldsRes is Failure<List<dynamic>>) {
      return ApiResult.failure(fieldsRes.errorHandler);
    }
    final refsRes = await _repository.listRefineries();
    if (refsRes is Failure<List<dynamic>>) {
      return ApiResult.failure(refsRes.errorHandler);
    }
    final facRes = await _repository.listFacilities();
    if (facRes is Failure<List<dynamic>>) {
      return ApiResult.failure(facRes.errorHandler);
    }
    return ApiResult.success(
      assembleMaster(
        fieldsRaw: (fieldsRes as Success<List<dynamic>>).data,
        refsRaw: (refsRes as Success<List<dynamic>>).data,
        facilitiesRaw: (facRes as Success<List<dynamic>>).data,
      ),
    );
  }
}
