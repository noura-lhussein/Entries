import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/euphrates/euphrates_bloc.dart';
import '../../bloc/euphrates/euphrates_event.dart';
import '../../bloc/euphrates/euphrates_state.dart';

class EuphratesDailyForm extends StatelessWidget {
  const EuphratesDailyForm({
    super.key,
    required this.titleController,
    required this.tishreenInflowController,
    required this.tishreenLevelController,
    required this.tishreenStorageController,
    required this.tishreenGenerationController,
    required this.furatLevelController,
    required this.furatStorageController,
    required this.furatGenerationController,
    required this.kadiranGenerationController,
    required this.totalController,
  });

  final TextEditingController titleController;
  final TextEditingController tishreenInflowController;
  final TextEditingController tishreenLevelController;
  final TextEditingController tishreenStorageController;
  final TextEditingController tishreenGenerationController;
  final TextEditingController furatLevelController;
  final TextEditingController furatStorageController;
  final TextEditingController furatGenerationController;
  final TextEditingController kadiranGenerationController;
  final TextEditingController totalController;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        BlocSelector<EuphratesBloc, EuphratesState, DateTime>(
          selector: (s) => s.date,
          builder: (context, date) {
            return FormCard(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  AppTextField(
                    label: 'عنوان التقرير',
                    controller: titleController,
                  ),
                  SizedBox(height: 10.h),
                  DatePickerField(
                    label: 'التاريخ',
                    initialDate: date,
                    onDateChanged: (d) => context
                        .read<EuphratesBloc>()
                        .add(EuphratesDateChanged(d)),
                  ),
                ],
              ),
            );
          },
        ),
        SizedBox(height: 12.h),
        SectionCard(
          title: 'محطة تشرين',
          child: FieldsWrap(
            fields: [
              AppTextField(
                label: 'الوارد (م³/ث)',
                controller: tishreenInflowController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'م³/ث',
              ),
              AppTextField(
                label: 'منسوب تشرين',
                controller: tishreenLevelController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'م',
              ),
              AppTextField(
                label: 'مخزون تشرين',
                controller: tishreenStorageController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'مليون م³',
              ),
              AppTextField(
                label: 'توليد تشرين',
                controller: tishreenGenerationController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'MW',
              ),
            ],
          ),
        ),
        SizedBox(height: 12.h),
        SectionCard(
          title: 'محطة الفرات + كديران',
          child: FieldsWrap(
            fields: [
              AppTextField(
                label: 'منسوب الفرات',
                controller: furatLevelController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'م',
              ),
              AppTextField(
                label: 'مخزون الفرات',
                controller: furatStorageController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'مليون م³',
              ),
              AppTextField(
                label: 'توليد الفرات',
                controller: furatGenerationController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'MW',
              ),
              AppTextField(
                label: 'توليد كديران',
                controller: kadiranGenerationController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                suffixText: 'MW',
              ),
            ],
          ),
        ),
        SizedBox(height: 12.h),
        SectionCard(
          title: 'الإجمالي',
          child: AppTextField(
            label: 'إجمالي التوليد',
            controller: totalController,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            suffixText: 'MW',
          ),
        ),
        SizedBox(height: 12.h),
        const DuplicateNote(),
        SizedBox(height: 12.h),
        BlocSelector<EuphratesBloc, EuphratesState, bool>(
          selector: (s) => s.isBusy,
          builder: (context, isBusy) => SaveButton(
            isLoading: isBusy,
            onPressed: () => context.read<EuphratesBloc>().add(
                  EuphratesSaveRequested(
                    reportLabel: titleController.text,
                    tishreenInflow: tishreenInflowController.text,
                    tishreenLevel: tishreenLevelController.text,
                    tishreenStorage: tishreenStorageController.text,
                    tishreenGeneration: tishreenGenerationController.text,
                    furatLevel: furatLevelController.text,
                    furatStorage: furatStorageController.text,
                    furatGeneration: furatGenerationController.text,
                    kadiranGeneration: kadiranGenerationController.text,
                    totalGeneration: totalController.text,
                  ),
                ),
          ),
        ),
      ],
    );
  }
}
