import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/api_result.dart';
import '../../domain/usecases/water_files_usecases.dart';
import 'water_snack.dart';

Future<void> saveAndOpenBytes(
  List<int> bytes, {
  required String filename,
}) async {
  final path = '${Directory.systemTemp.path}${Platform.pathSeparator}$filename';
  final file = File(path);
  await file.writeAsBytes(bytes, flush: true);
  await OpenFilex.open(path);
}

String _filenameFromResponse(Response<List<int>> res, String fallback) {
  final cd = res.headers.value('content-disposition') ?? '';
  final match = RegExp(r'filename[^;=\n]*=[\s"]*([^";\n]+)').firstMatch(cd);
  if (match != null) return match.group(1)!.trim();
  return fallback;
}

Future<void> downloadWaterTemplate(
  BuildContext context, {
  required String kind,
  String fallbackName = 'template.xlsx',
}) async {
  final result = await getIt<DownloadWaterTemplateUseCase>().call(kind);
  if (!context.mounted) return;
  if (result is Success<Response<List<int>>>) {
    final res = result.data;
    final bytes = res.data;
    if (bytes == null || bytes.isEmpty) {
      showWaterSnack(context, 'القالب فارغ', ok: false);
      return;
    }
    try {
      await saveAndOpenBytes(
        bytes,
        filename: _filenameFromResponse(res, fallbackName),
      );
      if (context.mounted) showWaterSnack(context, 'تم تنزيل القالب');
    } catch (_) {
      if (context.mounted) showWaterSnack(context, 'تعذر حفظ القالب', ok: false);
    }
  } else {
    showWaterSnack(context, 'فشل تنزيل القالب', ok: false);
  }
}

Future<void> exportDrinkingSurvey(BuildContext context) async {
  final result = await getIt<ExportDrinkingWaterSurveyUseCase>().call();
  if (!context.mounted) return;
  if (result is Success<Response<List<int>>>) {
    final res = result.data;
    final bytes = res.data;
    if (bytes == null || bytes.isEmpty) {
      showWaterSnack(context, 'لا توجد بيانات للتصدير', ok: false);
      return;
    }
    try {
      await saveAndOpenBytes(
        bytes,
        filename: _filenameFromResponse(res, 'drinking-water-survey.xlsx'),
      );
      if (context.mounted) showWaterSnack(context, 'تم التصدير');
    } catch (_) {
      if (context.mounted) showWaterSnack(context, 'تعذر حفظ الملف', ok: false);
    }
  } else {
    showWaterSnack(context, 'فشل التصدير', ok: false);
  }
}
