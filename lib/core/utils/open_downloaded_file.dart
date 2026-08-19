import 'dart:io';

import 'package:dio/dio.dart';
import 'package:open_filex/open_filex.dart';

Options binaryDownloadOptions({Duration? receiveTimeout}) {
  return Options(
    responseType: ResponseType.bytes,
    receiveTimeout: receiveTimeout ?? const Duration(minutes: 2),
    headers: const {'Accept': '*/*'},
  );
}

String sanitizeDownloadFilename(String name) {
  var n = name.replaceAll('"', '').replaceAll("'", '');
  try {
    n = Uri.decodeComponent(n);
  } catch (_) {}
  n = n.replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1F]'), '_').trim();
  if (n.isEmpty) return 'download.bin';
  return n;
}

String filenameFromResponse(Response res, String fallback) {
  final cd = res.headers.value('content-disposition') ?? '';
  final star = RegExp(
    r"filename\*=(?:UTF-8'')?([^;]+)",
    caseSensitive: false,
  ).firstMatch(cd);
  if (star != null) {
    return sanitizeDownloadFilename(star.group(1)!.trim());
  }
  final match = RegExp(
    r'filename[^;=\n]*=[\s"]*([^";\n]+)',
    caseSensitive: false,
  ).firstMatch(cd);
  if (match != null) {
    return sanitizeDownloadFilename(match.group(1)!.trim());
  }
  return sanitizeDownloadFilename(fallback);
}

bool bytesLookLikeErrorPayload(List<int> bytes) {
  if (bytes.isEmpty) return true;
  final sample = String.fromCharCodes(bytes.take(160)).trimLeft();
  final lower = sample.toLowerCase();
  if (lower.startsWith('<!doctype') || lower.startsWith('<html')) return true;
  if (sample.startsWith('{') &&
      (sample.contains('"detail"') ||
          sample.contains('"non_field_errors"'))) {
    return true;
  }
  return false;
}

List<int>? bytesFromResponse(Response res) {
  final data = res.data;
  if (data is List<int>) return data;
  return null;
}

Future<void> saveAndOpenBytes(
  List<int> bytes, {
  required String filename,
}) async {
  final path =
      '${Directory.systemTemp.path}${Platform.pathSeparator}${sanitizeDownloadFilename(filename)}';
  final file = File(path);
  await file.writeAsBytes(bytes, flush: true);
  await OpenFilex.open(path);
}
