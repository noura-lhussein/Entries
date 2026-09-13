import 'package:json_annotation/json_annotation.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/network/auth_tokens.dart';
import '../../../../core/utils/media_url.dart';
import '../../domain/entities/user_entity.dart';

part 'login_response.g.dart';

@JsonSerializable()
class LoginResponse {
  final String? refresh;
  final String? access;
  final UserResponse? user;

  LoginResponse({this.refresh, this.access, this.user});

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    final tokens = AuthTokens.fromJson(json);
    UserResponse? user;
    final nestedUser = json['user'];
    if (nestedUser is Map) {
      user = UserResponse.fromJson(Map<String, dynamic>.from(nestedUser));
    } else if (json['id'] != null || json['username'] != null) {
      user = UserResponse.fromJson(json);
    }
    return LoginResponse(
      access: tokens.access,
      refresh: tokens.refresh,
      user: user,
    );
  }

  Map<String, dynamic> toJson() => _$LoginResponseToJson(this);
}

@JsonSerializable()
class UserResponse {
  final int? id;
  final String? email;
  final String? username;
  @JsonKey(name: 'full_name')
  final String? fullName;
  @JsonKey(name: 'first_name')
  final String? firstName;
  @JsonKey(name: 'last_name')
  final String? lastName;
  @JsonKey(name: 'display_name')
  final String? displayName;
  @JsonKey(name: 'date_joined')
  final String? dateJoined;
  @JsonKey(name: 'is_admin')
  final bool? isAdmin;
  @JsonKey(name: 'is_staff')
  final bool? isStaff;
  @JsonKey(name: 'is_superuser')
  final bool? isSuperuser;
  @JsonKey(name: 'is_active')
  final bool? isActive;
  @JsonKey(name: 'can_write_info')
  final bool? canWriteInfo;
  @JsonKey(name: 'can_view_info')
  final bool? canViewInfo;
  @JsonKey(name: 'can_confirm_info')
  final bool? canConfirmInfo;
  @JsonKey(name: 'can_view_oil_gas')
  final bool? canViewOilGas;
  @JsonKey(name: 'can_write_oil_gas')
  final bool? canWriteOilGas;
  @JsonKey(name: 'can_view_electricity')
  final bool? canViewElectricity;
  @JsonKey(name: 'can_write_electricity')
  final bool? canWriteElectricity;
  @JsonKey(name: 'can_view_water')
  final bool? canViewWater;
  @JsonKey(name: 'can_write_water')
  final bool? canWriteWater;
  @JsonKey(name: 'can_view_mineral')
  final bool? canViewMineral;
  @JsonKey(name: 'can_write_mineral')
  final bool? canWriteMineral;
  @JsonKey(name: 'can_manage_projects')
  final bool? canManageProjects;
  @JsonKey(name: 'can_manage_datasets')
  final bool? canManageDatasets;
  @JsonKey(name: 'can_manage_control_panel')
  final bool? canManageControlPanel;
  @JsonKey(includeFromJson: false, includeToJson: false)
  final String? photoUrl;

