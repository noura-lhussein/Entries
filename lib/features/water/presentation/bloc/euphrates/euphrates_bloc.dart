import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../data/mappers/euphrates_daily_payload_mapper.dart';
import '../../../domain/entities/water_import_result_entity.dart';
import '../../../domain/usecases/water_euphrates_usecases.dart';
import '../../../domain/usecases/water_files_usecases.dart';
import '../water_feedback.dart';
import 'euphrates_event.dart';
import 'euphrates_state.dart';

class EuphratesBloc extends Bloc<EuphratesEvent, EuphratesState> {
  EuphratesBloc({
    required GetWaterImportStatusUseCase getImportStatus,
    required GetEuphratesDailyUseCase getEuphratesDaily,
    required SaveEuphratesDailyUseCase saveEuphratesDaily,
    required ImportEuphratesUseCase importEuphrates,
    required ClearEuphratesUseCase clearEuphrates,
  })  : _getImportStatus = getImportStatus,
        _getEuphratesDaily = getEuphratesDaily,
        _saveEuphratesDaily = saveEuphratesDaily,
        _importEuphrates = importEuphrates,
        _clearEuphrates = clearEuphrates,
        super(EuphratesState.initial()) {
    on<EuphratesStarted>(_onStarted);
    on<EuphratesDailyModeToggled>(_onDailyToggled);
    on<EuphratesDateChanged>(_onDateChanged);
    on<EuphratesSaveRequested>(_onSave);
    on<EuphratesImportRequested>(_onImport);
    on<EuphratesClearRequested>(_onClear);
  }

  final GetWaterImportStatusUseCase _getImportStatus;
  final GetEuphratesDailyUseCase _getEuphratesDaily;
  final SaveEuphratesDailyUseCase _saveEuphratesDaily;
  final ImportEuphratesUseCase _importEuphrates;
  final ClearEuphratesUseCase _clearEuphrates;

  Future<void> _onStarted(
    EuphratesStarted event,
    Emitter<EuphratesState> emit,
  ) async {
    await _loadImportStatus(emit);
    await _loadDaily(emit, state.date);
  }

  void _onDailyToggled(
    EuphratesDailyModeToggled event,
    Emitter<EuphratesState> emit,
  ) {
    emit(state.copyWith(isDaily: event.isDaily));
  }

  Future<void> _onDateChanged(
    EuphratesDateChanged event,
    Emitter<EuphratesState> emit,
  ) async {
    emit(state.copyWith(date: event.date));
    await _loadDaily(emit, event.date);
  }

  Future<void> _onSave(
    EuphratesSaveRequested event,
    Emitter<EuphratesState> emit,
  ) async {
    emit(state.copyWith(isBusy: true));
    final result = await _saveEuphratesDaily(
      payload: EuphratesDailyPayloadMapper.fromForm(
        date: state.date,
        reportLabel: event.reportLabel,
        tishreenInflow: event.tishreenInflow,
        tishreenLevel: event.tishreenLevel,
        tishreenStorage: event.tishreenStorage,
        tishreenGeneration: event.tishreenGeneration,
        furatLevel: event.furatLevel,
        furatStorage: event.furatStorage,
        furatGeneration: event.furatGeneration,
        kadiranGeneration: event.kadiranGeneration,
        totalGeneration: event.totalGeneration,
      ),
    );
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        result,
        successFallback: 'تم حفظ بيانات الوارد المائي بنجاح',
        failureFallback: 'فشل حفظ بيانات الوارد المائي',
      ),
    ));
  }

  Future<void> _onImport(
    EuphratesImportRequested event,
    Emitter<EuphratesState> emit,
  ) async {
    if (event.files.isEmpty) return;
    emit(state.copyWith(isBusy: true));
    final result = await _importEuphrates(files: event.files, clear: false);
    emit(state.copyWith(
      isBusy: false,
      feedback: feedbackFromImportResult(
        result,
        successFallback: 'تم استيراد بيانات الوارد المائي بنجاح',
        failureFallback: 'فشل استيراد بيانات الوارد المائي',
      ),
    ));
  }

  Future<void> _onClear(
    EuphratesClearRequested event,
    Emitter<EuphratesState> emit,
  ) async {
    final result = await _clearEuphrates();
    emit(state.copyWith(feedback: feedbackFromClearResult(result)));
    final ok = result is Success<WaterImportResultEntity> && result.data.ok;
    if (ok) await _loadImportStatus(emit);
  }

  Future<void> _loadImportStatus(Emitter<EuphratesState> emit) async {
    final result = await _getImportStatus();
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(importStatus: result.data));
    }
  }

  Future<void> _loadDaily(Emitter<EuphratesState> emit, DateTime date) async {
    final result = await _getEuphratesDaily(date);
    if (result is! Success<Map<String, dynamic>?>) return;
    emit(state.copyWith(reading: result.data, clearReading: true));
  }
}
