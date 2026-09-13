import 'package:flutter/material.dart';

import '../../../../core/widgets/shared_widgets.dart';

class ElectricityHeader extends StatelessWidget {
  const ElectricityHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return const ForestPageHeader(
      title: 'إدخال بيانات الكهرباء',
      subtitle:
          'اختر القسم والقسم الفرعي ثم عبّئ النماذج الديناميكية كما في النظام، مع حفظ المسودة أو الاعتماد والانتقال، أو استيراد Excel.',
      icon: Icons.bolt_outlined,
    );
  }
}
