import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';

class DrinkingImportModeCard extends StatelessWidget {
  const DrinkingImportModeCard({
    super.key,
    required this.importSurvey,
    required this.onChanged,
  });

  final bool importSurvey;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'نوع الاستيراد',
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 8.h),
          Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: const Text('السجل الجغرافي'),
                  selected: !importSurvey,
                  onSelected: (_) => onChanged(false),
                ),
              ),
              SizedBox(width: 8.w),
              Expanded(
                child: ChoiceChip(
                  label: const Text('استمارة TEI'),
                  selected: importSurvey,
                  onSelected: (_) => onChanged(true),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
