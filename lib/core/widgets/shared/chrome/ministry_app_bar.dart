import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../theme/app_theme.dart';
import '../../../models/user_model.dart';
import 'profile_avatar.dart';

/// Identical top bar everywhere: forest gradient, logo, profile avatar.
/// Pass [bottom] to attach a TabBar (as the sector dashboard does);
/// leave it null for a plain bar (as Home does).
class MinistryAppBar extends StatelessWidget implements PreferredSizeWidget {
  final UserModel user;
  final VoidCallback onLogout;
  final PreferredSizeWidget? bottom;
  final Gradient gradient;
  const MinistryAppBar({
    super.key,
    required this.user,
    required this.onLogout,
    this.bottom,
    this.gradient = AppColors.headerGradient,
  });

  @override
  Widget build(BuildContext context) {
    return AppBar(
      flexibleSpace: Container(
        decoration: BoxDecoration(gradient: gradient),
      ),
      backgroundColor: Colors.transparent,
      elevation: 0,
      title: const _MinistryLogo(),
      titleSpacing: 8,
      actions: [
        Padding(
          padding: EdgeInsets.only(right: 12.w, left: 12.w),
          child: ProfileAvatar(user: user, onLogout: onLogout),
        ),
      ],
      bottom: bottom,
    );
  }

  @override
  Size get preferredSize => Size.fromHeight(kToolbarHeight + (bottom?.preferredSize.height ?? 0));
}

class _MinistryLogo extends StatelessWidget {
  const _MinistryLogo();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140.w,
      height: 36.h,
      decoration: const BoxDecoration(
        image: DecorationImage(
          image: AssetImage('assets/images/h-logo.webp'),
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}
