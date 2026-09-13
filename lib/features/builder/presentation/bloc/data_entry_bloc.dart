import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../../core/network/user_facing_error.dart';
import '../../data/datasources/builder_remote_data_source.dart';
import '../../data/models/builder_models.dart';
import '../utils/data_entry_logic.dart';
import '../utils/filter_defaults.dart';
import 'data_entry_event.dart';
import 'data_entry_state.dart';

const kBuilderUnavailableMessage =
    'خدمة الإدخال غير متاحة على السيرفر حالياً. التطبيق يعمل، وأعد المحاولة بعد رفع الواجهة.';

class DataEntryBloc extends Bloc<DataEntryEvent, DataEntryState> {
  DataEntryBloc(this._remote) : super(const DataEntryState()) {
    on<DataEntryStarted>(_onStarted);
    on<MainSectionSelected>(_onMainSelected);
    on<SubSectionSelected>(_onSubSelected);
    on<TitleSelected>(_onTitleSelected);
    on<FieldValueChanged>(_onFieldChanged);
    on<FieldBlurred>(_onFieldBlurred);
    on<GroupToggled>(_onGroupToggled);
    on<HistoryToggled>(_onHistoryToggled);
    on<HistoryRowToggled>(_onHistoryRowToggled);
    on<HistoryReloadRequested>(_onHistoryReload);
    on<SaveDraftRequested>(_onSaveDraft);
    on<CommitAndNextRequested>(_onCommitAndNext);
  }

  final BuilderRemoteDataSource _remote;
  int _schemaToken = 0;
  List<int> _allowedSubMainIds = const [];

  Future<void> _onStarted(
    DataEntryStarted event,
    Emitter<DataEntryState> emit,
  ) async {
    emit(DataEntryState(
      sector: event.sector,
      isAdmin: event.isAdmin,
      bootstrapping: true,
    ));
    _allowedSubMainIds = const [];
    try {
      final fetched = await Future.wait<Object>([
        _remote.getMainSections(),
        _remote.getTitles(),
        _remote.getGovernorates(),
        event.isAdmin
            ? Future.value(const UserBuilderPermissions())
            : _remote.getPermissions(),
      ], eagerError: false);
      var mains = fetched[0] as List<BuilderNamedItem>;
      var titles = fetched[1] as List<BuilderTitle>;
      final governorates = fetched[2] as List<BuilderSelectOption>;
      final perms = fetched[3] as UserBuilderPermissions;

      if (mains.isEmpty && titles.isEmpty) {
        emit(state.copyWith(
          bootstrapping: false,
          loadError: kBuilderUnavailableMessage,
        ));
        return;
      }

      if (!event.isAdmin) {
        _allowedSubMainIds = perms.subMainIds;
      }

      mains = filterMainsForSector(
        mains: mains,
        sector: event.sector,
      );
      titles = filterTitlesForSector(
        titles: titles,
        sector: event.sector,
        isAdmin: event.isAdmin,
        allowedTitleIds: perms.titleIds,
        allowedCategoryIds: perms.titleCategoryIds,
      );

      emit(state.copyWith(
        bootstrapping: false,
        clearLoadError: true,
        mainSections: mains,
        titles: titles,
        governorates: governorates,
      ));
      final onlyMain = soleItem(mains);
      if (onlyMain != null) {
        add(MainSectionSelected(onlyMain.id));
      }
    } catch (e) {
      emit(state.copyWith(
        bootstrapping: false,
        loadError: userFacingErrorMessage(
          e,
          fallback: kBuilderUnavailableMessage,
        ),
      ));
    }
  }

  Future<void> _onMainSelected(
    MainSectionSelected event,
    Emitter<DataEntryState> emit,
  ) async {
    emit(state.copyWith(
      selectedMainId: event.mainId,
      clearMain: event.mainId == null,
      clearSub: true,
      subSections: const [],
      loadingSubs: event.mainId != null,
      historyRows: const [],
    ));
    if (event.mainId == null) return;
    try {
      var subs = await _remote.getSubSections(mainSectionId: event.mainId);
      if (!state.isAdmin) {
        final allow = _allowedSubMainIds.toSet();
        subs = subs.where((s) => allow.contains(s.id)).toList();
      }
      emit(state.copyWith(subSections: subs, loadingSubs: false));
      final only = soleItem(subs);
      if (only != null) {
        add(SubSectionSelected(only.id));
      } else if (state.selectedSubId != null &&
          !subs.any((s) => s.id == state.selectedSubId)) {
        add(const SubSectionSelected(null));
      }
    } catch (_) {
      emit(state.copyWith(
        loadingSubs: false,
        loadError: 'تعذّر تحميل الأقسام الفرعية',
      ));
    }
  }

