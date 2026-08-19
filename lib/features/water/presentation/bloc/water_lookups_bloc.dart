import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/usecases/get_water_lookups_use_case.dart';
import 'water_lookups_event.dart';
import 'water_lookups_state.dart';

class WaterLookupsBloc extends Bloc<WaterLookupsEvent, WaterLookupsState> {
  final GetWaterLookupsUseCase getWaterLookupsUseCase;

  WaterLookupsBloc({
    required this.getWaterLookupsUseCase,
  }) : super(WaterLookupsInitial()) {
    on<GetWaterLookupsStarted>(_onGetWaterLookupsStarted);
  }

  Future<void> _onGetWaterLookupsStarted(
    GetWaterLookupsStarted event,
    Emitter<WaterLookupsState> emit,
  ) async {
    emit(WaterLookupsLoading());

    final result = await getWaterLookupsUseCase();

    result.when(
      success: (lookups) {
        emit(WaterLookupsLoaded(lookups: lookups));
      },
      failure: (error) {
        emit(WaterLookupsError(
          message: error.apiErrorModel.message ?? 'فشل تحميل البيانات المساعدة',
        ));
      },
    );
  }
}
