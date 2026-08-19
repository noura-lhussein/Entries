class WaterImportResultEntity {
  final bool ok;
  final String? messageEn;
  final String? messageAr;
  final String? errorEn;
  final String? errorAr;

  final String? output;
  final bool? cleared;
  final bool? created;

  const WaterImportResultEntity({
    required this.ok,
    this.messageEn,
    this.messageAr,
    this.errorEn,
    this.errorAr,
    this.output,
    this.cleared,
    this.created,
  });

  factory WaterImportResultEntity.fromJson(Map<String, dynamic> json) {
    return WaterImportResultEntity(
      ok: json['ok'] == true,
      messageEn: json['message_en'] as String?,
      messageAr: json['message_ar'] as String?,
      errorEn: json['error_en'] as String?,
      errorAr: json['error_ar'] as String?,
      output: json['output'] as String?,
      cleared: json['cleared'] as bool?,
      created: json['created'] as bool?,
    );
  }
}

