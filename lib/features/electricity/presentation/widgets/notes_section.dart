import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';

class NotesSection extends StatelessWidget {
  final TextEditingController arabicNotesCtrl;
  final TextEditingController englishNotesCtrl;

  const NotesSection({
    super.key,
    required this.arabicNotesCtrl,
    required this.englishNotesCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'ملاحظات',
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 14.sp,
              fontWeight: FontWeight.w800,
              color: AppColors.forest,
            ),
          ),
          SizedBox(height: 12.h),
          AppTextField(
            label: 'ملاحظات (عربي)',
            controller: arabicNotesCtrl,
            hint: '',
          ),
          SizedBox(height: 10.h),
          AppTextField(
            label: 'ملاحظات (إنجليزي)',
            controller: englishNotesCtrl,
            hint: '',
          ),
          SizedBox(height: 12.h),
          BlocBuilder<ElectricityBloc, ElectricityState>(
            buildWhen: (p, c) => p.publishAfterSave != c.publishAfterSave,
            builder: (context, state) {
              return InkWell(
                onTap: () => context
                    .read<ElectricityBloc>()
                    .add(PublishAfterSaveToggled(!state.publishAfterSave)),
                child: Row(
                  children: [
                    Checkbox(
                      value: state.publishAfterSave,
                      activeColor: AppColors.forest1,
                      onChanged: (v) => context
                          .read<ElectricityBloc>()
                          .add(PublishAfterSaveToggled(v ?? true)),
                    ),
                    Expanded(
                      child: Text(
                        'نشر التقرير بعد الحفظ',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 12.sp,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
