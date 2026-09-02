import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
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
          return ListView(
            padding: EdgeInsets.fromLTRB(12.r, 8.r, 12.r, 16.r),
            children: [
              Text(
                'الملف الشخصي',
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 12.h),
              LayoutBuilder(
                builder: (context, constraints) {
                  final sideBySide = constraints.maxWidth >= 560;
                  final avatar = FormCard(
                    child: Column(
                      children: [
                        Container(
                          width: 88.r,
                          height: 88.r,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: AppColors.cardGoldenGradient,
                          ),
                          child: Center(
                            child: Text(
                              _initials(user),
                              style: TextStyle(
                                fontFamily: 'Cairo',
                                fontSize: 26.sp,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                        SizedBox(height: 10.h),
                        OutlinedButton.icon(
                          onPressed: () {},
                          icon: Icon(Icons.camera_alt_outlined, size: 16.r),
                          label: Text(
                            'تحديث الصورة',
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.textSecondary,
                            side: const BorderSide(color: AppColors.border),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8.r),
                            ),
                          ),
                        ),
                        SizedBox(height: 10.h),
                        Text(
                          user.fullName.trim().isEmpty
                              ? user.email
                              : user.fullName,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        SizedBox(height: 4.h),
                        Text(
                          user.email,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 12.sp,
                            color: AppColors.textHint,
                          ),
                        ),
                        SizedBox(height: 8.h),
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 10.w,
                            vertical: 4.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.goldPale,
                            borderRadius: BorderRadius.circular(20.r),
                          ),
                          child: Text(
                            user.appRole == AppRole.admin
                                ? 'مسؤول'
                                : 'مستخدم عادي',
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w700,
                              color: AppColors.inkMid,
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                  final info = FormCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'معلومات الحساب',
                          textAlign: TextAlign.right,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w800,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        SizedBox(height: 12.h),
                        LayoutBuilder(
                          builder: (context, infoConstraints) {
                            final itemWidth =
                                (infoConstraints.maxWidth - 12.w) / 2;
                            return Wrap(
                              spacing: 12.w,
                              runSpacing: 12.h,
                              children: [
                                _InfoItem(
                                  width: itemWidth,
                                  label: 'اسم المستخدم',
                                  value: user.username.isEmpty
                                      ? '—'
                                      : user.username,
                                ),
                                _InfoItem(
                                  width: itemWidth,
                                  label: 'البريد الإلكتروني',
                                  value: user.email,
                                ),
                                _InfoItem(
                                  width: itemWidth,
                                  label: 'تاريخ التسجيل',
                                  value: _joinDate(user.dateJoined),
                                ),
                                _InfoItem(
                                  width: itemWidth,
                                  label: 'الحالة',
                                  value: user.isActive ? 'نشط' : 'معطل',
                                  badge: true,
                                  positive: user.isActive,
                                ),
                              ],
                            );
                          },
                        ),
                      ],
                    ),
                  );
                  if (!sideBySide) {
                    return Column(
                      children: [
                        avatar,
                        SizedBox(height: 12.h),
                        info,
                      ],
                    );
                  }
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: avatar),
                      SizedBox(width: 12.w),
                      Expanded(child: info),
                    ],
                  );
                },
              ),
              SizedBox(height: 12.h),
              FormCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'تعديل البيانات الشخصية',
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    SizedBox(height: 12.h),
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
                          label: 'حفظ',
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
              SizedBox(height: 12.h),
              FormCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'تغيير كلمة المرور',
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    SizedBox(height: 12.h),
                    AppTextField(
                      label: 'كلمة المرور الحالية',
                      hint: 'كلمة المرور الحالية',
                      controller: _currentPass,
                      obscureText: true,
                    ),
                    SizedBox(height: 10.h),
                    Row(
                      children: [
                        Expanded(
                          child: AppTextField(
                            label: 'كلمة المرور الجديدة',
                            hint: 'كلمة المرور الجديدة',
                            controller: _newPass,
                            obscureText: true,
                          ),
                        ),
                        SizedBox(width: 10.w),
                        Expanded(
                          child: AppTextField(
                            label: 'تأكيد كلمة المرور',
                            hint: 'تأكيد كلمة المرور',
                            controller: _confirmPass,
                            obscureText: true,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 14.h),
                    BlocBuilder<ProfileBloc, ProfileState>(
                      buildWhen: (p, c) => p.changingPassword != c.changingPassword,
                      builder: (context, state) {
                        return SaveButton(
                          label: 'حفظ',
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

class _InfoItem extends StatelessWidget {
  final double width;
  final String label;
  final String value;
  final bool badge;
  final bool positive;
  const _InfoItem({
    required this.width,
    required this.label,
    required this.value,
    this.badge = false,
    this.positive = true,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            label,
            textAlign: TextAlign.right,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textHint,
            ),
          ),
          SizedBox(height: 4.h),
          if (badge)
            Align(
              alignment: Alignment.centerRight,
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
              textAlign: TextAlign.right,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
        ],
      ),
    );
  }
}