  Future<void> _onSubSelected(
    SubSectionSelected event,
    Emitter<DataEntryState> emit,
  ) async {
    emit(state.copyWith(
      selectedSubId: event.subId,
      clearSub: event.subId == null,
      historyRows: const [],
    ));
    if (event.subId == null) return;
    if (state.selectedTitleId != null) {
      await _loadHistory(emit);
    } else if (state.titles.isNotEmpty) {
      add(TitleSelected(state.titles.first.id));
    }
  }

  Future<void> _onTitleSelected(
    TitleSelected event,
    Emitter<DataEntryState> emit,
  ) async {
    final token = ++_schemaToken;
    emit(state.copyWith(
      selectedTitleId: event.titleId,
      loadingSchema: true,
      clearSchema: true,
      clearLoadError: true,
      values: const {},
      fieldErrors: const {},
      fieldWarnings: const {},
      clearDateWarning: true,
      savePhase: DataEntrySavePhase.idle,
      clearSaveMessage: true,
    ));
    try {
      final schema = await _remote.getFormSchema(event.titleId);
      if (token != _schemaToken) return;
      if (schema == null) {
        emit(state.copyWith(
          loadingSchema: false,
          loadError: kBuilderUnavailableMessage,
        ));
        return;
      }
      final collapsed = <String, bool>{
        for (final g in schema.section.groups) g.id: g.collapsedByDefault,
      };
      emit(state.copyWith(
        schema: schema,
        loadingSchema: false,
        collapsedGroups: collapsed,
        values: {for (final f in schema.fields) f.key: ''},
      ));
      await _loadEntityOptions(schema, emit);
      await _loadHistory(emit);
    } catch (_) {
      if (token != _schemaToken) return;
      emit(state.copyWith(
        loadingSchema: false,
        loadError: 'تعذّر تحميل النموذج',
      ));
    }
  }

  Future<void> _loadEntityOptions(
    FormSchemaPayload schema,
    Emitter<DataEntryState> emit,
  ) async {
    final types = schema.fields
        .where((f) => f.isEntity)
        .map((f) => f.type)
        .toSet();
    if (types.isEmpty) return;
    final next = Map<String, List<BuilderSelectOption>>.from(state.entityOptions);
    for (final type in types) {
      try {
        next[type] = await _remote.getEntityOptions(type);
      } catch (_) {
        next[type] = const [];
      }
    }
    emit(state.copyWith(entityOptions: next));
  }

  Future<void> _onFieldChanged(
    FieldValueChanged event,
    Emitter<DataEntryState> emit,
  ) async {
    final schema = state.schema;
    if (schema == null) return;
    var values = Map<String, String>.from(state.values)..[event.key] = event.value;
    values = applyComputedAndWarnings(fields: schema.fields, values: values);
    final warnings = collectWarnings(fields: schema.fields, values: values);
    final errors = Map<String, String>.from(state.fieldErrors)..remove(event.key);

    var districts = state.districts;
    var subdistricts = state.subdistricts;
    var communities = state.communities;
    final cityKey = fieldKeyOfType(schema.fields, 'city');
    final districtKey = fieldKeyOfType(schema.fields, 'district');
    final subdistrictKey = fieldKeyOfType(schema.fields, 'sub_district');
    final communityKey = fieldKeyOfType(schema.fields, 'community');

    if (cityKey != null && event.key == cityKey) {
      if (districtKey != null) values[districtKey] = '';
      if (subdistrictKey != null) values[subdistrictKey] = '';
      if (communityKey != null) values[communityKey] = '';
      districts = const [];
      subdistricts = const [];
      communities = const [];
      emit(state.copyWith(
        values: values,
        fieldErrors: errors,
        fieldWarnings: warnings,
        districts: districts,
        subdistricts: subdistricts,
        communities: communities,
      ));
      final govId = int.tryParse(event.value);
      if (govId != null) {
        try {
          districts = await _remote.getDistricts(govId);
        } catch (_) {}
        emit(state.copyWith(districts: districts));
      }
      return;
    }

    if (districtKey != null && event.key == districtKey) {
      if (subdistrictKey != null) values[subdistrictKey] = '';
      if (communityKey != null) values[communityKey] = '';
      subdistricts = const [];
      communities = const [];
      emit(state.copyWith(
        values: values,
        fieldErrors: errors,
        fieldWarnings: warnings,
        subdistricts: subdistricts,
        communities: communities,
      ));
      final distId = int.tryParse(event.value);
      if (distId != null) {
        try {
          subdistricts = await _remote.getSubdistricts(distId);
        } catch (_) {}
        emit(state.copyWith(subdistricts: subdistricts));
      }
      return;
    }

    if (subdistrictKey != null && event.key == subdistrictKey) {
      if (communityKey != null) values[communityKey] = '';
      communities = const [];
      emit(state.copyWith(
        values: values,
        fieldErrors: errors,
        fieldWarnings: warnings,
        communities: communities,
      ));
      final subId = int.tryParse(event.value);
      if (subId != null) {
        try {
          communities = await _remote.getCommunities(subId);
        } catch (_) {}
        emit(state.copyWith(communities: communities));
      }
      return;
    }

    emit(state.copyWith(
      values: values,
      fieldErrors: errors,
      fieldWarnings: warnings,
    ));
  }

