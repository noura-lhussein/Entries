import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Debug logger that keeps normal request/response logs, but truncates
/// known huge payloads (lookups, GeoJSON, catalogs) so they don't flood
/// the console and hide other traffic.
class SelectiveDioLogger extends Interceptor {
  static const int _maxChars = 1200;

  static const _bulkyPathFragments = [
    '/lookups/',
    '/geojson/',
    '/map-catalog/',
    '/spatial-layers/',
    '/preview/',
  ];

  bool _isBulky(RequestOptions options) {
    final path = options.uri.path.toLowerCase();
    return _bulkyPathFragments.any(path.contains);
  }

  void _log(String message) {
    if (kReleaseMode) return;
    debugPrint(message);
  }

  String _summarize(dynamic data, {required bool compact}) {
    if (data == null) return 'null';
    if (compact) {
      if (data is List) return 'List(${data.length} items)';
      if (data is Map) {
        final keys = data.keys.map((k) {
          final v = data[k];
          if (v is List) return '$k: List(${v.length})';
          if (v is Map) return '$k: Map(${v.length} keys)';
          return '$k: ${v.runtimeType}';
        }).join(', ');
        return 'Map{ $keys }';
      }
    }
    try {
      final raw = data is String ? data : jsonEncode(data);
      if (raw.length <= _maxChars) return raw;
      return '${raw.substring(0, _maxChars)}… [truncated ${raw.length} chars]';
    } catch (_) {
      return data.toString();
    }
  }

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _log('┌──────────────────────────────────────────────────────────────');
    _log('│ --> ${options.method} ${options.uri}');
    if (options.queryParameters.isNotEmpty) {
      _log('│ query: ${options.queryParameters}');
    }
    if (options.data != null) {
      _log('│ body: ${_summarize(options.data, compact: false)}');
    }
    _log('└──────────────────────────────────────────────────────────────');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    final bulky = _isBulky(response.requestOptions);
    _log('┌──────────────────────────────────────────────────────────────');
    _log(
      '│ <-- ${response.statusCode} ${response.requestOptions.method} '
      '${response.requestOptions.uri}',
    );
    if (bulky) {
      _log(
        '│ response: [large payload truncated] '
        '${_summarize(response.data, compact: true)}',
      );
    } else {
      _log('│ response: ${_summarize(response.data, compact: false)}');
    }
    _log('└──────────────────────────────────────────────────────────────');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _log('┌──────────────────────────────────────────────────────────────');
    _log(
      '│ *** ERROR ${err.response?.statusCode ?? '-'} '
      '${err.requestOptions.method} ${err.requestOptions.uri}',
    );
    _log('│ ${err.message}');
    if (err.response?.data != null) {
      _log(
        '│ error body: ${_summarize(err.response!.data, compact: false)}',
      );
    }
    _log('└──────────────────────────────────────────────────────────────');
    handler.next(err);
  }
}
