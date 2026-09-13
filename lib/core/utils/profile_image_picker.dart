import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:image_picker/image_picker.dart';

import '../theme/app_theme.dart';

Future<String?> pickCompressedProfileImage(BuildContext context) async {
  final source = await showModalBottomSheet<ImageSource>(
    context: context,
    backgroundColor: AppColors.surface,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(16.r)),
    ),
    builder: (ctx) {
      return SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'تحديث الصورة',
                textAlign: TextAlign.start,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 10.h),
              ListTile(
                leading: Icon(Icons.photo_library_outlined, color: AppColors.goldDeep),
                title: Text(
                  'اختيار من المعرض',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
                ),
                onTap: () => Navigator.pop(ctx, ImageSource.gallery),
              ),
              ListTile(
                leading: Icon(Icons.photo_camera_outlined, color: AppColors.goldDeep),
                title: Text(
                  'التقاط من الكاميرا',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
                ),
                onTap: () => Navigator.pop(ctx, ImageSource.camera),
              ),
            ],
          ),
        ),
      );
    },
  );
  if (source == null) return null;

  final file = await ImagePicker().pickImage(
    source: source,
    maxWidth: 1024,
    maxHeight: 1024,
    imageQuality: 72,
    requestFullMetadata: false,
  );
  return file?.path;
}
