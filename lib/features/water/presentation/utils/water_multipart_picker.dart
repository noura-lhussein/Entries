import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';

Future<List<MultipartFile>> pickWaterMultipartFiles({
  required List<String> allowedExtensions,
}) async {
  final result = await FilePicker.platform.pickFiles(
    allowMultiple: true,
    type: FileType.custom,
    allowedExtensions: allowedExtensions,
  );
  if (result == null) return [];

  final files = <MultipartFile>[];
  for (final f in result.files) {
    final filename = f.name;
    if (f.path != null) {
      files.add(await MultipartFile.fromFile(
        f.path!,
        filename: filename,
      ));
    } else if (f.bytes != null) {
      files.add(MultipartFile.fromBytes(f.bytes!, filename: filename));
    }
  }
  return files;
}
