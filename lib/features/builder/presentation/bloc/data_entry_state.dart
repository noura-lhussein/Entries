import 'package:equatable/equatable.dart';

import '../../data/models/builder_models.dart';

class DataEntryState extends Equatable {
  final DataEntrySectorFilter sector;
  final bool isAdmin;
  final bool bootstrapping;
  final bool loadingSubs;
  final bool loadingSchema;
  final String? loadError;

  final List<BuilderNamedItem> mainSections;
  final List<BuilderSubSection> subSections;
  final List<BuilderTitle> titles;
  final int? selectedMainId;
  final int? selectedSubId;
  final int? selectedTitleId;

  final FormSchemaPayload? schema;
  final Map<String, String> values;
  final Map<String, String> fieldErrors;
  final Map<String, String> fieldWarnings;
  final Map<String, bool> collapsedGroups;
  final Map<int, SectionEntryStatus> sectionStatus;
  final Map<String, List<BuilderSelectOption>> entityOptions;
  final List<BuilderSelectOption> governorates;
  final List<BuilderSelectOption> districts;
  final List<BuilderSelectOption> subdistricts;
  final List<BuilderSelectOption> communities;

  final List<InfoHistoryRow> historyRows;
  final bool historyOpen;
  final Set<String> expandedHistoryIds;
  final String? dateDuplicateWarning;

  final DataEntrySavePhase savePhase;
  final String? lastSavedAt;
  final String? saveMessage;

  const DataEntryState({
    this.sector = DataEntrySectorFilter.electricity,
    this.isAdmin = false,
    this.bootstrapping = true,
    this.loadingSubs = false,
    this.loadingSchema = false,
    this.loadError,
    this.mainSections = const [],
    this.subSections = const [],
    this.titles = const [],
    this.selectedMainId,
    this.selectedSubId,
    this.selectedTitleId,
    this.schema,
    this.values = const {},
    this.fieldErrors = const {},
    this.fieldWarnings = const {},
    this.collapsedGroups = const {},
    this.sectionStatus = const {},
    this.entityOptions = const {},
    this.governorates = const [],
    this.districts = const [],
    this.subdistricts = const [],
    this.communities = const [],
    this.historyRows = const [],
    this.historyOpen = false,
    this.expandedHistoryIds = const {},
    this.dateDuplicateWarning,
    this.savePhase = DataEntrySavePhase.idle,
    this.lastSavedAt,
    this.saveMessage,
  });

  BuilderTitle? get activeTitle {
    final id = selectedTitleId;
    if (id == null) return null;
    for (final t in titles) {
      if (t.id == id) return t;
    }
    return null;
  }

  List<GroupedSchemaFields> get groupedFields {
    final s = schema;
    if (s == null) return const [];
    return groupSchemaFields(s);
  }

  int get progressDone =>
      titles.where((t) => sectionStatus[t.id] == SectionEntryStatus.complete).length;

  DataEntryState copyWith({
    DataEntrySectorFilter? sector,
    bool? isAdmin,
    bool? bootstrapping,
    bool? loadingSubs,
    bool? loadingSchema,
    String? loadError,
    bool clearLoadError = false,
    List<BuilderNamedItem>? mainSections,
    List<BuilderSubSection>? subSections,
    List<BuilderTitle>? titles,
    int? selectedMainId,
    int? selectedSubId,
    int? selectedTitleId,
    bool clearMain = false,
    bool clearSub = false,
    bool clearTitle = false,
    FormSchemaPayload? schema,
    bool clearSchema = false,
    Map<String, String>? values,
    Map<String, String>? fieldErrors,
    Map<String, String>? fieldWarnings,
    Map<String, bool>? collapsedGroups,
    Map<int, SectionEntryStatus>? sectionStatus,
    Map<String, List<BuilderSelectOption>>? entityOptions,
    List<BuilderSelectOption>? governorates,
    List<BuilderSelectOption>? districts,
    List<BuilderSelectOption>? subdistricts,
    List<BuilderSelectOption>? communities,
    List<InfoHistoryRow>? historyRows,
    bool? historyOpen,
    Set<String>? expandedHistoryIds,
    String? dateDuplicateWarning,
    bool clearDateWarning = false,
    DataEntrySavePhase? savePhase,
    String? lastSavedAt,
    String? saveMessage,
    bool clearSaveMessage = false,
  }) {
    return DataEntryState(
      sector: sector ?? this.sector,
      isAdmin: isAdmin ?? this.isAdmin,
      bootstrapping: bootstrapping ?? this.bootstrapping,
      loadingSubs: loadingSubs ?? this.loadingSubs,
      loadingSchema: loadingSchema ?? this.loadingSchema,
      loadError: clearLoadError ? null : (loadError ?? this.loadError),
      mainSections: mainSections ?? this.mainSections,
      subSections: subSections ?? this.subSections,
      titles: titles ?? this.titles,
      selectedMainId: clearMain ? null : (selectedMainId ?? this.selectedMainId),
      selectedSubId: clearSub ? null : (selectedSubId ?? this.selectedSubId),
      selectedTitleId:
          clearTitle ? null : (selectedTitleId ?? this.selectedTitleId),
      schema: clearSchema ? null : (schema ?? this.schema),
      values: values ?? this.values,
      fieldErrors: fieldErrors ?? this.fieldErrors,
      fieldWarnings: fieldWarnings ?? this.fieldWarnings,
      collapsedGroups: collapsedGroups ?? this.collapsedGroups,
      sectionStatus: sectionStatus ?? this.sectionStatus,
      entityOptions: entityOptions ?? this.entityOptions,
      governorates: governorates ?? this.governorates,
      districts: districts ?? this.districts,
      subdistricts: subdistricts ?? this.subdistricts,
      communities: communities ?? this.communities,
      historyRows: historyRows ?? this.historyRows,
      historyOpen: historyOpen ?? this.historyOpen,
      expandedHistoryIds: expandedHistoryIds ?? this.expandedHistoryIds,
      dateDuplicateWarning: clearDateWarning
          ? null
          : (dateDuplicateWarning ?? this.dateDuplicateWarning),
      savePhase: savePhase ?? this.savePhase,
      lastSavedAt: lastSavedAt ?? this.lastSavedAt,
      saveMessage:
          clearSaveMessage ? null : (saveMessage ?? this.saveMessage),
    );
  }

  @override
  List<Object?> get props => [
        sector,
        isAdmin,
        bootstrapping,
        loadingSubs,
        loadingSchema,
        loadError,
        mainSections,
        subSections,
        titles,
        selectedMainId,
        selectedSubId,
        selectedTitleId,
        schema,
        values,
        fieldErrors,
        fieldWarnings,
        collapsedGroups,
        sectionStatus,
        entityOptions,
        governorates,
        districts,
        subdistricts,
        communities,
        historyRows,
        historyOpen,
        expandedHistoryIds,
        dateDuplicateWarning,
        savePhase,
        lastSavedAt,
        saveMessage,
      ];
}
