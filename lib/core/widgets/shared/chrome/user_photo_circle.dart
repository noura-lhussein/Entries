import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../theme/app_theme.dart';
import '../../../utils/media_url.dart';

class UserPhotoCircle extends StatelessWidget {
  final String? photoUrl;
  final String initials;
  final double size;
  final double fontSize;
  const UserPhotoCircle({
    super.key,
    required this.initials,
    this.photoUrl,
    this.size = 36,
    this.fontSize = 13,
  });

  @override
  Widget build(BuildContext context) {
    final url = absoluteMediaUrl(photoUrl);
    return Container(
      width: size.r,
      height: size.r,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: AppColors.goldGradient,
        border: Border.all(
          color: AppColors.goldLight.withValues(alpha: 0.85),
          width: 1.6,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.goldWarm.withValues(alpha: 0.4),
            blurRadius: 8,
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: url == null
          ? _Initials(initials: initials, fontSize: fontSize)
          : _Photo(url: url, initials: initials, fontSize: fontSize),
    );
  }
}

class _Photo extends StatelessWidget {
  final String url;
  final String initials;
  final double fontSize;
  const _Photo({
    required this.url,
    required this.initials,
    required this.fontSize,
  });

  @override
  Widget build(BuildContext context) {
    if (url.startsWith('file:')) {
      final path = Uri.parse(url).toFilePath();
      return Image.file(
        File(path),
        fit: BoxFit.cover,
        errorBuilder: (_, _, _) =>
            _Initials(initials: initials, fontSize: fontSize),
      );
    }
    if (!url.startsWith('http')) {
      return Image.file(
        File(url),
        fit: BoxFit.cover,
        errorBuilder: (_, _, _) =>
            _Initials(initials: initials, fontSize: fontSize),
      );
    }
    return Image.network(
      url,
      fit: BoxFit.cover,
      errorBuilder: (_, _, _) =>
          _Initials(initials: initials, fontSize: fontSize),
    );
  }
}

class _Initials extends StatelessWidget {
  final String initials;
  final double fontSize;
  const _Initials({required this.initials, required this.fontSize});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        initials,
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: fontSize.sp,
          fontWeight: FontWeight.w800,
          color: Colors.white,
        ),
      ),
    );
  }
}
