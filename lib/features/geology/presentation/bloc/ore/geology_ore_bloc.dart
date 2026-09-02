import 'package:dio/dio.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/network/api_result.dart';
import '../../../../../core/network/user_facing_error.dart';
import '../../../domain/usecases/geology_files_usecases.dart';
import '../../../domain/usecases/geology_report_usecases.dart';
import '../../../domain/utils/parse_geology_number.dart';
import '../geology_feedback.dart';
import 'geology_ore_event.dart';
import 'geology_ore_state.dart';

class GeologyOreBloc extends Bloc<GeologyOreEvent, GeologyOreState> {
  GeologyOreBloc({
    required GetGeologyDailyReportUseCase getDailyReport,
    required SaveGeologyDailyReportUseCase saveDailyReport,
    required DownloadGeologyOreTemplateUseCase downloadTemplate,
    required ExportGeologyOreProductionUseCase exportProduction,
    required ImportGeologyOreProductionUseCase importProduction,
  })  : _getDailyReport = getDailyReport,
        _saveDailyReport = saveDailyReport,
        _downloadTemplate = downloadTemplate,
        _exportProduction = exportProduction,
        _importProduction = importProduction,
        super(GeologyOreState.initial()) {
    on<GeologyOreStarted>(_onStarted);
    on<GeologyOreDateChanged>(_onDateChanged);
    on<GeologyOrePublishToggled>(
      (e, emit) => emit(state.copyWith(publish: e.value)),
    );
    on<GeologyOreLoadRequested>(_onLoad);
    on<GeologyOreSaveRequested>(_onSave);
    on<GeologyOreDownloadTemplateRequested>(_onDownloadTemplate);
    on<GeologyOreExportRequested>(_onExport);
    on<GeologyOreImportRequested>(_onImport);
  }

  final GetGeologyDailyReportUseCase _getDailyReport;
  final SaveGeologyDailyReportUseCase _saveDailyReport;
  final DownloadGeologyOreTemplateUseCase _downloadTemplate;
  final ExportGeologyOreProductionUseCase _exportProduction;
  final ImportGeologyOreProductionUseCase _importProduction;

  Future<void> _onStarted(
    GeologyOreStarted event,
    Emitter<GeologyOreState> emit,
  ) {
    return _loadReport(emit);
  }

  Future<void> _onDateChanged(
    GeologyOreDateChanged event,
    Emitter<GeologyOreState> emit,
  ) async {
    emit(state.copyWith(date: event.date));
    await _loadReport(emit);
  }

  Future<void> _onLoad(
    GeologyOreLoadRequested event,
    Emitter<GeologyOreState> emit,
  ) {
    return _loadReport(emit);
  }

  Future<void> _loadReport(Emitter<GeologyOreState> emit) async {
    emit(state.copyWith(loading: true, clearLoadError: true, loadError: null));
    final result = await _getDailyReport(geologyIsoDate(state.date));
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(
        loading: false,
        reportDetail: result.data,
        reportApplyToken: state.reportApplyToken + 1,
        loadError: null,
        clearLoadError: true,
      ));
    } else if (result is Failure<Map<String, dynamic>>) {
      emit(state.copyWith(
        loading: false,
        loadError: userFacingErrorMessage(
          result.errorHandler,
          fallback: 'تعذر تحميل تقرير الخامات لهذا التاريخ',
        ),
        clearLoadError: true,
      ));
    } else {
      emit(state.copyWith(loading: false));
    }
  }

  Future<void> _onSave(
    GeologyOreSaveRequested event,
    Emitter<GeologyOreState> emit,
  ) async {
    if (event.rows.isEmpty) {
      emit(state.copyWith(
        feedback: GeologyFeedback(
          message: 'لا توجد بيانات للحفظ',
          isSuccess: false,
        ),
      ));
      return;
    }
    emit(state.copyWith(saving: true));
    final result = await _saveDailyReport({
      'report_date': geologyIsoDate(state.date),
      'plan_year': state.planYear,
      'publish': state.publish,
      'rows': event.rows,
    });
    if (result is Success<Map<String, dynamic>>) {
      emit(state.copyWith(
        saving: false,
        feedback: GeologyFeedback(
          message: 'تم حفظ تقرير الخامات بنجاح',
          isSuccess: true,
        ),
      ));
    } else if (result is Failure<Map<String, dynamic>>) {
      emit(state.copyWith(
        saving: false,
        feedback: GeologyFeedback(
          message: userFacingErrorMessage(
            result.errorHandler,
            fallback: 'فشل حفظ تقرير الخامات',
          ),
          isSuccess: false,
        ),
      ));
    } else {
      emit(state.copyWith(saving: false));
    }
  }

  Future<void> _onDownloadTemplate(
    GeologyOreDownloadTemplateRequested event,
    Emitter<GeologyOreState> emit,
  ) {
    return _openBytes(
      emit,
      () => _downloadTemplate(planYear: state.planYear),
      fallbackName: 'geology_ore_template.xlsx',
    );
  }

  Future<void> _onExport(
    GeologyOreExportRequested event,
    Emitter<GeologyOreState> emit,
  ) {
    return _openBytes(
      emit,
      () => _exportProduction(state.planYear),
      fallbackName: 'geology_ore_production.xlsx',
    );
  }

  Future<void> _openBytes(
    Emitter<GeologyOreState> emit,
    Future<ApiResult<Response<List<int>>>> Function() run, {
    required String fallbackName,
  }) async {
    emit(state.copyWith(downloading: true, clearDownloadedFile: true));
    final result = await run();
    if (result is Success<Response<List<int>>>) {
      final bytes = result.data.data;
      if (bytes == null || bytes.isEmpty) {
        emit(state.copyWith(
          downloading: false,
          feedback: GeologyFeedback(
            message: 'تعذر تنزيل ملف Excel',
            isSuccess: false,
            floating: false,
          ),
        ));
        return;
      }
      emit(state.copyWith(
        downloading: false,
        downloadedFile: result.data,
        downloadFallbackName: fallbackName,
        clearDownloadedFile: true,
      ));
    } else {
      emit(state.copyWith(
        downloading: false,
        feedback: GeologyFeedback(
          message: 'تعذر تنزيل ملف Excel',
          isSuccess: false,
          floating: false,
        ),
      ));
    }
  }

  Future<void> _onImport(
    GeologyOreImportRequested event,
    Emitter<GeologyOreState> emit,
  ) async {
    emit(state.copyWith(importing: true));
    final result =
        await _importProduction(event.file, publish: state.publish);
    if (result is Success<Map<String, dynamic>>) {
      final dateStr = result.data['report_date']?.toString();
      final parsed = dateStr == null ? null : DateTime.tryParse(dateStr);
      if (parsed != null) {
        emit(state.copyWith(date: parsed));
      }
      await _loadReport(emit);
      emit(state.copyWith(
        importing: false,
        feedback: GeologyFeedback(
          message: 'تم استيراد الإنتاج من Excel بنجاح.',
          isSuccess: true,
          floating: false,
        ),
      ));
    } else {
      emit(state.copyWith(
        importing: false,
        feedback: GeologyFeedback(
          message: 'تعذر استيراد ملف Excel. تحقق من القالب والقيم.',
          isSuccess: false,
          floating: false,
        ),
      ));
    }
  }
}
