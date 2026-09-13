part of 'profile_bloc.dart';

class ProfileState extends Equatable {
  final bool updating;
  final bool uploadingPhoto;
  final bool changingPassword;
  final String? message;
  final String? error;
  final String? passwordError;
  final UserEntity? updatedUser;
  final bool passwordChanged;

  const ProfileState({
    this.updating = false,
    this.uploadingPhoto = false,
    this.changingPassword = false,
    this.message,
    this.error,
    this.passwordError,
    this.updatedUser,
    this.passwordChanged = false,
  });

  ProfileState copyWith({
    bool? updating,
    bool? uploadingPhoto,
    bool? changingPassword,
    String? message,
    String? error,
    String? passwordError,
    UserEntity? updatedUser,
    bool? passwordChanged,
    bool clearMessage = false,
    bool clearError = false,
    bool clearPasswordError = false,
  }) {
    return ProfileState(
      updating: updating ?? this.updating,
      uploadingPhoto: uploadingPhoto ?? this.uploadingPhoto,
      changingPassword: changingPassword ?? this.changingPassword,
      message: clearMessage ? null : (message ?? this.message),
      error: clearError ? null : (error ?? this.error),
      passwordError:
          clearPasswordError ? null : (passwordError ?? this.passwordError),
      updatedUser: updatedUser ?? this.updatedUser,
      passwordChanged: passwordChanged ?? false,
    );
  }

  @override
  List<Object?> get props => [
        updating,
        uploadingPhoto,
        changingPassword,
        message,
        error,
        passwordError,
        updatedUser,
        passwordChanged,
      ];
}
