import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../domain/entities/water_import_result_entity.dart';
import '../../../domain/services/rainfall_station_resolver.dart';
import '../../../domain/usecases/water_files_usecases.dart';
import '../../../domain/usecases/water_rainfall_usecases.dart';
import '../../../domain/utils/parse_water_number.dart';
import '../water_feedback.dart';
import 'rainfall_event.dart';
import 'rainfall_state.dart';

class RainfallBloc extends Bloc<RainfallEvent, RainfallState> {
  RainfallBloc({
    required GetWaterImportStatusUseCase getImportStatus,
    required SaveRainfallDailyUseCase saveRainfallDaily,
    required ImportRainfallUseCase importRainfall,
    required ClearRainfallUseCase clearRainfall,
  })  : _getImportStatus = getImportStatus,
        _saveRainfallDaily = saveRainfallDaily,
        _importRainfall = importRainfall,
        _clearRainfall = clearRainfall,
        super(RainfallState.initial()) {
    on<RainfallStarted>(_onStarted);
    on<RainfallDailyModeToggled>(_onDailyToggled);
    on<RainfallDateChanged>(_onDateChanged);
    on<RainfallStationSelected>(_onStationSelected);
    on<RainfallSaveRequested>(_onSave);
    on<RainfallImportRequested>(_onImport);
    on<RainfallClearRequested>(_onClear);
  }

  final GetWaterImportStatusUseCase _getImportStatus;
  final SaveRainfallDailyUseCase _saveRainfallDaily;
  final ImportRainfallUseCase _importRainfall;
  final ClearRainfallUseCase _clearRainfall;

  Future<void> _onStarted(
    RainfallStarted event,
    Emitter<RainfallState> emit,
  ) {
    return _loadImportStatus(emit);
  }

  void _onDailyToggled(
    RainfallDailyModeToggled event,
    Emitter<RainfallState> emit,
  ) {
    emit(state.copyWith(isDaily: event.isDaily));
  }

  void _onDateChanged(RainfallDateChanged event, Emitter<RainfallState> emit) {
    emit(state.copyWith(date: event.date));
  }

  void _onStationSelected(
    RainfallStationSelected event,
    Emitter<RainfallState> emit,
  ) {
    final resolved = RainfallStationResolver.resolve(
      station: event.station,
      basins: event.basins,
      governorates: event.governorates,
    );
    emit(state.copyWith(
      selectedStation: event.station,
      selectedBasin: resolved.basin,
      selectedGov: resolved.governorate,
      replaceStationLookups: true,
    ));
  }

  Future<void> _onSave(
    RainfallSaveRequested event,
    Emitter<RainfallState> emit,
  ) async {
    final stationId = state.selectedStation?.id;
    final basinSlug =
        state.selectedStation?.basinSlug ?? state.selectedBasin?.slug ?? '';
    final governorate =
        state.selectedStation?.governorate ?? state.selectedGov?.slug ?? '';
    final stationName = state.selectedStation?.name ?? '';

    if (stationId == null || stationId == 0 || stationName.isEmpty) {
      emit(state.copyWith(
        feedback: WaterFeedback(message: 'اختر المحطة', isSuccess: false),
      ));
      return;
    }

    emit(state.copyWith(isBusy: true));
    final result = await _saveRainfallDaily(
      observationDate: state.date,
      basinSlug: basinSlug,
      stationName: stationName,
      governorate: governorate,
      precipitationMm: parseWaterNumber(event.precipitationText),
      notes: event.notes.trim(),
      stationId: stationId,
    );
    final ok = result is Success<WaterImportResultEntity> && result.data.ok;
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        result,
        successFallback: 'تم حفظ بيانات الهطول بنجاح',
        failureFallback: 'فشل حفظ بيانات الهطول',
      ),
      formResetToken: ok ? state.formResetToken + 1 : state.formResetToken,
    ));
  }

  Future<void> _onImport(
    RainfallImportRequested event,
    Emitter<RainfallState> emit,
  ) async {
    if (event.files.isEmpty) return;
    emit(state.copyWith(isBusy: true));
    final result = await _importRainfall(files: event.files, clear: false);
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        result,
        successFallback: 'تم استيراد بيانات الهطول بنجاح',
        failureFallback: 'فشل استيراد بيانات الهطول',
      ),
    ));
  }

  Future<void> _onClear(
    RainfallClearRequested event,
    Emitter<RainfallState> emit,
  ) async {
    final result = await _clearRainfall();
    emit(state.copyWith(feedback: feedbackFromClearResult(result)));
    final ok = result is Success<WaterImportResultEntity> && result.data.ok;
    if (ok) await _loadImportStatus(emit);
  }

  Future<void> _loadImportStatus(Emitter<RainfallState> emit) async {
    final result = await _getImportStatus();
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(importStatus: result.data));
    }
  }
}
