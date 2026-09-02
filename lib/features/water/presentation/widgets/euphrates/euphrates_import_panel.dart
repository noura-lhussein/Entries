import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../../core/widgets/shared_widgets.dart';
import '../../bloc/euphrates/euphrates_bloc.dart';
import '../../bloc/euphrates/euphrates_event.dart';
import '../../utils/water_file_actions.dart';
import '../../utils/water_multipart_picker.dart';
import '../../utils/water_snack.dart';

class EuphratesImportPanel extends StatelessWidget {
  const EuphratesImportPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return FileImportPlaceholder(
      note: 'اسحب وأفلت ملفات .XLS أو .XLSX الخاصة بالوارد المائي',
      onPickFiles: () async {
        final files = await pickWaterMultipartFiles(
          allowedExtensions: ['xls', 'xlsx'],
        );
        if (!context.mounted || files.isEmpty) return;
        context.read<EuphratesBloc>().add(EuphratesImportRequested(files));
      },
      onDownloadTemplate: () => downloadWaterTemplate(
        context,
        kind: 'euphrates',
        fallbackName: 'euphrates.xlsx',
      ),
      onClear: () async {
        final ok = await confirmWaterClear(context);
        if (!ok || !context.mounted) return;
        context.read<EuphratesBloc>().add(const EuphratesClearRequested());
      },
    );
  }
}
