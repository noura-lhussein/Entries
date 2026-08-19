enum DataEntrySectorFilter { electricity, water, petroleum, mineral, all }

enum SectionEntryStatus { empty, draft, complete, error }

enum DataEntrySavePhase { idle, saving, saved, failed }

class BuilderNamedItem {
  final int id;
  final String name;
  const BuilderNamedItem({required this.id, required this.name});

  factory BuilderNamedItem.fromJson(Map<String, dynamic> json) =>
      BuilderNamedItem(
        id: _asInt(json['id']) ?? 0,
        name: json['name']?.toString() ?? '',
      );
}

class BuilderSubSection {
  final int id;
  final String name;
  final int mainSectionId;
  const BuilderSubSection({
    required this.id,
    required this.name,
    required this.mainSectionId,
  });

  factory BuilderSubSection.fromJson(Map<String, dynamic> json) =>
      BuilderSubSection(
        id: _asInt(json['id']) ?? 0,
        name: json['name']?.toString() ?? '',
        mainSectionId: _asInt(json['main_section_id']) ??
            _asInt(json['main_section']) ??
            0,
      );
}

class BuilderTitle {
  final int id;
  final String name;
  final int order;
  final int? categoryId;
  final String? categoryName;
  const BuilderTitle({
    required this.id,
    required this.name,
    required this.order,
    this.categoryId,
    this.categoryName,
  });

  factory BuilderTitle.fromJson(Map<String, dynamic> json) => BuilderTitle(
        id: _asInt(json['id']) ?? 0,
        name: json['name']?.toString() ?? '',
        order: _asInt(json['order']) ?? 0,
        categoryId: _asInt(json['category']),
        categoryName: json['category_name']?.toString(),
      );
}

class BuilderSelectOption {
  final int id;
  final String label;
  const BuilderSelectOption({required this.id, required this.label});

  factory BuilderSelectOption.fromJson(Map<String, dynamic> json) =>
      BuilderSelectOption(
        id: _asInt(json['id']) ?? 0,
        label: (json['label'] ?? json['name'] ?? json['value'])?.toString() ??
            '',
      );
}

class FormSchemaGroup {
  final String id;
  final String titleAr;
  final int order;
  final bool collapsedByDefault;
  const FormSchemaGroup({
    required this.id,
    required this.titleAr,
    required this.order,
    this.collapsedByDefault = false,
  });

  factory FormSchemaGroup.fromJson(Map<String, dynamic> json) =>
      FormSchemaGroup(
        id: json['id']?.toString() ?? '',
        titleAr: json['title_ar']?.toString() ?? '',
        order: _asInt(json['order']) ?? 0,
        collapsedByDefault: json['collapsed_by_default'] == true,
      );
}

class FormSchemaField {
  final int id;
  final String key;
  final String labelAr;
  final String type;
  final String group;
  final int order;
  final bool required;
  final String? unitAr;
  final bool readonly;
  final String? helpAr;
  final String? computedFrom;
  final num? min;
  final num? max;
  final String? maxField;
  final String? warnIfGtField;
  final String? messageAr;
  final int? decimals;
  final List<BuilderSelectOption> options;

  const FormSchemaField({
    required this.id,
    required this.key,
    required this.labelAr,
    required this.type,
    required this.group,
    required this.order,
    required this.required,
    this.unitAr,
    this.readonly = false,
    this.helpAr,
    this.computedFrom,
    this.min,
    this.max,
    this.maxField,
    this.warnIfGtField,
    this.messageAr,
    this.decimals,
    this.options = const [],
  });

