import 'package:flutter/material.dart';

import '../../../builder/data/models/builder_models.dart';
import '../../../builder/presentation/screens/sector_data_entry_screen.dart';

/// Mining / geology data entry — same report_moe builder flow as the web.
class GeologyScreen extends StatelessWidget {
  const GeologyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const SectorDataEntryScreen(
      sector: DataEntrySectorFilter.mineral,
      title: 'إدخال بيانات التعدين',
      subtitle:
          'اختر القسم والقسم الفرعي ثم عبّئ النماذج الديناميكية كما في النظام، مع حفظ المسودة أو الاعتماد والانتقال، أو استيراد Excel.',
      icon: Icons.diamond_outlined,
      emptyMainsHint: 'لا توجد أقسام تعدين متاحة',
    );
  }
}
