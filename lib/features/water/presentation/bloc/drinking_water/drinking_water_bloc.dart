import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../data/mappers/drinking_water_payload_mapper.dart';
import '../../../domain/usecases/water_drinking_usecases.dart';
import '../../../domain/usecases/water_files_usecases.dart';
import '../water_feedback.dart';
import 'drinking_water_event.dart';
import 'drinking_water_state.dart';

class DrinkingWaterBloc extends Bloc<DrinkingWaterEvent, DrinkingWaterState> {
  DrinkingWaterBloc({
    required GetWaterImportStatusUseCase getImportStatus,
    required GetDrinkingWaterStationUseCase getStation,
    required SaveDrinkingWaterStationUseCase saveStation,
    required ImportDrinkingWaterGeoUseCase importGeo,
    required ImportDrinkingWaterSurveyUseCase importSurvey,
  })  : _getImportStatus = getImportStatus,
        _getStation = getStation,
        _saveStation = saveStation,
        _importGeo = importGeo,
        _importSurvey = importSurvey,
        super(DrinkingWaterState.initial()) {
    on<DrinkingWaterStarted>(_onStarted);
    on<DrinkingWaterDailyModeToggled>(_onDailyToggled);
    on<DrinkingWaterImportSurveyToggled>(_onImportSurveyToggled);
    on<DrinkingWaterDateChanged>(_onDateChanged);
    on<DrinkingWaterStationSelected>(_onStationSelected);
    on<DrinkingWaterEnsureSelection>(_onEnsureSelection);
    on<DrinkingWaterFieldChanged>(_onFieldChanged);
    on<DrinkingWaterSaveRequested>(_onSave);
    on<DrinkingWaterImportRequested>(_onImport);
  }

  final GetWaterImportStatusUseCase _getImportStatus;
  final GetDrinkingWaterStationUseCase _getStation;
  final SaveDrinkingWaterStationUseCase _saveStation;
  final ImportDrinkingWaterGeoUseCase _importGeo;
  final ImportDrinkingWaterSurveyUseCase _importSurvey;

  Future<void> _onStarted(
    DrinkingWaterStarted event,
    Emitter<DrinkingWaterState> emit,
  ) {
    return _loadImportStatus(emit);
  }

  void _onDailyToggled(
    DrinkingWaterDailyModeToggled event,
    Emitter<DrinkingWaterState> emit,
  ) {
    emit(state.copyWith(isDaily: event.isDaily));
  }

  void _onImportSurveyToggled(
    DrinkingWaterImportSurveyToggled event,
    Emitter<DrinkingWaterState> emit,
  ) {
    emit(state.copyWith(importSurvey: event.importSurvey));
  }

  void _onDateChanged(
    DrinkingWaterDateChanged event,
    Emitter<DrinkingWaterState> emit,
  ) {
    emit(state.copyWith(registrationDate: event.date));
  }

  void _onStationSelected(
    DrinkingWaterStationSelected event,
    Emitter<DrinkingWaterState> emit,
  ) {
    emit(state.copyWith(selectedStation: event.station));
  }

  void _onEnsureSelection(
    DrinkingWaterEnsureSelection event,
    Emitter<DrinkingWaterState> emit,
  ) {
    if (state.selectedStation != null || event.stations.isEmpty) return;
    emit(state.copyWith(selectedStation: event.stations.first));
  }

  void _onFieldChanged(
    DrinkingWaterFieldChanged event,
    Emitter<DrinkingWaterState> emit,
  ) {
    final next = Map<String, String>.from(state.values);
    next[event.key] = event.value;
    emit(state.copyWith(values: next));
  }

  Future<void> _onSave(
    DrinkingWaterSaveRequested event,
    Emitter<DrinkingWaterState> emit,
  ) async {
    final station = state.selectedStation;
    if (station == null) {
      emit(state.copyWith(
        feedback: WaterFeedback(
          message: 'اختر محطة مياه الشرب أولاً',
          isSuccess: false,
        ),
      ));
      return;
    }

    emit(state.copyWith(isBusy: true));
    final stationRes = await _getStation(station.id);
    Map<String, dynamic>? payload;
    var fetchFailed = false;
    stationRes.when(
      success: (data) => payload = data,
      failure: (e) {
        fetchFailed = true;
        payload = null;
        emit(state.copyWith(
          isBusy: false,
          feedback: WaterFeedback(
            message: e.apiErrorModel.message ?? 'فشل جلب بيانات المحطة',
            isSuccess: false,
          ),
        ));
      },
    );

    if (fetchFailed || payload == null) {
      if (!fetchFailed) emit(state.copyWith(isBusy: false));
      return;
    }

    applyFormToPayload(
      payload!,
      stationId: station.id,
      registrationDate: state.registrationDate,
      orgUnit: event.orgUnit.trim(),
      values: state.values,
      notOperatingReason: event.notOperatingReason,
    );

    final saveRes = await _saveStation(payload: payload!);
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        saveRes,
        successFallback: 'تم حفظ بيانات محطة مياه الشرب بنجاح',
        failureFallback: 'فشل حفظ بيانات محطة مياه الشرب',
      ),
    ));
  }

  Future<void> _onImport(
    DrinkingWaterImportRequested event,
    Emitter<DrinkingWaterState> emit,
  ) async {
    if (event.files.isEmpty) return;
    emit(state.copyWith(isBusy: true));
    final result = state.importSurvey
        ? await _importSurvey(files: event.files)
        : await _importGeo(files: event.files, clear: false);
    final feedback = feedbackFromImportResult(
      result,
      successFallback: 'تم استيراد بيانات مياه الشرب بنجاح',
      failureFallback: 'فشل استيراد بيانات مياه الشرب',
    );
    emit(state.copyWith(isBusy: false, feedback: feedback));
    if (feedback.isSuccess) await _loadImportStatus(emit);
  }

  Future<void> _loadImportStatus(Emitter<DrinkingWaterState> emit) async {
    final result = await _getImportStatus();
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(importStatus: result.data));
    }
  }
}