  factory FormSchemaField.fromJson(Map<String, dynamic> json) {
    final rawOpts = json['options'];
    return FormSchemaField(
      id: _asInt(json['id']) ?? 0,
      key: json['key']?.toString() ?? '',
      labelAr: json['label_ar']?.toString() ?? json['label']?.toString() ?? '',
      type: json['type']?.toString() ?? 'text',
      group: json['group']?.toString() ?? 'other',
      order: _asInt(json['order']) ?? 0,
      required: json['required'] == true,
      unitAr: json['unit_ar']?.toString(),
      readonly: json['readonly'] == true,
      helpAr: json['help_ar']?.toString(),
      computedFrom: json['computed_from']?.toString(),
      min: json['min'] is num ? json['min'] as num : num.tryParse('${json['min'] ?? ''}'),
      max: json['max'] is num ? json['max'] as num : num.tryParse('${json['max'] ?? ''}'),
      maxField: json['max_field']?.toString(),
      warnIfGtField: json['warn_if_gt_field']?.toString(),
      messageAr: json['message_ar']?.toString(),
      decimals: _asInt(json['decimals']),
      options: rawOpts is List
          ? rawOpts
              .whereType<Map>()
              .map((e) =>
                  BuilderSelectOption.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : const [],
    );
  }

  bool get isNumber => type == 'number';
  bool get isDate => type == 'date';
  bool get isBoolean => type == 'boolean';
  bool get isTextarea => type == 'textarea';
  bool get isLocation => kLocationAttributeTypes.contains(type);
  bool get isEntity => kEntityAttributeTypes.contains(type);
  bool get isDropdown =>
      type == 'select' || isLocation || isEntity;
  bool get isFile => type == 'file' || type == 'image';
  bool get isFullWidth => type == 'textarea' || type == 'text';
}

class FormSchemaSection {
  final int id;
  final int order;
  final String titleAr;
  final String? subtitleAr;
  final String mode;
  final List<FormSchemaGroup> groups;
  final List<String> previewFieldKeys;

  const FormSchemaSection({
    required this.id,
    required this.order,
    required this.titleAr,
    this.subtitleAr,
    this.mode = '',
    this.groups = const [],
    this.previewFieldKeys = const [],
  });

  factory FormSchemaSection.fromJson(Map<String, dynamic> json) {
    final groups = json['groups'];
    final keys = json['preview_field_keys'];
    return FormSchemaSection(
      id: _asInt(json['id']) ?? 0,
      order: _asInt(json['order']) ?? 0,
      titleAr: json['title_ar']?.toString() ?? '',
      subtitleAr: json['subtitle_ar']?.toString(),
      mode: json['mode']?.toString() ?? '',
      groups: groups is List
          ? groups
              .whereType<Map>()
              .map((e) => FormSchemaGroup.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : const [],
      previewFieldKeys: keys is List
          ? keys.map((e) => e.toString()).toList()
          : const [],
    );
  }
}

class FormSchemaPayload {
  final FormSchemaSection section;
  final List<FormSchemaField> fields;
  const FormSchemaPayload({required this.section, required this.fields});

  factory FormSchemaPayload.fromJson(Map<String, dynamic> json) {
    final sectionRaw = json['section'];
    final fieldsRaw = json['fields'];
    return FormSchemaPayload(
      section: sectionRaw is Map
          ? FormSchemaSection.fromJson(Map<String, dynamic>.from(sectionRaw))
          : const FormSchemaSection(id: 0, order: 0, titleAr: ''),
      fields: fieldsRaw is List
          ? fieldsRaw
              .whereType<Map>()
              .map((e) =>
                  FormSchemaField.fromJson(Map<String, dynamic>.from(e)))
              .toList()
          : const [],
    );
  }
}

class InfoHistoryRow {
  final String rowId;
  final Map<String, String> fields;
  const InfoHistoryRow({required this.rowId, required this.fields});

  factory InfoHistoryRow.fromJson(Map<String, dynamic> json) {
    final raw = json['fields'];
    final fields = <String, String>{};
    if (raw is Map) {
      for (final e in raw.entries) {
        fields[e.key.toString()] = e.value?.toString() ?? '';
      }
    }
    return InfoHistoryRow(
      rowId: json['row_id']?.toString() ?? '',
      fields: fields,
    );
  }
}

class DateCheckResult {
  final bool duplicate;
  final String? detail;
  const DateCheckResult({required this.duplicate, this.detail});

  factory DateCheckResult.fromJson(Map<String, dynamic> json) =>
      DateCheckResult(
        duplicate: json['duplicate'] == true,
        detail: json['detail']?.toString(),
      );
}

class UserBuilderPermissions {
  final List<int> subMainIds;
  final List<int> titleIds;
  const UserBuilderPermissions({
    this.subMainIds = const [],
    this.titleIds = const [],
  });

