import 'package:flutter/material.dart';

import '../../../builder/data/models/builder_models.dart';
import '../../../builder/presentation/screens/sector_data_entry_screen.dart';

class ElectricityScreen extends StatelessWidget {
  const ElectricityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const SectorDataEntryScreen(
      sector: DataEntrySectorFilter.electricity,
      title: 'إدخال بيانات الكهرباء',
      subtitle:
          'اختر القسم والقسم الفرعي ثم عبّئ النماذج الديناميكية كما في النظام، مع حفظ المسودة أو الاعتماد والانتقال، أو استيراد Excel.',
      icon: Icons.bolt_outlined,
      emptyMainsHint: 'لا توجد أقسام كهرباء متاحة',
    );
  }
}
