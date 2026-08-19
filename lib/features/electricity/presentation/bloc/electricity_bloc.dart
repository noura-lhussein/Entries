import 'dart:math';

import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/di/injection.dart';
import '../../data/datasources/electricity_remote_data_source.dart';
import 'electricity_event.dart';
import 'electricity_state.dart';

class ElectricityBloc extends Bloc<ElectricityEvent, ElectricityState> {
  ElectricityBloc({ElectricityRemoteDataSource? remote})
      : _remote = remote ?? getIt<ElectricityRemoteDataSource>(),
        super(ElectricityState.initial()) {
    on<ElectricityStarted>((event, emit) => emit(ElectricityState.initial()));
    on<DailyEntryToggled>(
      (event, emit) => emit(state.copyWith(isDailyEntry: event.isDailyEntry)),
    );
    on<ReportDateChanged>(
      (event, emit) => emit(state.copyWith(reportDate: event.date)),
    );
    on<PeakTimeChanged>(
      (event, emit) => emit(state.copyWith(peakTime: event.time)),
    );
    on<DynamicRowAdded>(_onRowAdded);
    on<DynamicRowRemoved>(_onRowRemoved);
    on<DynamicRowsReplaced>(_onRowsReplaced);
    on<PublishAfterSaveToggled>(
      (event, emit) => emit(state.copyWith(publishAfterSave: event.value)),
    );
    on<ReportSaveRequested>(_onSaveRequested);
  }

  final ElectricityRemoteDataSource _remote;

  DynamicRow _newRow([List<String> values = const []]) => DynamicRow(
        '${DateTime.now().microsecondsSinceEpoch}_${Random().nextInt(9999)}',
        values,
      );

  void _onRowAdded(DynamicRowAdded event, Emitter<ElectricityState> emit) {
    final newRow = _newRow();
    switch (event.section) {
      case DynamicSectionType.maintenance:
        emit(state.copyWith(
          maintenanceRows: [...state.maintenanceRows, newRow],
        ));
        break;
      case DynamicSectionType.generationIncidents:
        emit(state.copyWith(
          generationIncidentRows: [...state.generationIncidentRows, newRow],
        ));
        break;
      case DynamicSectionType.lineIncidents:
        emit(state.copyWith(
          lineIncidentRows: [...state.lineIncidentRows, newRow],
        ));
        break;
    }
  }

  void _onRowRemoved(DynamicRowRemoved event, Emitter<ElectricityState> emit) {
    switch (event.section) {
      case DynamicSectionType.maintenance:
        emit(state.copyWith(
          maintenanceRows: state.maintenanceRows
              .where((r) => r.id != event.rowId)
              .toList(),
        ));
        break;
      case DynamicSectionType.generationIncidents:
        emit(state.copyWith(
          generationIncidentRows: state.generationIncidentRows
              .where((r) => r.id != event.rowId)
              .toList(),
        ));
        break;
      case DynamicSectionType.lineIncidents:
        emit(state.copyWith(
          lineIncidentRows:
              state.lineIncidentRows.where((r) => r.id != event.rowId).toList(),
        ));
        break;
    }
  }

  void _onRowsReplaced(
    DynamicRowsReplaced event,
    Emitter<ElectricityState> emit,
  ) {
    switch (event.section) {
      case DynamicSectionType.maintenance:
        emit(state.copyWith(maintenanceRows: event.rows));
        break;
      case DynamicSectionType.generationIncidents:
        emit(state.copyWith(generationIncidentRows: event.rows));
        break;
      case DynamicSectionType.lineIncidents:
        emit(state.copyWith(lineIncidentRows: event.rows));
        break;
    }
  }

  Future<void> _onSaveRequested(
    ReportSaveRequested event,
    Emitter<ElectricityState> emit,
  ) async {
    emit(state.copyWith(saveStatus: SaveStatus.saving));
    try {
      await _remote.upsertDailyReport(event.payload);
      emit(state.copyWith(saveStatus: SaveStatus.success));
    } catch (_) {
      emit(state.copyWith(saveStatus: SaveStatus.failure));
    }
  }
}
