import 'package:dio/dio.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../../../core/network/user_facing_error.dart';
import '../../../domain/usecases/oil_gas_files_usecases.dart';
import '../../../domain/usecases/oil_gas_report_usecases.dart';
import '../../../domain/utils/parse_oil_gas_number.dart';
import '../../widgets/models/petroleum_data.dart';
import '../petroleum_feedback.dart';
import 'spc_report_event.dart';
import 'spc_report_state.dart';

class SpcReportBloc extends Bloc<SpcReportEvent, SpcReportState> {
  SpcReportBloc({
    required GetOilGasReportDatesUseCase getReportDates,
    required GetOilGasReportDetailUseCase getReportDetail,
    required UpsertOilGasReportUseCase upsertReport,
    required DownloadOilGasExecutiveTemplateUseCase downloadTemplate,
    required ImportOilGasExecutiveReportUseCase importReport,
  })  : _getReportDates = getReportDates,
        _getReportDetail = getReportDetail,
        _upsertReport = upsertReport,
        _downloadTemplate = downloadTemplate,
        _importReport = importReport,
        super(SpcReportState.initial()) {
    on<SpcReportStarted>(_onStarted);
    on<SpcReportDateChanged>(_onDateChanged);
    on<SpcReportPublishToggled>(
      (e, emit) => emit(state.copyWith(publish: e.value)),
    );
    on<SpcReportLoadRequested>(_onLoadReport);
    on<SpcReportSaveRequested>(_onSave);
    on<SpcReportDownloadTemplateRequested>(_onDownload);
    on<SpcReportImportRequested>(_onImport);
  }

  final GetOilGasReportDatesUseCase _getReportDates;
  final GetOilGasReportDetailUseCase _getReportDetail;
  final UpsertOilGasReportUseCase _upsertReport;
  final DownloadOilGasExecutiveTemplateUseCase _downloadTemplate;
  final ImportOilGasExecutiveReportUseCase _importReport;

  Future<void> _onStarted(
    SpcReportStarted event,
    Emitter<SpcReportState> emit,
  ) async {
    emit(state.copyWith(loading: true));
    final datesRes = await _getReportDates();
    if (datesRes is Success<List<dynamic>>) {
      final dates = datesRes.data
          .map((e) => e.toString())
          .where((e) => e.isNotEmpty)
          .toList();
      DateTime date = state.date;
      if (dates.isNotEmpty) {
        final parsed = DateTime.tryParse(dates.first);
        if (parsed != null) date = parsed;
      }
      emit(state.copyWith(reportDates: dates, date: date));
    }
    await _loadReport(emit);
  }

  Future<void> _onDateChanged(
    SpcReportDateChanged event,
    Emitter<SpcReportState> emit,
  ) async {
    emit(state.copyWith(date: event.date));
    await _loadReport(emit);
  }

  Future<void> _onLoadReport(
    SpcReportLoadRequested event,
    Emitter<SpcReportState> emit,
  ) {
    return _loadReport(emit);
  }

  Future<void> _loadReport(Emitter<SpcReportState> emit) async {
    emit(state.copyWith(loading: true, clearLoadError: true, loadError: null));
    final result = await _getReportDetail(oilGasIsoDate(state.date));
    if (result is Success<Map<String, dynamic>>) {
      final detail = result.data;
      final status = detail['status']?.toString();
      emit(state.copyWith(
        loading: false,
        reportDetail: detail,
        reportApplyToken: state.reportApplyToken + 1,
        publish: status != null ? status == 'published' : state.publish,
        loadError: null,
        clearLoadError: true,
      ));
    } else if (result is Failure<Map<String, dynamic>>) {
      emit(state.copyWith(
        loading: false,
        loadError: userFacingErrorMessage(
          result.errorHandler,
          fallback: 'تعذر تحميل التقرير اليومي لهذا التاريخ',
        ),
        clearLoadError: true,
      ));
    } else {
      emit(state.copyWith(loading: false));
    }
  }

  Future<void> _onSave(
    SpcReportSaveRequested event,
    Emitter<SpcReportState> emit,
  ) async {
    emit(state.copyWith(saving: true));
    final metrics = <Map<String, dynamic>>[];
    for (final r in kSpcRows) {
      final v = parseOilGasNumber(event.metricTexts[r.key] ?? '');
      if (v != null) {
        metrics.add({
          'metric_key': r.key,
          'dimension': '',
          'value': v,
          'unit': r.unit,
        });
      }
    }
    final result = await _upsertReport({
      'report_date': oilGasIsoDate(state.date),
      'status': state.publish ? 'published' : 'draft',
      'notes_ar': event.notesAr.trim(),
      'notes_en': '',
      'metrics': metrics,
    });
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(
        saving: false,
        feedback: PetroleumFeedback(
          message: 'تم حفظ التقرير اليومي بنجاح',
          isSuccess: true,
        ),
      ));
    } else if (result is Failure<Map<String, dynamic>>) {
      emit(state.copyWith(
        saving: false,
        feedback: PetroleumFeedback(
          message: userFacingErrorMessage(
            result.errorHandler,
            fallback: 'فشل حفظ التقرير اليومي',
          ),
          isSuccess: false,
        ),
      ));
    } else {
      emit(state.copyWith(saving: false));
    }
  }

  Future<void> _onDownload(
    SpcReportDownloadTemplateRequested event,
    Emitter<SpcReportState> emit,
  ) async {
    emit(state.copyWith(downloading: true, clearDownloadedFile: true));
    final result =
        await _downloadTemplate(date: oilGasIsoDate(state.date));
    if (result is Success<Response<List<int>>>) {
      final bytes = result.data.data;
      if (bytes == null || bytes.isEmpty) {
        emit(state.copyWith(
          downloading: false,
          feedback: PetroleumFeedback(
            message: 'تعذر تنزيل قالب Excel',
            isSuccess: false,
            floating: false,
          ),
        ));
        return;
      }
      emit(state.copyWith(
        downloading: false,
        downloadedFile: result.data,
        clearDownloadedFile: true,
      ));
    } else {
      emit(state.copyWith(
        downloading: false,
        feedback: PetroleumFeedback(
          message: 'تعذر تنزيل قالب Excel',
          isSuccess: false,
          floating: false,
        ),
      ));
    }
  }

  Future<void> _onImport(
    SpcReportImportRequested event,
    Emitter<SpcReportState> emit,
  ) async {
    emit(state.copyWith(importing: true));
    final result =
        await _importReport(event.file, publish: state.publish);
    if (result is Success<Map<String, dynamic>>) {
      final dateStr = result.data['report_date']?.toString();
      final parsed = dateStr == null ? null : DateTime.tryParse(dateStr);
      if (parsed != null) {
        emit(state.copyWith(date: parsed));
      }
      await _loadReport(emit);
      emit(state.copyWith(
        importing: false,
        feedback: PetroleumFeedback(
          message: 'تم استيراد التقرير من Excel بنجاح.',
          isSuccess: true,
          floating: false,
        ),
      ));
    } else {
      emit(state.copyWith(
        importing: false,
        feedback: PetroleumFeedback(
          message: 'تعذر استيراد ملف Excel. تحقق من القالب والقيم.',
          isSuccess: false,
          floating: false,
        ),
      ));
    }
  }
}