  Future<void> _onFieldBlurred(
    FieldBlurred event,
    Emitter<DataEntryState> emit,
  ) async {
    final schema = state.schema;
    if (schema == null) return;
    FormSchemaField? field;
    for (final f in schema.fields) {
      if (f.key == event.key) {
        field = f;
        break;
      }
    }
    if (field == null || field.readonly) return;
    final error = validateField(field, state.values);
    final errors = Map<String, String>.from(state.fieldErrors);
    if (error == null) {
      errors.remove(field.key);
    } else {
      errors[field.key] = error;
    }
    emit(state.copyWith(fieldErrors: errors));
    if (isReportDateField(field) || field.isEntity) {
      await _checkDuplicateDate(emit, field: isReportDateField(field) ? field : null);
    }
  }

  Future<void> _checkDuplicateDate(
    Emitter<DataEntryState> emit, {
    FormSchemaField? field,
  }) async {
    final schema = state.schema;
    final titleId = state.selectedTitleId;
    final subId = state.selectedSubId;
    if (schema == null || titleId == null || subId == null) {
      emit(state.copyWith(clearDateWarning: true));
      return;
    }
    final dateField = field != null && isReportDateField(field)
        ? field
        : findReportDateField(schema.fields);
    if (dateField == null) {
      emit(state.copyWith(clearDateWarning: true));
      return;
    }
    final dateValue = normalizeDateValue(state.values[dateField.key]);
    if (dateValue == null) {
      emit(state.copyWith(clearDateWarning: true));
      return;
    }
    final entity = currentEntityFromValues(schema.fields, state.values);
    try {
      final res = await _remote.checkReportDate(
        titleId: titleId,
        subMainId: subId,
        date: dateValue,
        entityType: entity.entityType,
        entityId: entity.entityId,
      );
      if (res.duplicate) {
        final msg = res.detail?.trim().isNotEmpty == true
            ? res.detail!
            : 'يوجد تقرير مسجّل مسبقاً لهذا القسم بتاريخ $dateValue. لا يمكن إدخال أكثر من تقرير لنفس التاريخ.';
        final errors = Map<String, String>.from(state.fieldErrors)
          ..[dateField.key] = msg;
        emit(state.copyWith(
          dateDuplicateWarning: msg,
          fieldErrors: errors,
        ));
      } else {
        final errors = Map<String, String>.from(state.fieldErrors);
        if (errors[dateField.key]?.contains('نفس التاريخ') == true) {
          errors.remove(dateField.key);
        }
        emit(state.copyWith(
          clearDateWarning: true,
          fieldErrors: errors,
        ));
      }
    } catch (_) {}
  }

  void _onGroupToggled(GroupToggled event, Emitter<DataEntryState> emit) {
    final next = Map<String, bool>.from(state.collapsedGroups);
    next[event.groupId] = !(next[event.groupId] ?? false);
    emit(state.copyWith(collapsedGroups: next));
  }

  void _onHistoryToggled(HistoryToggled event, Emitter<DataEntryState> emit) {
    emit(state.copyWith(historyOpen: !state.historyOpen));
  }

  void _onHistoryRowToggled(
    HistoryRowToggled event,
    Emitter<DataEntryState> emit,
  ) {
    final next = Set<String>.from(state.expandedHistoryIds);
    if (next.contains(event.rowId)) {
      next.remove(event.rowId);
    } else {
      next.add(event.rowId);
    }
    emit(state.copyWith(expandedHistoryIds: next));
  }

