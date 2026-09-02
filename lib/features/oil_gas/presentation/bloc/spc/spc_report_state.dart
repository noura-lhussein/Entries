import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';

import '../petroleum_feedback.dart';

class SpcReportState extends Equatable {
  const SpcReportState({
    required this.date,
    this.publish = true,
    this.loading = false,
    this.saving = false,
    this.downloading = false,
    this.importing = false,
    this.loadError,
    this.reportDates = const [],
    this.reportDetail,
    this.reportApplyToken = 0,
    this.downloadedFile,
    this.feedback,
  });

  factory SpcReportState.initial() => SpcReportState(date: DateTime.now());

  final DateTime date;
  final bool publish;
  final bool loading;
  final bool saving;
  final bool downloading;
  final bool importing;
  final String? loadError;
  final List<String> reportDates;
  final Map<String, dynamic>? reportDetail;
  final int reportApplyToken;
  final Response<List<int>>? downloadedFile;
  final PetroleumFeedback? feedback;

  SpcReportState copyWith({
    DateTime? date,
    bool? publish,
    bool? loading,
    bool? saving,
    bool? downloading,
    bool? importing,
    String? loadError,
    bool clearLoadError = false,
    List<String>? reportDates,
    Map<String, dynamic>? reportDetail,
    int? reportApplyToken,
    Response<List<int>>? downloadedFile,
    bool clearDownloadedFile = false,
    PetroleumFeedback? feedback,
  }) {
    return SpcReportState(
      date: date ?? this.date,
      publish: publish ?? this.publish,
      loading: loading ?? this.loading,
      saving: saving ?? this.saving,
      downloading: downloading ?? this.downloading,
      importing: importing ?? this.importing,
      loadError: clearLoadError ? loadError : (loadError ?? this.loadError),
      reportDates: reportDates ?? this.reportDates,
      reportDetail: reportDetail ?? this.reportDetail,
      reportApplyToken: reportApplyToken ?? this.reportApplyToken,
      downloadedFile: clearDownloadedFile
          ? downloadedFile
          : (downloadedFile ?? this.downloadedFile),
      feedback: feedback ?? this.feedback,
    );
  }

  @override
  List<Object?> get props => [
        date,
        publish,
        loading,
        saving,
        downloading,
        importing,
        loadError,
        reportDates,
        reportDetail,
        reportApplyToken,
        downloadedFile,
        feedback,
      ];
}
