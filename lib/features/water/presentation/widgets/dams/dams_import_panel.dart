import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/dams/dams_bloc.dart';
import '../../bloc/dams/dams_event.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_multipart_picker.dart';
import '../../utils/water_snack.dart';

class DamsImportPanel extends StatelessWidget {
  const DamsImportPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return FileImportPlaceholder(
      note: 'اسحب وأفلت ملفات .XLS أو .XLSX الخاصة بالسدود',
      onPickFiles: () async {
        final files = await pickWaterMultipartFiles(
          allowedExtensions: ['xls', 'xlsx'],
        );
        if (!context.mounted || files.isEmpty) return;
        context.read<DamsBloc>().add(DamsImportRequested(files));
      },
      onDownloadTemplate: () => downloadWaterTemplate(
        context,
        kind: 'dams-storage',
        fallbackName: 'dams-storage.xlsx',
      ),
      onClear: () async {
        final ok = await confirmWaterClear(context);
        if (!ok || !context.mounted) return;
        context.read<DamsBloc>().add(const DamsClearRequested());
      },
    );
  }
}