  Future<void> _onHistoryReload(
    HistoryReloadRequested event,
    Emitter<DataEntryState> emit,
  ) async {
    if (event.openHistory) {
      emit(state.copyWith(historyOpen: true));
    }
    await _loadHistory(emit);
  }

  Future<void> _onSaveDraft(
    SaveDraftRequested event,
    Emitter<DataEntryState> emit,
  ) =>
      _persist(emit, requireComplete: false);

  Future<void> _onCommitAndNext(
    CommitAndNextRequested event,
    Emitter<DataEntryState> emit,
  ) async {
    final ok = await _persist(emit, requireComplete: true);
    if (!ok) return;
    final idx = state.titles.indexWhere((t) => t.id == state.selectedTitleId);
    if (idx >= 0 && idx < state.titles.length - 1) {
      add(TitleSelected(state.titles[idx + 1].id));
    }
  }

  Future<bool> _persist(
    Emitter<DataEntryState> emit, {
    required bool requireComplete,
  }) async {
    final schema = state.schema;
    final titleId = state.selectedTitleId;
    final subId = state.selectedSubId;
    if (schema == null || titleId == null || subId == null) {
      emit(state.copyWith(saveMessage: 'اختر القسم الفرعي أولاً'));
      return false;
    }

    if (requireComplete) {
      final errors = validateRequired(schema.fields, state.values);
      emit(state.copyWith(fieldErrors: errors));
      if (errors.isNotEmpty) {
        _markSection(emit, SectionEntryStatus.error);
        emit(state.copyWith(
          savePhase: DataEntrySavePhase.failed,
          saveMessage: 'أكمل الحقول المطلوبة قبل الاعتماد',
        ));
        return false;
      }
    }

    if (state.dateDuplicateWarning != null) {
      _markSection(emit, SectionEntryStatus.error);
      emit(state.copyWith(
        savePhase: DataEntrySavePhase.failed,
        saveMessage: state.dateDuplicateWarning,
      ));
      return false;
    }

    final attributeValues = collectAttributeValues(
      fields: schema.fields,
      values: state.values,
    );
    emit(state.copyWith(
      savePhase: DataEntrySavePhase.saving,
      clearSaveMessage: true,
    ));
    try {
      final ok = await _remote.submitReport(
        titleId: titleId,
        subMainId: subId,
        attributeValues: attributeValues,
      );
      if (!ok) {
        emit(state.copyWith(
          savePhase: DataEntrySavePhase.failed,
          saveMessage: kBuilderUnavailableMessage,
        ));
        return false;
      }
      final stamp = DateFormat.Hm('en').format(DateTime.now());
      _markSection(
        emit,
        requireComplete ? SectionEntryStatus.complete : SectionEntryStatus.draft,
      );
      emit(state.copyWith(
        savePhase: DataEntrySavePhase.saved,
        lastSavedAt: stamp,
        saveMessage: requireComplete ? 'تم اعتماد القسم' : 'حُفظت المسودة',
      ));
      await _loadHistory(emit);
      return true;
    } catch (e) {
      if (isDuplicateDateError(e)) {
        final msg = extractApiDetail(e) ??
            'يوجد تقرير مسجّل مسبقاً لهذا التاريخ. لا يمكن إدخال أكثر من تقرير لنفس التاريخ.';
        emit(state.copyWith(
          savePhase: DataEntrySavePhase.failed,
          dateDuplicateWarning: msg,
          saveMessage: msg,
        ));
        _markSection(emit, SectionEntryStatus.error);
        return false;
      }
      emit(state.copyWith(
        savePhase: DataEntrySavePhase.failed,
        saveMessage: userFacingErrorMessage(
          e,
          fallback: 'فشل الحفظ — القيم ما زالت في النموذج',
        ),
      ));
      return false;
    }
  }

  void _markSection(Emitter<DataEntryState> emit, SectionEntryStatus status) {
    final id = state.selectedTitleId;
    if (id == null) return;
    final next = Map<int, SectionEntryStatus>.from(state.sectionStatus)
      ..[id] = status;
    emit(state.copyWith(sectionStatus: next));
  }

  Future<void> _loadHistory(Emitter<DataEntryState> emit) async {
    final titleId = state.selectedTitleId;
    final subId = state.selectedSubId;
    if (titleId == null || subId == null) {
      emit(state.copyWith(historyRows: const []));
      return;
    }
    try {
      final rows = await _remote.getInfoRows(
        titleId: titleId,
        subMainId: subId,
      );
      emit(state.copyWith(historyRows: rows));
    } catch (_) {
      emit(state.copyWith(historyRows: const []));
    }
  }
}
