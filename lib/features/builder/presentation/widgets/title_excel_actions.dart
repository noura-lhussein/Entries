import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/open_downloaded_file.dart';
import '../../data/datasources/builder_remote_data_source.dart';
import '../../data/models/builder_models.dart';

class TitleExcelActions extends StatefulWidget {
  final int titleId;
  final String titleName;
  final int? subMainId;
  final VoidCallback? onImported;

  const TitleExcelActions({
    super.key,
    required this.titleId,
    required this.titleName,
    required this.subMainId,
    this.onImported,
  });

  @override
  State<TitleExcelActions> createState() => _TitleExcelActionsState();
}

class _TitleExcelActionsState extends State<TitleExcelActions> {
  var _downloading = false;

  bool get _ready => widget.subMainId != null;

  Future<void> _download() async {
    final subId = widget.subMainId;
    if (subId == null) return;
    setState(() => _downloading = true);
    try {
      final res = await getIt<BuilderRemoteDataSource>().downloadExcelTemplate(
        titleId: widget.titleId,
        subMainId: subId,
      );
      final bytes = bytesFromResponse(res);
      if (bytes == null || bytes.isEmpty || bytesLookLikeErrorPayload(bytes)) {
        throw StateError('empty');
      }
      var safe = widget.titleName.replaceAll(RegExp(r'[^\w\u0600-\u06FF\-]+'), '_');
      if (safe.length > 40) safe = safe.substring(0, 40);
      if (safe.isEmpty) safe = 'template';
      await saveAndOpenBytes(
        bytes,
        filename: filenameFromResponse(res, '$safe-template.xlsx'),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'تم تنزيل قالب Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.forest1,
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'تعذر تنزيل قالب Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
        ),
      );
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _pickAndImport() async {
    final subId = widget.subMainId;
    if (subId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'اختر القسم الفرعي أولاً قبل رفع Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
        ),
      );
      return;
    }
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['xlsx'],
    );
    if (picked == null || picked.files.isEmpty) return;
    final f = picked.files.first;
    if (f.path == null && (f.bytes == null || f.bytes!.isEmpty)) return;
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _ExcelImportDialog(
        titleId: widget.titleId,
        subMainId: subId,
        fileName: f.name,
        filePath: f.path,
        fileBytes: f.bytes,
        onImported: widget.onImported,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) return const SizedBox.shrink();
    return Wrap(
      spacing: 6.w,
      runSpacing: 6.h,
      alignment: WrapAlignment.end,
      children: [
        OutlinedButton.icon(
          onPressed: _downloading ? null : _download,
          icon: _downloading
              ? SizedBox(
                  width: 12.r,
                  height: 12.r,
                  child: const CircularProgressIndicator(strokeWidth: 2),
                )
              : Icon(Icons.download_outlined, size: 14.r),
          label: Text(
            'تنزيل القالب',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp),
          ),
          style: OutlinedButton.styleFrom(
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 6.h),
          ),
        ),
        FilledButton.icon(
          onPressed: _downloading ? null : _pickAndImport,
          icon: Icon(Icons.upload_file_outlined, size: 14.r),
          label: Text(
            'رفع Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp),
          ),
          style: FilledButton.styleFrom(
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 6.h),
            backgroundColor: AppColors.inkMid,
          ),
        ),
      ],
    );
  }
}

class _ExcelImportDialog extends StatefulWidget {
  final int titleId;
  final int subMainId;
  final String fileName;
  final String? filePath;
  final List<int>? fileBytes;
  final VoidCallback? onImported;

  const _ExcelImportDialog({
    required this.titleId,
    required this.subMainId,
    required this.fileName,
    this.filePath,
    this.fileBytes,
    this.onImported,
  });

  @override
  State<_ExcelImportDialog> createState() => _ExcelImportDialogState();
}

class _ExcelImportDialogState extends State<_ExcelImportDialog> {
  var _busy = false;
  var _validatedOk = false;
  ExcelImportResult? _result;

