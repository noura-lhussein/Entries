enum UserDepartment { water, petroleum, electricity, mineral, admin }

enum AppRole { admin, dataEntry, viewer }

class UserModel {
  final String id;
  final String name;
  final String email;

  final UserDepartment department;

  final String role;

  final AppRole appRole;

  final List<UserDepartment> sectors;

  final bool canEnterData;

  final bool canViewData;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    required this.department,
    required this.role,
    required this.appRole,
    required this.sectors,
    this.canEnterData = false,
    this.canViewData = false,
  });

  bool get isAdmin => appRole == AppRole.admin;
  bool get isDataEntry => appRole == AppRole.dataEntry;
  bool get isViewer => appRole == AppRole.viewer;

  bool get canSwitchModes =>
      isAdmin || (canEnterData && canViewData);

  List<UserDepartment> get accessibleSectors => isAdmin
      ? const [
          UserDepartment.water,
          UserDepartment.petroleum,
          UserDepartment.electricity,
          UserDepartment.mineral,
        ]
      : sectors;

  String get appRoleLabel {
    if (canSwitchModes && !isAdmin) return 'إدخال وعرض';
    switch (appRole) {
      case AppRole.admin:
        return 'مدير النظام';
      case AppRole.dataEntry:
        return 'مدخل بيانات';
      case AppRole.viewer:
        return 'عارض بيانات';
    }
  }

  String get departmentLabel {
    if (isAdmin) return 'كل القطاعات';
    if (sectors.length > 1) return 'قطاعات متعددة';
    if (sectors.length == 1) return sectorLabel(sectors.first);
    return sectorLabel(department);
  }

  static String sectorLabel(UserDepartment d) {
    switch (d) {
      case UserDepartment.water:
        return 'المياه';
      case UserDepartment.petroleum:
        return 'البترول';
      case UserDepartment.electricity:
        return 'الكهرباء';
      case UserDepartment.mineral:
        return 'التعدين';
      case UserDepartment.admin:
        return 'الإدارة العامة';
    }
  }
}
