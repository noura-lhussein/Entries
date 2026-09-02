import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../../../core/network/user_facing_error.dart';
import '../../../domain/services/oil_gas_master_parser.dart';
import '../../../domain/usecases/oil_gas_master_usecases.dart';
import '../../../domain/usecases/oil_gas_operations_usecases.dart';
import '../../../domain/utils/parse_oil_gas_number.dart';
import '../petroleum_feedback.dart';
import 'petroleum_ops_event.dart';
import 'petroleum_ops_state.dart';

class PetroleumOpsBloc extends Bloc<PetroleumOpsEvent, PetroleumOpsState> {
  PetroleumOpsBloc({
    required LoadOilGasMasterUseCase loadMaster,
    required UpsertOilGasOperationsUseCase upsertOperations,
    required PublishOilGasDayUseCase publishDay,
  })  : _loadMaster = loadMaster,
        _upsertOperations = upsertOperations,
        _publishDay = publishDay,
        super(PetroleumOpsState.initial()) {
    on<PetroleumOpsStarted>(_onStarted);
    on<PetroleumOpsDateChanged>(
      (e, emit) => emit(state.copyWith(date: e.date)),
    );
    on<PetroleumOpsPublishToggled>(
      (e, emit) => emit(state.copyWith(publish: e.value)),
    );
    on<PetroleumOpsSaveRequested>(_onSave);
  }

  final LoadOilGasMasterUseCase _loadMaster;
  final UpsertOilGasOperationsUseCase _upsertOperations;
  final PublishOilGasDayUseCase _publishDay;

  Future<void> _onStarted(
    PetroleumOpsStarted event,
    Emitter<PetroleumOpsState> emit,
  ) async {
    emit(state.copyWith(masterLoading: true, clearMasterError: true, masterError: null));
    final result = await _loadMaster();
    if (result is Failure<OilGasMasterSnapshot>) {
      emit(state.copyWith(
        masterLoading: false,
        fields: const [],
        refineries: const [],
        powerFacilities: const {},
        depots: const [],
        masterError: userFacingErrorMessage(
          result.errorHandler,
          fallback: 'تعذر تحميل بيانات الحقول والمصافي',
        ),
        clearMasterError: true,
      ));
      return;
    }
    final snap = (result as Success<OilGasMasterSnapshot>).data;
    String? warning;
    if (snap.fields.isEmpty && snap.refineries.isEmpty) {
      warning = 'لم يُرجع الخادم حقولاً أو مصافٍ. تحقق من بيانات السجل.';
    }
    emit(state.copyWith(
      masterLoading: false,
      fields: snap.fields,
      refineries: snap.refineries,
      powerFacilities: snap.powerFacilities,
      depots: snap.depots,
      masterError: warning,
      clearMasterError: true,
    ));
  }

  Future<void> _onSave(
    PetroleumOpsSaveRequested event,
    Emitter<PetroleumOpsState> emit,
  ) async {
    final production = <Map<String, dynamic>>[];
    for (final f in state.fields) {
      final oil = parseOilGasNumber(event.oilTexts[f.code] ?? '');
      final gas = parseOilGasNumber(event.gasTexts[f.code] ?? '');
      if (oil != null || gas != null) {
        production.add({
          'field_code': f.code,
          'crude_oil_bbl': oil ?? 0,
          'natural_gas_mmscf': gas ?? 0,
        });
      }
    }

    final refineryOutputs = <Map<String, dynamic>>[];
    for (final r in state.refineries) {
      final gasoline = parseOilGasNumber(event.refineryTexts['${r}_benzin'] ?? '');
      final diesel = parseOilGasNumber(event.refineryTexts['${r}_diesel'] ?? '');
      final fuel = parseOilGasNumber(event.refineryTexts['${r}_fuel'] ?? '');
      final lpg = parseOilGasNumber(event.refineryTexts['${r}_lpg'] ?? '');
      if (gasoline != null || diesel != null || fuel != null || lpg != null) {
        refineryOutputs.add({
          'refinery_name': r,
          'gasoline_ton': gasoline ?? 0,
          'diesel_ton': diesel ?? 0,
          'fuel_oil_ton': fuel ?? 0,
          'lpg_ton': lpg ?? 0,
        });
      }
    }

    if (production.isEmpty &&
        refineryOutputs.isEmpty &&
        event.inventory.isEmpty &&
        event.exports.isEmpty &&
        event.losses.isEmpty &&
        event.supply.isEmpty &&
        event.requirement.isEmpty) {
      emit(state.copyWith(
        feedback: PetroleumFeedback(
          message: 'لا توجد بيانات للحفظ',
          isSuccess: false,
        ),
      ));
      return;
    }

    emit(state.copyWith(saving: true));
    final payload = <String, dynamic>{
      'production_date': oilGasIsoDate(state.date),
      'publish': state.publish,
      if (production.isNotEmpty) 'production': production,
      if (refineryOutputs.isNotEmpty) 'refinery_outputs': refineryOutputs,
      if (event.inventory.isNotEmpty) 'inventory': event.inventory,
      if (event.exports.isNotEmpty) 'exports': event.exports,
      if (event.losses.isNotEmpty) 'losses': event.losses,
      if (event.supply.isNotEmpty) 'power_gas_supply': event.supply,
      if (event.requirement.isNotEmpty)
        'power_gas_requirement': event.requirement,
    };

    final upsert = await _upsertOperations(payload);
    if (upsert is Failure<Map<String, dynamic>>) {
      emit(state.copyWith(
        saving: false,
        feedback: PetroleumFeedback(
          message: userFacingErrorMessage(
            upsert.errorHandler,
            fallback: 'فشل حفظ البيانات التشغيلية',
          ),
          isSuccess: false,
        ),
      ));
      return;
    }

    if (state.publish) {
      final pub = await _publishDay(oilGasIsoDate(state.date));
      if (pub is Failure<Map<String, dynamic>>) {
        emit(state.copyWith(
          saving: false,
          feedback: PetroleumFeedback(
            message: userFacingErrorMessage(
              pub.errorHandler,
              fallback: 'فشل حفظ البيانات التشغيلية',
            ),
            isSuccess: false,
          ),
        ));
        return;
      }
    }

    emit(state.copyWith(
      saving: false,
      formResetToken: state.formResetToken + 1,
      feedback: PetroleumFeedback(
        message: state.publish
            ? 'تم حفظ ونشر البيانات التشغيلية بنجاح'
            : 'تم حفظ البيانات التشغيلية كمسودة',
        isSuccess: true,
      ),
    ));
  }
}
