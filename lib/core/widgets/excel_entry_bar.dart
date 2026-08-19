import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_theme.dart';
import 'shared_widgets.dart';

class ExcelEntryBar extends StatelessWidget {
  final String hint;
  final bool downloading;
  final bool importing;
  final VoidCallback? onDownload;
  final VoidCallback? onExport;
  final VoidCallback? onUpload;
  final String? exportLabel;

  const ExcelEntryBar({
    super.key,
    required this.hint,
    this.downloading = false,
    this.importing = false,
    this.onDownload,
    this.onExport,
    this.onUpload,
    this.exportLabel,
  });

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            hint,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              color: AppColors.textSecondary,
            ),
          ),
          SizedBox(height: 10.h),
          Wrap(
            spacing: 8.w,
            runSpacing: 8.h,
            children: [
              if (onDownload != null)
                OutlinedButton.icon(
                  onPressed: downloading ? null : onDownload,
                  icon: downloading
                      ? SizedBox(
                          width: 14.r,
                          height: 14.r,
                          child: const CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(Icons.download_outlined, size: 16.r),
                  label: Text(
                    downloading ? 'جاري التنزيل…' : 'تنزيل قالب Excel',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                  ),
                ),
              if (onExport != null)
                OutlinedButton.icon(
                  onPressed: onExport,
                  icon: Icon(Icons.file_upload_outlined, size: 16.r),
                  label: Text(
                    exportLabel ?? 'استخراج البيانات الحالية',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                  ),
                ),
              if (onUpload != null)
                FilledButton.icon(
                  onPressed: importing ? null : onUpload,
                  icon: importing
                      ? SizedBox(
                          width: 14.r,
                          height: 14.r,
                          child: const CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(Icons.upload_file_outlined, size: 16.r),
                  label: Text(
                    importing ? 'جاري الاستيراد…' : 'رفع ملف Excel',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
