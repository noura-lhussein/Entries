import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/rainfall/rainfall_bloc.dart';
import '../../bloc/rainfall/rainfall_event.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_multipart_picker.dart';
import '../../utils/water_snack.dart';

class RainfallImportPanel extends StatelessWidget {
  const RainfallImportPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return FileImportPlaceholder(
      note: 'اسحب وأفلت ملفات .XLS أو .XLSX أو .ZIP الخاصة بالهطول',
      onPickFiles: () async {
        final files = await pickWaterMultipartFiles(
          allowedExtensions: ['xls', 'xlsx', 'zip'],
        );
        if (!context.mounted || files.isEmpty) return;
        context.read<RainfallBloc>().add(RainfallImportRequested(files));
      },
      onDownloadTemplate: () => downloadWaterTemplate(
        context,
        kind: 'rainfall',
        fallbackName: 'rainfall.xlsx',
      ),
      onClear: () async {
        final ok = await confirmWaterClear(context);
        if (!ok || !context.mounted) return;
        context.read<RainfallBloc>().add(const RainfallClearRequested());
      },
    );
  }
}
