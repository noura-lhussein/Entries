import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import 'login_input_decoration.dart';
import 'login_submit_button.dart';

typedef LoginSubmitCallback = void Function(String email, String password);

class LoginForm extends StatefulWidget {
  const LoginForm({
    super.key,
    required this.onSubmit,
    this.isLoading = false,
  });

  final LoginSubmitCallback onSubmit;
  final bool isLoading;

  @override
  State<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends State<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  var _obscure = true;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    if (widget.isLoading) return;
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;
    widget.onSubmit(_emailCtrl.text.trim(), _passwordCtrl.text);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(22.w, 24.h, 22.w, 22.h),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.28),
            blurRadius: 32,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'بيانات الدخول',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 18.sp,
                fontWeight: FontWeight.w800,
                color: AppColors.ink,
              ),
            ),
            SizedBox(height: 4.h),
            Text(
              'البريد الرسمي وكلمة المرور',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 12.sp,
                color: AppColors.inkSoft,
              ),
            ),
            SizedBox(height: 20.h),
            const LoginFieldLabel('البريد الإلكتروني'),
            SizedBox(height: 8.h),
            TextFormField(
              controller: _emailCtrl,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              textDirection: TextDirection.ltr,
              textAlign: TextAlign.left,
              style: _inputStyle,
              decoration: LoginInputDecoration.build(
                hint: 'name@energy.gov.sy',
                icon: Icons.mail_outline_rounded,
              ),
              validator: (v) {
                final t = v?.trim() ?? '';
                if (t.isEmpty) return 'أدخل البريد الإلكتروني';
                if (!t.contains('@')) return 'بريد غير صالح';
                return null;
              },
            ),
            SizedBox(height: 16.h),
            const LoginFieldLabel('كلمة المرور'),
            SizedBox(height: 8.h),
            TextFormField(
              controller: _passwordCtrl,
              obscureText: _obscure,
              textInputAction: TextInputAction.done,
              onFieldSubmitted: (_) => _submit(),
              textDirection: TextDirection.ltr,
              textAlign: TextAlign.left,
              style: _inputStyle,
              decoration: LoginInputDecoration.build(
                hint: 'أدخل كلمة المرور',
                icon: Icons.lock_outline_rounded,
                suffix: IconButton(
                  onPressed: () => setState(() => _obscure = !_obscure),
                  icon: Icon(
                    _obscure
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                    size: 20.r,
                    color: AppColors.inkSoft,
                  ),
                ),
              ),
              validator: (v) {
                if (v == null || v.length < 6) {
                  return '6 أحرف على الأقل';
                }
                return null;
              },
            ),
            SizedBox(height: 24.h),
            LoginSubmitButton(
              onPressed: _submit,
              isLoading: widget.isLoading,
            ),
          ],
        ),
      ),
    );
  }

  TextStyle get _inputStyle => TextStyle(
        fontFamily: 'Cairo',
        fontSize: 14.sp,
        color: AppColors.ink,
        fontWeight: FontWeight.w600,
      );
}
