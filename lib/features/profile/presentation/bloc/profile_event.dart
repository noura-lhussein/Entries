part of 'profile_bloc.dart';

abstract class ProfileEvent extends Equatable {
  const ProfileEvent();
  @override
  List<Object?> get props => [];
}

class ProfileUpdateRequested extends ProfileEvent {
  final int userId;
  final String firstName;
  final String lastName;
  final String email;
  const ProfileUpdateRequested({
    required this.userId,
    required this.firstName,
    required this.lastName,
    required this.email,
  });
  @override
  List<Object?> get props => [userId, firstName, lastName, email];
}

class ProfilePasswordChangeRequested extends ProfileEvent {
  final int userId;
  final String currentPassword;
  final String newPassword;
  final String confirmPassword;
  const ProfilePasswordChangeRequested({
    required this.userId,
    required this.currentPassword,
    required this.newPassword,
    required this.confirmPassword,
  });
  @override
  List<Object?> get props =>
      [userId, currentPassword, newPassword, confirmPassword];
}
