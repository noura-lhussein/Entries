import 'package:json_annotation/json_annotation.dart';
import '../../../../core/models/user_model.dart';
import '../../domain/entities/user_entity.dart';

part 'login_response.g.dart';

@JsonSerializable()
class LoginResponse {
  final String? refresh;
  final String? access;
  final UserResponse? user;

  LoginResponse({this.refresh, this.access, this.user});

  factory LoginResponse.fromJson(Map<String, dynamic> json) =>
      _$LoginResponseFromJson(json);

  Map<String, dynamic> toJson() => _$LoginResponseToJson(this);
}

@JsonSerializable()
class UserResponse {
  final int? id;
  final String? email;
  @JsonKey(name: 'full_name')
  final String? fullName;
  @JsonKey(name: 'display_name')
  final String? displayName;
  @JsonKey(name: 'date_joined')
  final String? dateJoined;
  @JsonKey(name: 'is_admin')
  final bool? isAdmin;
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

  UserResponse({
    this.id,
    this.email,
    this.fullName,
    this.displayName,
    this.dateJoined,
    this.isAdmin,
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
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) =>
      _$UserResponseFromJson(json);

  Map<String, dynamic> toJson() => _$UserResponseToJson(this);

  bool get _admin => isAdmin == true;

  bool get _canWrite =>
      _admin ||
      canWriteOilGas == true ||
      canWriteElectricity == true ||
      canWriteWater == true ||
      canWriteMineral == true ||
      canManageProjects == true ||
      canManageDatasets == true ||
      canManageControlPanel == true;

  bool get _canView =>
      _admin ||
      canViewOilGas == true ||
      canViewElectricity == true ||
      canViewWater == true ||
      canViewMineral == true ||
      _canWrite; // write implies portal access on mobile shell

  List<UserDepartment> get _sectors {
    if (_admin) {
      return const [
        UserDepartment.water,
        UserDepartment.petroleum,
        UserDepartment.electricity,
        UserDepartment.mineral,
      ];
    }
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
    return out;
  }

  AppRole get _appRole {
    if (_admin) return AppRole.admin;
    // Both capabilities → dataEntry default; shell allows switching to viewer.
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

  UserEntity toEntity() {
    return UserEntity(
      id: id ?? 0,
      email: email ?? '',
      fullName: fullName ?? '',
      displayName: displayName ?? '',
      dateJoined: dateJoined ?? '',
      department: _department,
      role: _roleLabel,
      appRole: _appRole,
      sectors: _sectors,
      canEnterData: _canWrite,
      canViewData: _canView,
    );
  }
}
