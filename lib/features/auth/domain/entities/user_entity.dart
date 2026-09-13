import 'package:equatable/equatable.dart';
import '../../../../core/models/user_model.dart';

class UserEntity extends Equatable {
  final int id;
  final String email;
  final String fullName;
  final String displayName;
  final String dateJoined;
  final String username;
  final String firstName;
  final String lastName;
  final bool isActive;

  final UserDepartment department;
  final String role;
  final AppRole appRole;
  final List<UserDepartment> sectors;
  final bool canEnterData;
  final bool canViewData;
  final bool canConfirmInfo;
  final String? photoUrl;

  const UserEntity({
    required this.id,
    required this.email,
    required this.fullName,
    required this.displayName,
    required this.dateJoined,
    this.username = '',
    this.firstName = '',
    this.lastName = '',
    this.isActive = true,
    this.department = UserDepartment.admin,
    this.role = 'مدير النظام',
    this.appRole = AppRole.admin,
    this.sectors = const [
      UserDepartment.water,
      UserDepartment.petroleum,
      UserDepartment.electricity,
      UserDepartment.mineral,
    ],
    this.canEnterData = true,
    this.canViewData = true,
    this.canConfirmInfo = false,
    this.photoUrl,
  });

  UserEntity copyWith({
    int? id,
    String? email,
    String? fullName,
    String? displayName,
    String? dateJoined,
    String? username,
    String? firstName,
    String? lastName,
    bool? isActive,
    UserDepartment? department,
    String? role,
    AppRole? appRole,
    List<UserDepartment>? sectors,
    bool? canEnterData,
    bool? canViewData,
    bool? canConfirmInfo,
    String? photoUrl,
  }) {
    return UserEntity(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      displayName: displayName ?? this.displayName,
      dateJoined: dateJoined ?? this.dateJoined,
      username: username ?? this.username,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      isActive: isActive ?? this.isActive,
      department: department ?? this.department,
      role: role ?? this.role,
      appRole: appRole ?? this.appRole,
      sectors: sectors ?? this.sectors,
      canEnterData: canEnterData ?? this.canEnterData,
      canViewData: canViewData ?? this.canViewData,
      canConfirmInfo: canConfirmInfo ?? this.canConfirmInfo,
      photoUrl: photoUrl ?? this.photoUrl,
    );
  }

  UserModel toUserModel() {
    final resolvedName = fullName.trim().isNotEmpty
        ? fullName.trim()
        : (displayName.trim().isNotEmpty ? displayName.trim() : email);
    return UserModel(
      id: id.toString(),
      name: resolvedName,
      email: email,
      department: department,
      role: role,
      appRole: appRole,
      sectors: sectors,
      canEnterData: canEnterData,
      canViewData: canViewData,
      canConfirmInfo: canConfirmInfo,
      photoUrl: photoUrl,
    );
  }

  @override
  List<Object?> get props => [
        id,
        email,
        fullName,
        displayName,
        dateJoined,
        username,
        firstName,
        lastName,
        isActive,
        department,
        role,
        appRole,
        sectors,
        canEnterData,
        canViewData,
        canConfirmInfo,
        photoUrl,
      ];
}