  factory UserBuilderPermissions.fromJson(Map<String, dynamic> json) =>
      UserBuilderPermissions(
        subMainIds: _asIntList(json['sub_main_ids']),
        titleIds: _asIntList(json['title_ids']),
      );
}

class GroupedSchemaFields {
  final FormSchemaGroup group;
  final List<FormSchemaField> fields;
  const GroupedSchemaFields({required this.group, required this.fields});
}

const Set<String> kLocationAttributeTypes = {
  'city',
  'district',
  'sub_district',
  'community',
};

const Set<String> kEntityAttributeTypes = {
  'drinking_station',
  'dam',
  'rainfall_station',
  'rainfall_basin',
  'spring',
  'lake',
  'river',
  'stream',
  'geology_unit',
  'power_plant',
  'substation',
  'transmission_line',
  'power_gis_substation_66',
  'power_gis_substation_230',
  'power_gis_substation_400',
  'power_gis_renewable',
  'fuel_tank_station',
  'hydro_dam',
  'load_governorate',
  'oil_field',
  'oil_well',
  'oil_refinery',
  'fuel_station',
  'storage_depot',
  'pipeline',
};

List<BuilderTitle> sortBuilderTitles(Iterable<BuilderTitle> titles) {
  final list = titles.toList();
  list.sort((a, b) {
    final catA = a.categoryId ?? 1 << 30;
    final catB = b.categoryId ?? 1 << 30;
    final byCat = catA.compareTo(catB);
    if (byCat != 0) return byCat;
    final byOrder = a.order.compareTo(b.order);
    if (byOrder != 0) return byOrder;
    return a.id.compareTo(b.id);
  });
  return list;
}

List<GroupedSchemaFields> groupSchemaFields(FormSchemaPayload schema) {
  final byGroup = <String, List<FormSchemaField>>{};
  final fields = [...schema.fields]..sort((a, b) => a.order.compareTo(b.order));
  for (final f in fields) {
    final gid = f.group.isEmpty ? 'other' : f.group;
    byGroup.putIfAbsent(gid, () => []).add(f);
  }
  final groups = [...schema.section.groups]
    ..sort((a, b) => a.order.compareTo(b.order));
  final known = groups.map((g) => g.id).toSet();
  final result = <GroupedSchemaFields>[];
  for (final g in groups) {
    final items = byGroup[g.id] ?? const <FormSchemaField>[];
    if (items.isNotEmpty) {
      result.add(GroupedSchemaFields(group: g, fields: items));
    }
  }
  for (final entry in byGroup.entries) {
    if (known.contains(entry.key) || entry.value.isEmpty) continue;
    result.add(
      GroupedSchemaFields(
        group: FormSchemaGroup(
          id: entry.key,
          titleAr: entry.key == 'other' ? 'أخرى' : entry.key,
          order: 999,
          collapsedByDefault: true,
        ),
        fields: entry.value,
      ),
    );
  }
  return result;
}

bool matchesSectorName(String name, DataEntrySectorFilter filter) {
  if (filter == DataEntrySectorFilter.all) return true;
  final n = name.toLowerCase();
  switch (filter) {
    case DataEntrySectorFilter.electricity:
      return n.contains('كهرب') ||
          n.contains('electric') ||
          n.contains('power');
    case DataEntrySectorFilter.water:
      return n.contains('ماء') || n.contains('مياه') || n.contains('water');
    case DataEntrySectorFilter.petroleum:
      return n.contains('نفط') ||
          n.contains('بترول') ||
          n.contains('غاز') ||
          n.contains('oil') ||
          n.contains('gas') ||
          n.contains('petroleum');
    case DataEntrySectorFilter.mineral:
      return n.contains('تعدين') ||
          n.contains('جيول') ||
          n.contains('mineral') ||
          n.contains('geolog');
    case DataEntrySectorFilter.all:
      return true;
  }
}

int? _asInt(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is Map && value['id'] != null) return _asInt(value['id']);
  return int.tryParse(value.toString());
}

List<int> _asIntList(dynamic value) {
  if (value is! List) return const [];
  return value.map(_asInt).whereType<int>().toList();
}
