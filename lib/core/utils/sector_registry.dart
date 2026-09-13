import 'package:flutter/material.dart';

import '../models/user_model.dart';
import '../../features/water/presentation/screens/water_hub_screen.dart';
import '../../features/oil_gas/presentation/screens/petroleum_screen.dart';
import '../../features/electricity/presentation/screens/electricity_screen.dart';
import '../../features/geology/presentation/screens/geology_screen.dart';
import '../theme/app_theme.dart';

class SectorInfo {
  final UserDepartment id;
  final String label;
  final IconData icon;
  final Color color;
  const SectorInfo({
    required this.id,
    required this.label,
    required this.icon,
    required this.color,
  });
}

const List<SectorInfo> kAllSectors = [
  SectorInfo(
    id: UserDepartment.water,
    label: 'المياه',
    icon: Icons.water_drop_outlined,
    color: AppColors.inkSoft,
  ),
  SectorInfo(
    id: UserDepartment.petroleum,
    label: 'البترول',
    icon: Icons.oil_barrel_outlined,
    color: AppColors.goldDeep,
  ),
  SectorInfo(
    id: UserDepartment.electricity,
    label: 'الكهرباء',
    icon: Icons.bolt_outlined,
    color: AppColors.successGreen,
  ),
  SectorInfo(
    id: UserDepartment.mineral,
    label: 'التعدين',
    icon: Icons.diamond_outlined,
    color: AppColors.goldWarm,
  ),
];

SectorInfo sectorInfo(UserDepartment d) =>
    kAllSectors.firstWhere((s) => s.id == d, orElse: () => kAllSectors.first);

/// Sectors the account may open (same order as [kAllSectors]).
List<SectorInfo> sectorsForDepartments(Iterable<UserDepartment> allowed) {
  final set = allowed.toSet();
  return [for (final s in kAllSectors) if (set.contains(s.id)) s];
}

/// Sector data-entry body (same as report_moe builder — no records tab).
Widget buildSectorEntryBody(UserDepartment sector) {
  switch (sector) {
    case UserDepartment.water:
      return const WaterHubScreen();
    case UserDepartment.petroleum:
      return const PetroleumScreen();
    case UserDepartment.electricity:
      return const ElectricityScreen();
    case UserDepartment.mineral:
      return const GeologyScreen();
    case UserDepartment.admin:
      return const SizedBox.shrink();
  }
}
