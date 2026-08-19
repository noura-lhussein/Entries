import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../admin/presentation/screens/admin_resource_screen.dart';
import '../bloc/water_lookups_bloc.dart';
import '../bloc/water_lookups_event.dart';
import 'water_tabs/dams_screen.dart';
import 'water_tabs/water_flow_screen.dart';
import 'water_tabs/rainfall_screen.dart';
import 'water_tabs/drinking_water_screen.dart';

/// Water daily entry + registry in a single tab bar.
class WaterHubScreen extends StatefulWidget {
  const WaterHubScreen({super.key});
  @override
  State<WaterHubScreen> createState() => _WaterHubScreenState();
}

class _WaterHubScreenState extends State<WaterHubScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tab;

  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 5, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          getIt<WaterLookupsBloc>()..add(const GetWaterLookupsStarted()),
      child: Column(
        children: [
          SectorTabBar(
            controller: _tab,
            tabs: const [
              SectorTab(icon: Icons.grain_outlined, label: 'الهطول'),
              SectorTab(icon: Icons.water_damage_outlined, label: 'السدود'),
              SectorTab(icon: Icons.waves_outlined, label: 'الفرات'),
              SectorTab(icon: Icons.local_drink_outlined, label: 'مياه الشرب'),
              SectorTab(icon: Icons.folder_outlined, label: 'السجلات'),
            ],
          ),
          Expanded(
            child: SafeArea(
              child: TabBarView(
                controller: _tab,
                children: const [
                  RainfallScreen(),
                  DamsScreen(),
                  WaterFlowScreen(),
                  DrinkingWaterScreen(),
                  AdminResourceScreen(sector: UserDepartment.water),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
