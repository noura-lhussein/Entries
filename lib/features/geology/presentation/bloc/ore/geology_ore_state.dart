import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';

import '../geology_feedback.dart';

class GeologyOreState extends Equatable {
  const GeologyOreState({
    required this.date,
    this.publish = true,
    this.loading = false,
    this.saving = false,
    this.downloading = false,
    this.importing = false,
    this.loadError,
    this.reportDetail,
    this.reportApplyToken = 0,
    this.downloadedFile,
    this.downloadFallbackName = 'geology_ore_template.xlsx',
    this.feedback,
  });

  factory GeologyOreState.initial() => GeologyOreState(date: DateTime.now());

  final DateTime date;
  final bool publish;
  final bool loading;
  final bool saving;
  final bool downloading;
  final bool importing;
  final String? loadError;
  final Map<String, dynamic>? reportDetail;
  final int reportApplyToken;
  final Response<List<int>>? downloadedFile;
  final String downloadFallbackName;
  final GeologyFeedback? feedback;

  int get planYear => date.year;

  GeologyOreState copyWith({
    DateTime? date,
    bool? publish,
    bool? loading,
    bool? saving,
    bool? downloading,
    bool? importing,
    String? loadError,
    bool clearLoadError = false,
    Map<String, dynamic>? reportDetail,
    int? reportApplyToken,
    Response<List<int>>? downloadedFile,
    bool clearDownloadedFile = false,
    String? downloadFallbackName,
    GeologyFeedback? feedback,
  }) {
    return GeologyOreState(
      date: date ?? this.date,
      publish: publish ?? this.publish,
      loading: loading ?? this.loading,
      saving: saving ?? this.saving,
      downloading: downloading ?? this.downloading,
      importing: importing ?? this.importing,
      loadError: clearLoadError ? loadError : (loadError ?? this.loadError),
      reportDetail: reportDetail ?? this.reportDetail,
      reportApplyToken: reportApplyToken ?? this.reportApplyToken,
      downloadedFile: clearDownloadedFile
          ? downloadedFile
          : (downloadedFile ?? this.downloadedFile),
      downloadFallbackName: downloadFallbackName ?? this.downloadFallbackName,
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
        reportDetail,
        reportApplyToken,
        downloadedFile,
        downloadFallbackName,
        feedback,
      ];
}