  UserResponse({
    this.id,
    this.email,
    this.username,
    this.fullName,
    this.firstName,
    this.lastName,
    this.displayName,
    this.dateJoined,
    this.isAdmin,
    this.isStaff,
    this.isSuperuser,
    this.isActive,
    this.canWriteInfo,
    this.canViewInfo,
    this.canConfirmInfo,
    this.canViewOilGas,
    this.canWriteOilGas,
    this.canViewElectricity,
    this.canWriteElectricity,
    this.canViewWater,
    this.canWriteWater,
    this.canViewMineral,
    this.canWriteMineral,
    this.canManageProjects,
    this.canManageDatasets,
    this.canManageControlPanel,
    this.photoUrl,
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) {
    final user = _$UserResponseFromJson(json);
    return UserResponse(
      id: user.id,
      email: user.email,
      username: user.username,
      fullName: user.fullName,
      firstName: user.firstName,
      lastName: user.lastName,
      displayName: user.displayName,
      dateJoined: user.dateJoined,
      isAdmin: user.isAdmin,
      isStaff: user.isStaff,
      isSuperuser: user.isSuperuser,
      isActive: user.isActive,
      canWriteInfo: user.canWriteInfo,
      canViewInfo: user.canViewInfo,
      canConfirmInfo: user.canConfirmInfo,
      canViewOilGas: user.canViewOilGas,
      canWriteOilGas: user.canWriteOilGas,
      canViewElectricity: user.canViewElectricity,
      canWriteElectricity: user.canWriteElectricity,
      canViewWater: user.canViewWater,
      canWriteWater: user.canWriteWater,
      canViewMineral: user.canViewMineral,
      canWriteMineral: user.canWriteMineral,
      canManageProjects: user.canManageProjects,
      canManageDatasets: user.canManageDatasets,
      canManageControlPanel: user.canManageControlPanel,
      photoUrl: photoUrlFromJson(json) ?? user.photoUrl,
    );
  }

  Map<String, dynamic> toJson() => {
        ..._$UserResponseToJson(this),
        if (photoUrl != null && photoUrl!.isNotEmpty) 'photo': photoUrl,
      };

  static const _allSectors = [
    UserDepartment.water,
    UserDepartment.petroleum,
    UserDepartment.electricity,
    UserDepartment.mineral,
  ];

  bool get _admin =>
      isAdmin == true || isStaff == true || isSuperuser == true;

  bool get _canWrite =>
      _admin ||
      canWriteInfo == true ||
      canWriteOilGas == true ||
      canWriteElectricity == true ||
      canWriteWater == true ||
      canWriteMineral == true ||
      canManageProjects == true ||
      canManageDatasets == true ||
      canManageControlPanel == true;

  bool get _canView =>
      _admin ||
      canViewInfo == true ||
      canConfirmInfo == true ||
      canViewOilGas == true ||
      canViewElectricity == true ||
      canViewWater == true ||
      canViewMineral == true ||
      _canWrite;

  List<UserDepartment> get _sectors {
    if (_admin) return _allSectors;
    final out = <UserDepartment>[];
    if (canViewWater == true || canWriteWater == true) {
      out.add(UserDepartment.water);
    }
    if (canViewOilGas == true || canWriteOilGas == true) {
      out.add(UserDepartment.petroleum);
    }
    if (canViewElectricity == true || canWriteElectricity == true) {
      out.add(UserDepartment.electricity);
    }
    if (canViewMineral == true || canWriteMineral == true) {
      out.add(UserDepartment.mineral);
    }
    // report_moe users are gated by title/sub-section ids, not sector flags.
    if (out.isEmpty && (_canWrite || _canView)) return _allSectors;
    return out;
  }

  AppRole get _appRole {
    if (_admin) return AppRole.admin;
    if (_canWrite) return AppRole.dataEntry;
    if (_canView) return AppRole.viewer;
    return AppRole.viewer;
  }

  UserDepartment get _department {
    final sectors = _sectors;
    if (sectors.isEmpty) return UserDepartment.admin;
    return sectors.first;
  }

  String get _roleLabel {
    if (_admin) return 'مدير النظام';
    if (_canWrite && _canView) return 'إدخال وعرض';
    switch (_appRole) {
      case AppRole.dataEntry:
        return 'مدخل بيانات';
      case AppRole.viewer:
        return 'عارض بيانات';
      case AppRole.admin:
        return 'مدير النظام';
    }
  }

  String get _resolvedEmail {
    final mail = email?.trim() ?? '';
    if (mail.isNotEmpty) return mail;
    return username?.trim() ?? '';
  }

  String get _resolvedName {
    final full = fullName?.trim() ?? '';
    if (full.isNotEmpty) return full;
    final parts = [
      firstName?.trim() ?? '',
      lastName?.trim() ?? '',
    ].where((e) => e.isNotEmpty).join(' ');
    if (parts.isNotEmpty) return parts;
    final display = displayName?.trim() ?? '';
    if (display.isNotEmpty) return display;
    return _resolvedEmail;
  }

  UserEntity toEntity() {
    return UserEntity(
      id: id ?? 0,
      email: _resolvedEmail,
      fullName: _resolvedName,
      displayName: displayName?.trim().isNotEmpty == true
          ? displayName!.trim()
          : _resolvedName,
      dateJoined: dateJoined ?? '',
      username: username?.trim() ?? '',
      firstName: firstName?.trim() ?? '',
      lastName: lastName?.trim() ?? '',
      isActive: isActive ?? true,
      department: _department,
      role: _roleLabel,
      appRole: _appRole,
      sectors: _sectors,
      canEnterData: _canWrite,
      canViewData: _canView,
      canConfirmInfo: _admin || canConfirmInfo == true,
      photoUrl: photoUrl,
    );
  }
}
