import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/profile_image_picker.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../auth/domain/entities/user_entity.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../bloc/profile_bloc.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ProfileBloc>(),
      child: const _ProfileView(),
    );
  }
}

class _ProfileView extends StatefulWidget {
  const _ProfileView();

  @override
  State<_ProfileView> createState() => _ProfileViewState();
}

class _ProfileViewState extends State<_ProfileView> {
  late final TextEditingController _first;
  late final TextEditingController _last;
  late final TextEditingController _email;
  late final TextEditingController _currentPass;
  late final TextEditingController _newPass;
  late final TextEditingController _confirmPass;
  bool _hideCurrent = true;
  bool _hideNew = true;
  bool _hideConfirm = true;

  @override
  void initState() {
    super.initState();
    final auth = context.read<AuthBloc>().state;
    final user = auth is AuthAuthenticated ? auth.user : null;
    _first = TextEditingController(text: user?.firstName ?? '');
    _last = TextEditingController(text: user?.lastName ?? '');
    _email = TextEditingController(text: user?.email ?? '');
    _currentPass = TextEditingController();
    _newPass = TextEditingController();
    _confirmPass = TextEditingController();
  }

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _email.dispose();
    _currentPass.dispose();
    _newPass.dispose();
    _confirmPass.dispose();
    super.dispose();
  }

  String _initials(UserEntity user) {
    final source = (user.fullName.trim().isNotEmpty
            ? user.fullName
            : (user.username.trim().isNotEmpty ? user.username : user.email))
        .trim();
    final parts = source.split(RegExp(r'\s+')).where((e) => e.isNotEmpty).toList();
    if (parts.length >= 2) {
      return '${parts[0].characters.first}${parts[1].characters.first}'
          .toUpperCase();
    }
    if (source.isEmpty) return '؟';
    return source.characters.take(2).toString().toUpperCase();
  }

  String _joinDate(String raw) {
    if (raw.trim().isEmpty) return '—';
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;
    final d = parsed.toLocal();
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
  }

  Widget _eye(bool hidden, VoidCallback onTap) {
    return IconButton(
      onPressed: onTap,
      visualDensity: VisualDensity.compact,
      icon: Icon(
        hidden ? Icons.visibility_outlined : Icons.visibility_off_outlined,
        size: 18.r,
        color: AppColors.goldDeep,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<ProfileBloc, ProfileState>(
      listenWhen: (p, c) =>
          p.message != c.message ||
          p.error != c.error ||
          p.passwordError != c.passwordError ||
          p.updatedUser != c.updatedUser ||
          p.passwordChanged != c.passwordChanged,
      listener: (context, state) {
        if (state.updatedUser != null) {
          context.read<AuthBloc>().add(UserUpdated(state.updatedUser!));
        }
        if (state.passwordChanged) {
          _currentPass.clear();
          _newPass.clear();
          _confirmPass.clear();
        }
        final msg = state.message ?? state.error ?? state.passwordError;
        if (msg == null || msg.trim().isEmpty) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              msg,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor: state.error != null || state.passwordError != null
                ? AppColors.red2
                : AppColors.forest1,
          ),
        );
      },
      child: BlocBuilder<AuthBloc, AuthState>(
        builder: (context, authState) {
          if (authState is! AuthAuthenticated) {
            return const Center(child: CircularProgressIndicator());
          }
          final user = authState.user;
          final displayName =
              user.fullName.trim().isEmpty ? user.email : user.fullName;
          return ListView(
            padding: EdgeInsets.fromLTRB(14.r, 10.r, 14.r, 20.r),
            children: [
              BlocBuilder<ProfileBloc, ProfileState>(
                buildWhen: (p, c) => p.uploadingPhoto != c.uploadingPhoto,
                builder: (context, profileState) {
                  return _HeroCard(
                    initials: _initials(user),
                    photoUrl: user.photoUrl,
                    name: displayName,
                    email: user.email,
                    isAdmin: user.appRole == AppRole.admin,
                    isActive: user.isActive,
                    uploading: profileState.uploadingPhoto,
                    onUpdatePhoto: profileState.uploadingPhoto
                        ? null
                        : () async {
                            final path =
                                await pickCompressedProfileImage(context);
                            if (!context.mounted || path == null) return;
                            context.read<ProfileBloc>().add(
                                  ProfilePhotoUpdateRequested(
                                    userId: user.id,
                                    filePath: path,
                                  ),
                                );
                          },
                  );
                },
              ),
              SizedBox(height: 14.h),
              SectionCard(
                title: 'معلومات الحساب',
                icon: Icons.badge_outlined,
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final width = (constraints.maxWidth - 10.w) / 2;
                    return Wrap(
                      spacing: 10.w,
                      runSpacing: 10.h,
                      children: [
                        _InfoTile(
                          width: width,
                          icon: Icons.person_outline_rounded,
                          label: 'اسم المستخدم',
                          value: user.username.isEmpty ? '—' : user.username,
                        ),
                        _InfoTile(
                          width: width,
                          icon: Icons.mail_outline_rounded,
                          label: 'البريد الإلكتروني',
                          value: user.email,
                        ),
                        _InfoTile(
                          width: width,
                          icon: Icons.event_outlined,
                          label: 'تاريخ التسجيل',
                          value: _joinDate(user.dateJoined),
                        ),
                        _InfoTile(
                          width: width,
                          icon: Icons.verified_outlined,
                          label: 'الحالة',
                          value: user.isActive ? 'نشط' : 'معطل',
                          badge: true,
                          positive: user.isActive,
                        ),
                      ],
                    );
                  },
                ),
              ),
              SizedBox(height: 14.h),
              SectionCard(
                title: 'تعديل البيانات الشخصية',
                icon: Icons.edit_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: AppTextField(
                            label: 'الاسم الأول',
                            hint: 'أدخل الاسم الأول',
                            controller: _first,
                          ),
                        ),
                        SizedBox(width: 10.w),
                        Expanded(
                          child: AppTextField(
                            label: 'الاسم الأخير',
                            hint: 'أدخل الاسم الأخير',
                            controller: _last,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 10.h),
                    AppTextField(
                      label: 'البريد الإلكتروني',
                      hint: 'أدخل البريد الإلكتروني',
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                    ),
                    SizedBox(height: 14.h),
                    BlocBuilder<ProfileBloc, ProfileState>(
                      buildWhen: (p, c) => p.updating != c.updating,
                      builder: (context, state) {
                        return SaveButton(
                          label: 'حفظ البيانات',
                          isLoading: state.updating,
                          onPressed: state.updating
                              ? null
                              : () {
                                  final email = _email.text.trim();
                                  if (email.isEmpty || !email.contains('@')) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(
                                          email.isEmpty
                                              ? 'مطلوب'
                                              : 'البريد الإلكتروني غير صحيح',
                                          style: TextStyle(
                                            fontFamily: 'Cairo',
                                            fontSize: 13.sp,
                                          ),
                                        ),
                                        backgroundColor: AppColors.red2,
                                      ),
                                    );
                                    return;
                                  }
                                  context.read<ProfileBloc>().add(
                                        ProfileUpdateRequested(
                                          userId: user.id,
                                          firstName: _first.text.trim(),
                                          lastName: _last.text.trim(),
                                          email: email,
                                        ),
                                      );
                                },
                        );
                      },
                    ),
                  ],
                ),
              ),
              SizedBox(height: 14.h),
              SectionCard(
                title: 'تغيير كلمة المرور',
                icon: Icons.lock_outline_rounded,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppTextField(
                      label: 'كلمة المرور الحالية',
                      hint: 'كلمة المرور الحالية',
                      controller: _currentPass,
                      obscureText: _hideCurrent,
                      suffixIcon: _eye(
                        _hideCurrent,
                        () => setState(() => _hideCurrent = !_hideCurrent),
                      ),
                    ),
                    SizedBox(height: 10.h),
                    Row(
                      children: [
                        Expanded(
                          child: AppTextField(
                            label: 'كلمة المرور الجديدة',
                            hint: 'كلمة المرور الجديدة',
                            controller: _newPass,
                            obscureText: _hideNew,
                            suffixIcon: _eye(
                              _hideNew,
                              () => setState(() => _hideNew = !_hideNew),
                            ),
                          ),
                        ),
                        SizedBox(width: 10.w),
                        Expanded(
                          child: AppTextField(
                            label: 'تأكيد كلمة المرور',
                            hint: 'تأكيد كلمة المرور',
                            controller: _confirmPass,
                            obscureText: _hideConfirm,
                            suffixIcon: _eye(
                              _hideConfirm,
                              () => setState(() => _hideConfirm = !_hideConfirm),
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 14.h),
                    BlocBuilder<ProfileBloc, ProfileState>(
                      buildWhen: (p, c) =>
                          p.changingPassword != c.changingPassword,
                      builder: (context, state) {
                        return SaveButton(
                          label: 'تحديث كلمة المرور',
                          isLoading: state.changingPassword,
                          onPressed: state.changingPassword
                              ? null
                              : () => context.read<ProfileBloc>().add(
                                    ProfilePasswordChangeRequested(
                                      userId: user.id,
                                      currentPassword: _currentPass.text,
                                      newPassword: _newPass.text,
                                      confirmPassword: _confirmPass.text,
                                    ),
                                  ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  final String initials;
  final String? photoUrl;
  final String name;
  final String email;
  final bool isAdmin;
  final bool isActive;
  final bool uploading;
  final VoidCallback? onUpdatePhoto;
  const _HeroCard({
    required this.initials,
    required this.name,
    required this.email,
    required this.isAdmin,
    required this.isActive,
    this.photoUrl,
    this.uploading = false,
    this.onUpdatePhoto,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 20.h, 16.w, 18.h),
      decoration: AppDecorations.forestHeader(radius: 16.r),
      child: Column(
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              UserPhotoCircle(
                photoUrl: photoUrl,
                initials: initials,
                size: 88,
                fontSize: 26,
              ),
              if (uploading)
                SizedBox(
                  width: 88.r,
                  height: 88.r,
                  child: const CircularProgressIndicator(
                    strokeWidth: 2.4,
                    color: Colors.white,
                  ),
                ),
            ],
          ),
          SizedBox(height: 12.h),
          OutlinedButton.icon(
            onPressed: onUpdatePhoto,
            icon: Icon(Icons.camera_alt_outlined, size: 15.r),
            label: Text(
              uploading ? 'جارٍ الرفع…' : 'تحديث الصورة',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.5.sp,
                fontWeight: FontWeight.w700,
              ),
            ),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.goldLight,
              side: BorderSide(color: AppColors.goldWarm.withValues(alpha: 0.45)),
              backgroundColor: Colors.white.withValues(alpha: 0.06),
              visualDensity: VisualDensity.compact,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20.r),
              ),
            ),
          ),
          SizedBox(height: 10.h),
          Text(
            name,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 17.sp,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 3.h),
          Text(
            email,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 12.sp,
              color: AppColors.goldLight.withValues(alpha: 0.9),
            ),
          ),
          SizedBox(height: 12.h),
          Wrap(
            spacing: 8.w,
            runSpacing: 6.h,
            alignment: WrapAlignment.center,
            children: [
              _HeroChip(
                label: isAdmin ? 'مسؤول' : 'مستخدم عادي',
                color: AppColors.goldWarm,
              ),
              _HeroChip(
                label: isActive ? 'نشط' : 'معطل',
                color: isActive ? AppColors.goldLight : AppColors.burgundyLight,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroChip extends StatelessWidget {
  final String label;
  final Color color;
  const _HeroChip({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: color.withValues(alpha: 0.55)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: 11.sp,
          fontWeight: FontWeight.w800,
          color: color,
        ),
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  final double width;
  final IconData icon;
  final String label;
  final String value;
  final bool badge;
  final bool positive;
  const _InfoTile({
    required this.width,
    required this.icon,
    required this.label,
    required this.value,
    this.badge = false,
    this.positive = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      padding: EdgeInsets.all(10.r),
      decoration: AppDecorations.goldWashTile(radius: 12.r),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, size: 14.r, color: AppColors.goldDeep),
              SizedBox(width: 6.w),
              Expanded(
                child: Text(
                  label,
                  textAlign: TextAlign.start,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 10.5.sp,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textHint,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 6.h),
          if (badge)
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: (positive
                          ? AppColors.successGreen
                          : AppColors.errorRed)
                      .withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20.r),
                ),
                child: Text(
                  value,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w800,
                    color:
                        positive ? AppColors.successGreen : AppColors.errorRed,
                  ),
                ),
              ),
            )
          else
            Text(
              value,
              textAlign: TextAlign.start,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 12.5.sp,
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
            ),
        ],
      ),
    );
  }
}
