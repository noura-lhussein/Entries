import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:open_filex/open_filex.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/api_result.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/water_import_result_entity.dart';
import '../../domain/repositories/water_repository.dart';

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

void _snack(BuildContext context, String msg, {bool ok = true}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(msg, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
      backgroundColor: ok ? AppColors.forest1 : AppColors.red2,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
    ),
  );
}

Future<void> downloadWaterTemplate(
  BuildContext context, {
  required String kind,
  String fallbackName = 'template.xlsx',
}) async {
  final result = await getIt<WaterRepository>().downloadTemplate(kind);
  if (!context.mounted) return;
  if (result is Success<Response<List<int>>>) {
    final res = result.data;
    final bytes = res.data;
    if (bytes == null || bytes.isEmpty) {
      _snack(context, 'القالب فارغ', ok: false);
      return;
    }
    try {
      await saveAndOpenBytes(
        bytes,
        filename: _filenameFromResponse(res, fallbackName),
      );
      if (context.mounted) _snack(context, 'تم تنزيل القالب');
    } catch (_) {
      if (context.mounted) _snack(context, 'تعذر حفظ القالب', ok: false);
    }
  } else {
    _snack(context, 'فشل تنزيل القالب', ok: false);
  }
}

Future<void> exportDrinkingSurvey(BuildContext context) async {
  final result = await getIt<WaterRepository>().exportDrinkingWaterSurvey();
  if (!context.mounted) return;
  if (result is Success<Response<List<int>>>) {
    final res = result.data;
    final bytes = res.data;
    if (bytes == null || bytes.isEmpty) {
      _snack(context, 'لا توجد بيانات للتصدير', ok: false);
      return;
    }
    try {
      await saveAndOpenBytes(
        bytes,
        filename: _filenameFromResponse(res, 'drinking-water-survey.xlsx'),
      );
      if (context.mounted) _snack(context, 'تم التصدير');
    } catch (_) {
      if (context.mounted) _snack(context, 'تعذر حفظ الملف', ok: false);
    }
  } else {
    _snack(context, 'فشل التصدير', ok: false);
  }
}

Future<void> clearWaterImport(
  BuildContext context, {
  required Future<ApiResult<WaterImportResultEntity>> Function() clear,
  required Future<void> Function() onDone,
}) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('تأكيد المسح', style: TextStyle(fontFamily: 'Cairo')),
      content: const Text(
        'هل تريد مسح البيانات المستوردة لهذا القسم؟',
        style: TextStyle(fontFamily: 'Cairo'),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('إلغاء')),
        TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('مسح')),
      ],
    ),
  );
  if (ok != true || !context.mounted) return;

  final result = await clear();
  if (!context.mounted) return;
  if (result is Success<WaterImportResultEntity>) {
    final r = result.data;
    _snack(
      context,
      r.messageAr ?? (r.ok ? 'تم المسح' : 'فشل المسح'),
      ok: r.ok,
    );
    if (r.ok) await onDone();
  } else {
    _snack(context, 'فشل المسح', ok: false);
  }
}
