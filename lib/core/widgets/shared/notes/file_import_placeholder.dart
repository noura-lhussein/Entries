import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';

class FileImportPlaceholder extends StatelessWidget {
  final String note;
  final VoidCallback? onPickFiles;
  final VoidCallback? onDownloadTemplate;
  final VoidCallback? onClear;
  final VoidCallback? onExport;
  final String? templateLabel;
  final String? clearLabel;
  final String? exportLabel;

  const FileImportPlaceholder({
    super.key,
    this.note = 'اسحب وأفلت ملفات .XLS أو .XLSX هنا',
    this.onPickFiles,
    this.onDownloadTemplate,
    this.onClear,
    this.onExport,
    this.templateLabel,
    this.clearLabel,
    this.exportLabel,
  });

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.symmetric(vertical: 32.h, horizontal: 24.w),
    decoration: BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(14.r),
      border: Border.all(color: AppColors.border),
    ),
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(
        width: 56.r, height: 56.r,
        decoration: BoxDecoration(color: AppColors.goldWash, shape: BoxShape.circle,
          border: Border.all(color: AppColors.borderMid)),
        child: Icon(Icons.cloud_upload_outlined, size: 26.r, color: AppColors.goldMid),
      ),
      SizedBox(height: 14.h),
      Text(note, style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, color: AppColors.textHint, height: 1.6),
        textAlign: TextAlign.center),
      SizedBox(height: 16.h),
      OutlinedButton.icon(
        onPressed: onPickFiles,
        icon: Icon(Icons.folder_open_outlined, size: 15.r),
        label: Text('تصفح الملفات', style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp, fontWeight: FontWeight.w600)),
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.inkMid,
          side: const BorderSide(color: AppColors.borderMid),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 10.h),
        ),
      ),
      if (onDownloadTemplate != null || onClear != null || onExport != null) ...[
        SizedBox(height: 12.h),
        Wrap(
          spacing: 8.w,
          runSpacing: 8.h,
          alignment: WrapAlignment.center,
          children: [
            if (onDownloadTemplate != null)
              TextButton.icon(
                onPressed: onDownloadTemplate,
                icon: Icon(Icons.download_outlined, size: 16.r),
                label: Text(templateLabel ?? 'تحميل القالب',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp)),
              ),
            if (onExport != null)
              TextButton.icon(
                onPressed: onExport,
                icon: Icon(Icons.file_download_outlined, size: 16.r),
                label: Text(exportLabel ?? 'تصدير',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp)),
              ),
            if (onClear != null)
              TextButton.icon(
                onPressed: onClear,
                icon: Icon(Icons.delete_outline, size: 16.r, color: AppColors.red2),
                label: Text(clearLabel ?? 'مسح البيانات المستوردة',
                    style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 12.sp,
                        color: AppColors.red2)),
              ),
          ],
        ),
      ],
    ]),
  );
}
