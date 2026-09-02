import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/network/api_result.dart';
import '../../../auth/domain/entities/user_entity.dart';
import '../../../auth/domain/usecases/auth_usecases.dart';

part 'profile_event.dart';
part 'profile_state.dart';

class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  ProfileBloc({
    required this.updateProfile,
    required this.changePassword,
  }) : super(const ProfileState()) {
    on<ProfileUpdateRequested>(_onUpdate);
    on<ProfilePasswordChangeRequested>(_onPassword);
  }

  final UpdateProfileUseCase updateProfile;
  final ChangePasswordUseCase changePassword;

  Future<void> _onUpdate(
    ProfileUpdateRequested event,
    Emitter<ProfileState> emit,
  ) async {
    emit(state.copyWith(updating: true, clearMessage: true, clearError: true));
    final result = await updateProfile(
      userId: event.userId,
      firstName: event.firstName,
      lastName: event.lastName,
      email: event.email,
    );
    result.when(
      success: (user) {
        emit(state.copyWith(
          updating: false,
          updatedUser: user,
          message: 'تم حفظ التغييرات بنجاح',
        ));
      },
      failure: (err) {
        emit(state.copyWith(
          updating: false,
          error: err.apiErrorModel.message ?? 'خطأ في حفظ التغييرات',
        ));
      },
    );
  }

  Future<void> _onPassword(
    ProfilePasswordChangeRequested event,
    Emitter<ProfileState> emit,
  ) async {
    if (event.currentPassword.trim().isEmpty) {
      emit(state.copyWith(
        passwordError: 'مطلوب',
        clearMessage: true,
      ));
      return;
    }
    if (event.newPassword != event.confirmPassword) {
      emit(state.copyWith(
        passwordError: 'كلمات المرور غير متطابقة',
        clearMessage: true,
      ));
      return;
    }
    if (event.newPassword.trim().length < 6) {
      emit(state.copyWith(
        passwordError: 'كلمة المرور الجديدة مطلوبة (6 أحرف على الأقل)',
        clearMessage: true,
      ));
      return;
    }
    emit(state.copyWith(
      changingPassword: true,
      clearPasswordError: true,
      clearMessage: true,
    ));
    final result = await changePassword(
      userId: event.userId,
      newPassword: event.newPassword,
    );
    result.when(
      success: (_) {
        emit(state.copyWith(
          changingPassword: false,
          passwordChanged: true,
          message: 'تم حفظ التغييرات بنجاح',
        ));
      },
      failure: (err) {
        emit(state.copyWith(
          changingPassword: false,
          passwordError: err.apiErrorModel.message ?? 'خطأ في حفظ التغييرات',
        ));
      },
    );
  }
}
