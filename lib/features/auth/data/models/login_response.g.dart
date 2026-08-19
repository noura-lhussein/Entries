// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'login_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LoginResponse _$LoginResponseFromJson(Map<String, dynamic> json) =>
    LoginResponse(
      refresh: json['refresh'] as String?,
      access: json['access'] as String?,
      user: json['user'] == null
          ? null
          : UserResponse.fromJson(json['user'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$LoginResponseToJson(LoginResponse instance) =>
    <String, dynamic>{
      'refresh': instance.refresh,
      'access': instance.access,
      'user': instance.user,
    };

UserResponse _$UserResponseFromJson(Map<String, dynamic> json) => UserResponse(
  id: (json['id'] as num?)?.toInt(),
  email: json['email'] as String?,
  fullName: json['full_name'] as String?,
  displayName: json['display_name'] as String?,
  dateJoined: json['date_joined'] as String?,
  isAdmin: json['is_admin'] as bool?,
  canViewOilGas: json['can_view_oil_gas'] as bool?,
  canWriteOilGas: json['can_write_oil_gas'] as bool?,
  canViewElectricity: json['can_view_electricity'] as bool?,
  canWriteElectricity: json['can_write_electricity'] as bool?,
  canViewWater: json['can_view_water'] as bool?,
  canWriteWater: json['can_write_water'] as bool?,
  canViewMineral: json['can_view_mineral'] as bool?,
  canWriteMineral: json['can_write_mineral'] as bool?,
  canManageProjects: json['can_manage_projects'] as bool?,
  canManageDatasets: json['can_manage_datasets'] as bool?,
  canManageControlPanel: json['can_manage_control_panel'] as bool?,
);

Map<String, dynamic> _$UserResponseToJson(UserResponse instance) =>
    <String, dynamic>{
      'id': instance.id,
      'email': instance.email,
      'full_name': instance.fullName,
      'display_name': instance.displayName,
      'date_joined': instance.dateJoined,
      'is_admin': instance.isAdmin,
      'can_view_oil_gas': instance.canViewOilGas,
      'can_write_oil_gas': instance.canWriteOilGas,
      'can_view_electricity': instance.canViewElectricity,
      'can_write_electricity': instance.canWriteElectricity,
      'can_view_water': instance.canViewWater,
      'can_write_water': instance.canWriteWater,
      'can_view_mineral': instance.canViewMineral,
      'can_write_mineral': instance.canWriteMineral,
      'can_manage_projects': instance.canManageProjects,
      'can_manage_datasets': instance.canManageDatasets,
      'can_manage_control_panel': instance.canManageControlPanel,
    };
