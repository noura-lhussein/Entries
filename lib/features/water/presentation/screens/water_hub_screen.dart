import 'package:flutter/material.dart';

import '../../../builder/data/models/builder_models.dart';
import '../../../builder/presentation/screens/sector_data_entry_screen.dart';

/// Water data entry — same report_moe builder flow as the web
/// (main section → sub-section → dynamic titles/schema).
class WaterHubScreen extends StatelessWidget {
  const WaterHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const SectorDataEntryScreen(
      sector: DataEntrySectorFilter.water,
      title: 'إدخال بيانات المياه',
      subtitle:
          'اختر القسم والقسم الفرعي ثم عبّئ النماذج الديناميكية كما في النظام (هطول، سدود، فرات، مياه شرب وغيرها حسب التعريف في الويب)، مع حفظ المسودة أو الاعتماد والانتقال، أو استيراد Excel.',
      icon: Icons.water_drop_outlined,
      emptyMainsHint: 'لا توجد أقسام مياه متاحة',
    );
  }
}
