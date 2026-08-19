import 'package:flutter/material.dart';

import '../../../../core/models/user_model.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../admin/presentation/screens/admin_resource_screen.dart';
import 'petroleum_ops_tab.dart';
import 'spc_daily_report_tab.dart';

class PetroleumScreen extends StatefulWidget {
  const PetroleumScreen({super.key});
  @override
  State<PetroleumScreen> createState() => _PetroleumScreenState();
}

class _PetroleumScreenState extends State<PetroleumScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tab;
  @override
  void initState() {
    super.initState();
    _tab = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Column(children: [
        SectorTabBar(
          controller: _tab,
          tabs: const [
            SectorTab(icon: Icons.receipt_long_outlined, label: 'التقرير اليومي'),
            SectorTab(icon: Icons.analytics_outlined, label: 'التشغيل'),
            SectorTab(icon: Icons.folder_outlined, label: 'السجلات'),
          ],
        ),
        Expanded(
            child: TabBarView(
                controller: _tab,
                children: const [
                  SpcDailyReportTab(),
                  PetroleumOpsTab(),
                  AdminResourceScreen(sector: UserDepartment.petroleum),
                ])),
      ]),
    );
  }
}
