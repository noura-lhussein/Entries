import 'package:flutter/material.dart';

import '../../../builder/data/models/builder_models.dart';
import '../../../builder/presentation/screens/sector_data_entry_screen.dart';

class PetroleumScreen extends StatelessWidget {
  const PetroleumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const SectorDataEntryScreen(
      sector: DataEntrySectorFilter.petroleum,
      title: 'إدخال بيانات البترول',
      subtitle:
          'اختر القسم والقسم الفرعي ثم عبّئ النماذج الديناميكية كما في النظام، مع حفظ المسودة أو الاعتماد والانتقال، أو استيراد Excel.',
      icon: Icons.oil_barrel_outlined,
      emptyMainsHint: 'لا توجد أقسام بترول متاحة',
    );
  }
}
