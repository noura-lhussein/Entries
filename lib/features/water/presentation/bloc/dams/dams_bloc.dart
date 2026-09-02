import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../domain/entities/water_import_result_entity.dart';
import '../../../domain/usecases/water_dams_usecases.dart';
import '../../../domain/usecases/water_files_usecases.dart';
import '../../../domain/utils/parse_water_number.dart';
import '../water_feedback.dart';
import 'dams_event.dart';
import 'dams_state.dart';

class DamsBloc extends Bloc<DamsEvent, DamsState> {
  DamsBloc({
    required GetWaterImportStatusUseCase getImportStatus,
    required SaveDamDailyUseCase saveDamDaily,
    required ImportDamsUseCase importDams,
    required ClearDamStorageUseCase clearDamStorage,
  })  : _getImportStatus = getImportStatus,
        _saveDamDaily = saveDamDaily,
        _importDams = importDams,
        _clearDamStorage = clearDamStorage,
        super(DamsState.initial()) {
    on<DamsStarted>(_onStarted);
    on<DamsDailyModeToggled>(_onDailyToggled);
    on<DamsDateChanged>(_onDateChanged);
    on<DamsDamSelected>(_onDamSelected);
    on<DamsEnsureSelection>(_onEnsureSelection);
    on<DamsSaveRequested>(_onSave);
    on<DamsImportRequested>(_onImport);
    on<DamsClearRequested>(_onClear);
    on<DamsImportStatusRequested>(_onLoadImportStatus);
  }

  final GetWaterImportStatusUseCase _getImportStatus;
  final SaveDamDailyUseCase _saveDamDaily;
  final ImportDamsUseCase _importDams;
  final ClearDamStorageUseCase _clearDamStorage;

  Future<void> _onStarted(DamsStarted event, Emitter<DamsState> emit) {
    return _loadImportStatus(emit);
  }

  void _onDailyToggled(DamsDailyModeToggled event, Emitter<DamsState> emit) {
    emit(state.copyWith(isDaily: event.isDaily));
  }

  void _onDateChanged(DamsDateChanged event, Emitter<DamsState> emit) {
    emit(state.copyWith(date: event.date));
  }

  void _onDamSelected(DamsDamSelected event, Emitter<DamsState> emit) {
    emit(state.copyWith(selectedDam: event.dam));
  }

  void _onEnsureSelection(DamsEnsureSelection event, Emitter<DamsState> emit) {
    if (state.selectedDam != null || event.dams.isEmpty) return;
    emit(state.copyWith(selectedDam: event.dams.first));
  }

  Future<void> _onSave(DamsSaveRequested event, Emitter<DamsState> emit) async {
    final damId = state.selectedDam?.id;
    if (damId == null || damId == 0) {
      emit(state.copyWith(
        feedback: WaterFeedback(message: 'اختر السد أولاً', isSuccess: false),
      ));
      return;
    }

    emit(state.copyWith(isBusy: true));
    final result = await _saveDamDaily(
      readingDate: state.date,
      damId: damId,
      storageMcm: parseWaterNumber(event.storageText),
      notes: event.notes.trim(),
    );
    final feedback = feedbackFromImportResult(
      result,
      successFallback: 'تم حفظ بيانات السد بنجاح',
      failureFallback: 'فشل حفظ بيانات السد',
    );
    final ok = result is Success<WaterImportResultEntity> && result.data.ok;
    emit(state.copyWith(
      isBusy: false,
      feedback: feedback,
      formResetToken: ok ? state.formResetToken + 1 : state.formResetToken,
    ));
  }

  Future<void> _onImport(
    DamsImportRequested event,
    Emitter<DamsState> emit,
  ) async {
    if (event.files.isEmpty) return;
    emit(state.copyWith(isBusy: true));
    final result = await _importDams(files: event.files, clear: false);
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        result,
        successFallback: 'تم استيراد بيانات السدود بنجاح',
        failureFallback: 'فشل استيراد بيانات السدود',
      ),
    ));
  }

  Future<void> _onClear(
    DamsClearRequested event,
    Emitter<DamsState> emit,
  ) async {
    final result = await _clearDamStorage();
    emit(state.copyWith(feedback: feedbackFromClearResult(result)));
    final ok = result is Success<WaterImportResultEntity> && result.data.ok;
    if (ok) await _loadImportStatus(emit);
  }

  Future<void> _onLoadImportStatus(
    DamsImportStatusRequested event,
    Emitter<DamsState> emit,
  ) {
    return _loadImportStatus(emit);
  }

  Future<void> _loadImportStatus(Emitter<DamsState> emit) async {
    final result = await _getImportStatus();
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(importStatus: result.data));
    }
  }
}