  String _kindLabel(String kind) {
    switch (kind) {
      case 'missing_column':
        return 'عمود ناقص';
      case 'unknown_column':
        return 'عمود غير معروف';
      case 'skipped_attribute':
        return 'حقل متجاهل';
      default:
        return kind;
    }
  }

  Future<MultipartFile> _buildFile() async {
    if (widget.filePath != null && widget.filePath!.isNotEmpty) {
      return MultipartFile.fromFile(widget.filePath!, filename: widget.fileName);
    }
    return MultipartFile.fromBytes(
      widget.fileBytes ?? const <int>[],
      filename: widget.fileName,
    );
  }

  Future<void> _run({required bool dryRun}) async {
    setState(() => _busy = true);
    try {
      final result = await getIt<BuilderRemoteDataSource>().importExcel(
        titleId: widget.titleId,
        file: await _buildFile(),
        subMainId: widget.subMainId,
        dryRun: dryRun,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _busy = false;
        if (dryRun) _validatedOk = result.canConfirm;
      });
      final messenger = ScaffoldMessenger.maybeOf(context);
      if (dryRun) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text(
              result.canConfirm
                  ? 'التحقق ناجح — يمكن تأكيد الاستيراد'
                  : 'فشل التحقق من الملف',
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor:
                result.canConfirm ? AppColors.forest1 : AppColors.red2,
          ),
        );
        return;
      }
      if (result.errors.isNotEmpty) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text(
              'تم الاستيراد مع أخطاء في بعض الصفوف',
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor: AppColors.red2,
          ),
        );
        return;
      }
      messenger?.showSnackBar(
        SnackBar(
          content: Text(
            'تم استيراد Excel بنجاح',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.forest1,
        ),
      );
      widget.onImported?.call();
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'تعذر استيراد ملف Excel',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.red2,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;
    return AlertDialog(
      title: Text(
        'استيراد Excel',
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: 16.sp,
          fontWeight: FontWeight.w800,
        ),
      ),
      content: SizedBox(
        width: 420.w,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'تحقق من الملف أولاً ثم أكّد الاستيراد. يُستخدم القسم الفرعي الحالي لكل الصفوف.',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 12.sp,
                  color: AppColors.textSecondary,
                ),
              ),
              if (result != null) ...[
                SizedBox(height: 12.h),
                Text(
                  'المستوردة: ${result.importedRows}  —  المتجاهلة: ${result.skippedRows}',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (result.issues.isNotEmpty) ...[
                  SizedBox(height: 10.h),
                  Text(
                    'التحقق من الأعمدة',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  SizedBox(height: 6.h),
                  for (final issue in result.issues)
                    Padding(
                      padding: EdgeInsets.only(bottom: 4.h),
                      child: Text(
                        '${_kindLabel(issue.kind)} · ${issue.column.isEmpty ? '—' : issue.column}: ${issue.message}',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 11.sp,
                          color: issue.isBlocking
                              ? AppColors.errorRed
                              : AppColors.textSecondary,
                        ),
                      ),
                    ),
                ],
                if (result.errors.isNotEmpty) ...[
                  SizedBox(height: 10.h),
                  for (final err in result.errors)
                    Text(
                      'صف ${err.row}: ${err.message}',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 11.sp,
                        color: AppColors.errorRed,
                      ),
                    ),
                ],
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.pop(context),
          child: Text(
            'إلغاء',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
        ),
        OutlinedButton(
          onPressed: _busy ? null : () => _run(dryRun: true),
          child: Text(
            'تحقق',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
        ),
        FilledButton(
          onPressed: _busy || !_validatedOk || !(_result?.canConfirm ?? false)
              ? null
              : () => _run(dryRun: false),
          style: FilledButton.styleFrom(backgroundColor: AppColors.successGreen),
          child: _busy
              ? SizedBox(
                  width: 16.r,
                  height: 14.r,
                  child: const CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(
                  'تأكيد الاستيراد',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
                ),
        ),
      ],
    );
  }
}
