import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/drinking_water/drinking_water_bloc.dart';
import '../../bloc/drinking_water/drinking_water_event.dart';
import '../../bloc/drinking_water/drinking_water_state.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_multipart_picker.dart';
import 'drinking_import_mode_card.dart';

class DrinkingWaterImportPanel extends StatelessWidget {
  const DrinkingWaterImportPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DrinkingWaterBloc, DrinkingWaterState>(
      buildWhen: (p, c) => p.importSurvey != c.importSurvey,
      builder: (context, state) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DrinkingImportModeCard(
              importSurvey: state.importSurvey,
              onChanged: (v) => context
                  .read<DrinkingWaterBloc>()
                  .add(DrinkingWaterImportSurveyToggled(v)),
            ),
            SizedBox(height: 12.h),
            FileImportPlaceholder(
              note: state.importSurvey
                  ? 'اسحب وأفلت ملفات استمارة TEI (.XLS / .XLSX / .ZIP)'
                  : 'اسحب وأفلت ملفات السجل الجغرافي (.XLS / .XLSX / .ZIP)',
              onPickFiles: () async {
                final files = await pickWaterMultipartFiles(
                  allowedExtensions: ['xls', 'xlsx', 'zip'],
                );
                if (!context.mounted || files.isEmpty) return;
                context
                    .read<DrinkingWaterBloc>()
                    .add(DrinkingWaterImportRequested(files));
              },
              onDownloadTemplate: () => downloadWaterTemplate(
                context,
                kind: state.importSurvey
                    ? 'drinking-water-survey'
                    : 'drinking-water-geo',
                fallbackName: state.importSurvey
                    ? 'drinking-water-survey.xlsx'
                    : 'drinking-water-geo.xlsx',
              ),
              onExport: state.importSurvey
                  ? () => exportDrinkingSurvey(context)
                  : null,
              exportLabel: 'تصدير استمارة TEI',
            ),
          ],
        );
      },
    );
  }
}
