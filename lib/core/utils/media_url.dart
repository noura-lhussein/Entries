import '../network/api_constants.dart';

String? photoUrlFromJson(Map<String, dynamic> json) {
  for (final key in const [
    'photo',
    'avatar',
    'image',
    'profile_photo',
    'photo_url',
    'avatar_url',
    'image_url',
  ]) {
    final value = json[key];
    if (value is String && value.trim().isNotEmpty) return value.trim();
  }
  return null;
}

String? absoluteMediaUrl(String? raw) {
  if (raw == null) return null;
  final value = raw.trim();
  if (value.isEmpty) return null;
  if (value.startsWith('http://') ||
      value.startsWith('https://') ||
      value.startsWith('file:') ||
      value.startsWith('data:')) {
    return value;
  }
  final origin = ApiConstants.url.endsWith('/')
      ? ApiConstants.url.substring(0, ApiConstants.url.length - 1)
      : ApiConstants.url;
  if (value.startsWith('/')) return '$origin$value';
  return '$origin/$value';
}
