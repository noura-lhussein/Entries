import 'package:flutter/material.dart';

import '../models/user_model.dart';
import '../../features/admin/presentation/screens/admin_resource_screen.dart';
import '../../features/water/presentation/screens/water_hub_screen.dart';
import '../../features/oil_gas/presentation/screens/petroleum_screen.dart';
import '../../features/electricity/presentation/screens/electricity_screen.dart';
import '../../features/geology/presentation/screens/geology_screen.dart';
import '../theme/app_theme.dart';
import '../widgets/shared_widgets.dart';

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
    color: Color(0xFF2E7DD1),
  ),
  SectorInfo(
    id: UserDepartment.petroleum,
    label: 'البترول',
    icon: Icons.oil_barrel_outlined,
    color: Color(0xFFB8942A),
  ),
  SectorInfo(
    id: UserDepartment.electricity,
    label: 'الكهرباء',
    icon: Icons.bolt_outlined,
    color: Color(0xFF1A6B3C),
  ),
  SectorInfo(
    id: UserDepartment.mineral,
    label: 'التعدين',
    icon: Icons.diamond_outlined,
    color: AppColors.goldMid,
  ),
];

SectorInfo sectorInfo(UserDepartment d) =>
    kAllSectors.firstWhere((s) => s.id == d, orElse: () => kAllSectors.first);

/// Sectors the account may open (same order as [kAllSectors]).
List<SectorInfo> sectorsForDepartments(Iterable<UserDepartment> allowed) {
  final set = allowed.toSet();
  return [for (final s in kAllSectors) if (set.contains(s.id)) s];
}

/// Entry hub: daily operations + admin registry (like moe-portal).
Widget buildSectorEntryBody(UserDepartment sector) {
  if (sector == UserDepartment.admin) return const SizedBox.shrink();
  return _SectorEntryHub(sector: sector);
}

class _SectorEntryHub extends StatefulWidget {
  final UserDepartment sector;
  const _SectorEntryHub({required this.sector});

  @override
  State<_SectorEntryHub> createState() => _SectorEntryHubState();
}

class _SectorEntryHubState extends State<_SectorEntryHub>
    with SingleTickerProviderStateMixin {
  late TabController _tab;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  Widget _dailyBody() {
    switch (widget.sector) {
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

  @override
  Widget build(BuildContext context) {
    final nested = widget.sector == UserDepartment.water ||
        widget.sector == UserDepartment.petroleum;
    if (nested) {
      return _dailyBody();
    }
    return Column(
      children: [
        SectorTabBar(
          controller: _tab,
          tabs: const [
            SectorTab(icon: Icons.edit_note_outlined, label: 'الإدخال اليومي'),
            SectorTab(icon: Icons.folder_outlined, label: 'السجلات'),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tab,
            children: [
              _dailyBody(),
              AdminResourceScreen(sector: widget.sector),
            ],
          ),
        ),
      ],
    );
  }
}
