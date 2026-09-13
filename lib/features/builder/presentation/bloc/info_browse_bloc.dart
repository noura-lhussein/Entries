import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/datasources/builder_remote_data_source.dart';
import '../../data/models/builder_models.dart';
import '../utils/filter_defaults.dart';
import 'info_browse_event.dart';
import 'info_browse_state.dart';

class InfoBrowseBloc extends Bloc<InfoBrowseEvent, InfoBrowseState> {
  InfoBrowseBloc(this._remote) : super(const InfoBrowseState()) {
    on<InfoBrowseStarted>(_onStarted);
    on<InfoBrowseSearchChanged>(_onSearch);
    on<InfoBrowseMainFilterChanged>(_onMain);
    on<InfoBrowseSubFilterChanged>(_onSub);
    on<InfoBrowseCategoryFilterChanged>(_onCategory);
    on<InfoBrowseTitleFilterChanged>(_onTitle);
    on<InfoBrowseAttributeFilterChanged>(_onAttribute);
    on<InfoBrowseStatusFilterChanged>(_onStatus);
    on<InfoBrowseFromDateChanged>(_onFrom);
    on<InfoBrowseToDateChanged>(_onTo);
    on<InfoBrowseEnteredByChanged>(_onEnteredBy);
    on<InfoBrowseTitleToggled>(_onToggle);
    on<InfoBrowseLoadMore>(_onLoadMore);
    on<InfoBrowseRefreshed>(_onRefresh);
    on<InfoBrowseRowDeleteRequested>(_onDelete);
    on<InfoBrowseRowConfirmRequested>(_onConfirm);
    on<InfoBrowseRowCommitNoteRequested>(_onCommitNote);
    on<InfoBrowseActionCleared>(_onClearAction);
    on<InfoBrowseFilterCleared>(_onClearFilter);
    on<InfoBrowseFiltersCleared>(_onClearFilters);
    on<InfoBrowseFiltersApplied>(_onFiltersApplied);
  }

  final BuilderRemoteDataSource _remote;
  static const _pageSize = 10;

  Future<void> _onStarted(
    InfoBrowseStarted event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(InfoBrowseState(
      mode: event.mode,
      currentUserId: event.currentUserId,
      canWrite: event.canWrite,
      canConfirm: event.canConfirm,
      isAdmin: event.isAdmin,
      bootstrapping: true,
    ));
    try {
      final mains = await _remote.getMainSections();
      final subs = await _remote.getSubSections();
      final titles = await _remote.getTitles();
      final cats = await _remote.getTitleCategories();
      final attrs = await _remote.getAttributes();
      var users = const <BuilderNamedItem>[];
      if (event.isAdmin || event.mode == InfoBrowseMode.submitted) {
        try {
          users = await _remote.getUsers();
        } catch (_) {
          users = const [];
        }
      }
      final labels = <String, String>{};
      for (final a in attrs) {
        if (a.id > 0 && a.label.trim().isNotEmpty) {
          labels['${a.id}'] = a.label;
        }
      }
      emit(_withSoleDefaults(state.copyWith(
        bootstrapping: false,
        clearError: true,
        mainSections: mains,
        subSections: subs,
        titles: titles,
        titleCategories: cats,
        attributes: attrs,
        users: users,
        attributeLabels: labels,
      )));
      await _refreshCounts(emit);
    } catch (_) {
      emit(state.copyWith(
        bootstrapping: false,
        loadError: 'خطأ في تحميل البيانات',
      ));
    }
  }

  Future<void> _onSearch(
    InfoBrowseSearchChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(search: event.query));
    await _afterFilterChange(emit);
  }

  Future<void> _onMain(
    InfoBrowseMainFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(_withSoleDefaults(state.copyWith(
      mainId: event.mainId,
      clearMain: event.mainId == null,
    )));
    await _afterFilterChange(emit);
  }

  Future<void> _onSub(
    InfoBrowseSubFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      subId: event.subId,
      clearSub: event.subId == null,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onCategory(
    InfoBrowseCategoryFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    final patch = applyTitleCategoryFilterChange(
      prevTitleId: state.titleId,
      categoryId: event.categoryId,
      titles: state.titles,
    );
    emit(_withSoleDefaults(state.copyWith(
      titleCategoryId: patch.categoryId,
      clearCategory: patch.categoryId == null,
      titleId: patch.titleId,
      clearTitle: patch.titleId == null,
    )));
    await _afterFilterChange(emit);
  }

  Future<void> _onTitle(
    InfoBrowseTitleFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(_withSoleDefaults(state.copyWith(
      titleId: event.titleId,
      clearTitle: event.titleId == null,
    )));
    await _afterFilterChange(emit);
  }

  Future<void> _onAttribute(
    InfoBrowseAttributeFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      attributeId: event.attributeId,
      clearAttribute: event.attributeId == null,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onStatus(
    InfoBrowseStatusFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      confirmed: event.confirmed,
      clearConfirmed: event.confirmed == null || event.confirmed!.isEmpty,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onFrom(
    InfoBrowseFromDateChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      fromDate: event.from,
      clearFrom: event.from == null,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onTo(
    InfoBrowseToDateChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      toDate: event.to,
      clearTo: event.to == null,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onEnteredBy(
    InfoBrowseEnteredByChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      enteredByUserId: event.userId,
      clearEnteredBy: event.userId == null,
    ));
    await _afterFilterChange(emit);
  }

  Future<void> _onToggle(
    InfoBrowseTitleToggled event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (state.expandedTitleId == event.titleId) {
      emit(state.copyWith(
        clearExpanded: true,
        rows: const [],
        rowsTotal: 0,
        page: 1,
      ));
      return;
    }
    emit(state.copyWith(
      expandedTitleId: event.titleId,
      rows: const [],
      rowsTotal: 0,
      page: 1,
      loadingRows: true,
    ));
    await _loadRows(emit, page: 1);
  }

  Future<void> _onLoadMore(
    InfoBrowseLoadMore event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (state.loadingMore || state.loadingRows) return;
    if (state.rows.length >= state.rowsTotal) return;
    final next = state.page + 1;
    emit(state.copyWith(loadingMore: true, page: next));
    await _loadRows(emit, page: next, append: true);
  }

  Future<void> _onRefresh(
    InfoBrowseRefreshed event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (state.titles.isEmpty) {
      add(InfoBrowseStarted(
        mode: state.mode,
        currentUserId: state.currentUserId,
        canWrite: state.canWrite,
        canConfirm: state.canConfirm,
        isAdmin: state.isAdmin,
      ));
      return;
    }
    await _reloadOpenTitle(emit);
  }

  Future<void> _onClearAction(
    InfoBrowseActionCleared event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(clearAction: true));
  }

  Future<void> _onClearFilter(
    InfoBrowseFilterCleared event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (event.key == 'title_category_id') {
      await _onCategory(const InfoBrowseCategoryFilterChanged(null), emit);
      return;
    }
    var next = state;
    switch (event.key) {
      case 'main_section_id':
        next = state.copyWith(clearMain: true);
      case 'sub_main_id':
        next = state.copyWith(clearSub: true);
      case 'title_id':
        next = state.copyWith(clearTitle: true);
      case 'attribute_id':
        next = state.copyWith(clearAttribute: true);
      case 'user':
        next = state.copyWith(clearEnteredBy: true);
      case 'confirmed':
        next = state.copyWith(clearConfirmed: true);
      case 'from':
        next = state.copyWith(clearFrom: true);
      case 'to':
        next = state.copyWith(clearTo: true);
    }
    emit(_withSoleDefaults(next));
    await _afterFilterChange(emit);
  }

  Future<void> _onFiltersApplied(
    InfoBrowseFiltersApplied event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(_withSoleDefaults(state.copyWith(
      mainId: event.mainId,
      clearMain: event.mainId == null,
      subId: event.subId,
      clearSub: event.subId == null,
      titleCategoryId: event.titleCategoryId,
      clearCategory: event.titleCategoryId == null,
      titleId: event.titleId,
      clearTitle: event.titleId == null,
      attributeId: event.attributeId,
      clearAttribute: event.attributeId == null,
      enteredByUserId: event.enteredByUserId,
      clearEnteredBy: event.enteredByUserId == null,
      confirmed: event.confirmed,
      clearConfirmed: event.confirmed == null || event.confirmed!.isEmpty,
      fromDate: event.fromDate,
      clearFrom: event.fromDate == null,
      toDate: event.toDate,
      clearTo: event.toDate == null,
    )));
    await _afterFilterChange(emit);
  }

  Future<void> _onClearFilters(
    InfoBrowseFiltersCleared event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(_withSoleDefaults(state.copyWith(
      clearMain: true,
      clearSub: true,
      clearCategory: true,
      clearTitle: true,
      clearAttribute: true,
      clearEnteredBy: true,
      clearConfirmed: true,
      clearFrom: true,
      clearTo: true,
      search: '',
      clearExpanded: true,
      rows: const [],
      rowsTotal: 0,
      page: 1,
    )));
    await _refreshCounts(emit);
  }

  InfoBrowseState _withSoleDefaults(InfoBrowseState s) {
    final mainId = s.mainId ?? soleItem(s.mainSections)?.id;
    final subId = s.subId ?? soleItem(s.subSections)?.id;
    final catId = s.titleCategoryId ?? soleItem(s.titleCategories)?.id;
    final allowedTitles = titlesForCategory(s.titles, catId);
    var titleId = s.titleId;
    if (titleId != null && !allowedTitles.any((t) => t.id == titleId)) {
      titleId = null;
    }
    titleId ??= soleItem(allowedTitles)?.id;
    final attrId = s.attributeId ?? soleItem(s.attributes)?.id;
    var enteredBy = s.enteredByUserId;
    if (s.showEnteredBy) {
      enteredBy ??= soleItem(s.users)?.id;
    }

    return s.copyWith(
      mainId: mainId,
      clearMain: mainId == null,
      subId: subId,
      clearSub: subId == null,
      titleCategoryId: catId,
      clearCategory: catId == null,
      titleId: titleId,
      clearTitle: titleId == null,
      attributeId: attrId,
      clearAttribute: attrId == null,
      enteredByUserId: enteredBy,
      clearEnteredBy: enteredBy == null,
    );
  }

  Future<void> _onDelete(
    InfoBrowseRowDeleteRequested event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (event.row.isAccepted || !state.canWrite) {
      emit(state.copyWith(actionError: 'لا يمكن تعديل سجل موافق عليه'));
      return;
    }
    try {
      await _remote.deleteInfoRow(
        rowKey: event.row.rowKey,
        infoId: event.row.infoIds.isEmpty ? null : event.row.infoIds.first,
      );
      emit(state.copyWith(actionMessage: 'تم حذف السجل'));
      _applyLocalRowChange(emit, event.row, remove: true);
    } catch (_) {
      emit(state.copyWith(actionError: 'تعذر حذف السجل'));
    }
  }

  Future<void> _onConfirm(
    InfoBrowseRowConfirmRequested event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (!state.canConfirm) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
      return;
    }
    if (event.approve && event.row.isAccepted) return;
    if (!event.approve && event.row.isRejected) return;
    final ids = event.row.infoIds;
    if (ids.isEmpty) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
      return;
    }
    try {
      await _remote.confirmInfoIds(
        ids: ids,
        status: event.approve ? 'accept' : 'reject',
      );
      final nextStatus = event.approve ? 'accept' : 'reject';
      emit(state.copyWith(
        actionMessage: event.approve ? 'تم الموافقة' : 'تم إلغاء الموافقة',
      ));
      _applyLocalRowChange(
        emit,
        event.row,
        confirmed: nextStatus,
      );
    } catch (_) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
    }
  }

  Future<void> _onCommitNote(
    InfoBrowseRowCommitNoteRequested event,
    Emitter<InfoBrowseState> emit,
  ) async {
    if (!state.canConfirm) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
      return;
    }
    final ids = event.row.infoIds;
    if (ids.isEmpty) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
      return;
    }
    try {
      await _remote.commitInfoNoteIds(ids: ids, note: event.note);
      emit(state.copyWith(actionMessage: 'تم حفظ ملاحظة المتابعة'));
      _applyLocalRowChange(
        emit,
        event.row,
        commitNote: event.note,
      );
    } catch (_) {
      emit(state.copyWith(actionError: 'خطأ في تحديث البيانات'));
    }
  }

  void _applyLocalRowChange(
    Emitter<InfoBrowseState> emit,
    InfoRecord row, {
    bool remove = false,
    String? confirmed,
    String? commitNote,
  }) {
    final titleId = row.titleId ?? state.expandedTitleId;
    final rows = [...state.rows];
    final idx = rows.indexWhere((r) => r.isSameRow(row));
    var drop = remove;
    if (!drop && idx >= 0) {
      final updated = rows[idx].copyWith(
        confirmed: confirmed,
        commitNote: commitNote,
      );
      final filter = state.confirmed;
      if (confirmed != null &&
          filter != null &&
          filter.isNotEmpty &&
          filter != confirmed) {
        drop = true;
      } else {
        rows[idx] = updated;
      }
    }
    if (drop && idx >= 0) {
      rows.removeAt(idx);
    }

    var rowsTotal = state.rowsTotal;
    final counts = Map<int, int?>.from(state.rowCounts);
    if (drop) {
      rowsTotal = rowsTotal < 1 ? 0 : rowsTotal - 1;
      if (titleId != null) {
        final current = counts[titleId];
        if (current != null && current > 0) {
          counts[titleId] = current - 1;
        }
      }
    }

    emit(state.copyWith(
      rows: rows,
      rowsTotal: rowsTotal,
      rowCounts: counts,
    ));
  }

  Future<void> _reloadOpenTitle(Emitter<InfoBrowseState> emit) async {
    final titleId = state.expandedTitleId;
    if (titleId == null) return;
    final pages = state.page < 1 ? 1 : state.page;
    try {
      final pageData = await _remote.queryInfoRows(
        page: 1,
        pageSize: _pageSize * pages,
        titleId: titleId,
        mainSectionId: state.mainId,
        subMainId: state.subId,
        userId: state.effectiveUserId,
        titleCategoryId: state.titleCategoryId,
        attributeId: state.attributeId,
        confirmed: state.confirmed,
        search: state.search,
        from: state.fromIso,
        to: state.toIso,
      );
      if (state.expandedTitleId != titleId) return;
      emit(state.copyWith(
        rows: pageData.results,
        rowsTotal: pageData.count,
        loadingRows: false,
        loadingMore: false,
      ));
      await _refreshCountForTitle(emit, titleId);
    } catch (_) {
      emit(state.copyWith(loadingRows: false, loadingMore: false));
    }
  }

  Future<void> _refreshCountForTitle(
    Emitter<InfoBrowseState> emit,
    int titleId,
  ) async {
    try {
      final count = await _remote.getInfoRowCount(
        titleId: titleId,
        mainSectionId: state.mainId,
        subMainId: state.subId,
        userId: state.effectiveUserId,
        titleCategoryId: state.titleCategoryId,
        attributeId: state.attributeId,
        confirmed: state.confirmed,
        search: state.search,
        from: state.fromIso,
        to: state.toIso,
      );
      final next = Map<int, int?>.from(state.rowCounts);
      next[titleId] = count;
      emit(state.copyWith(rowCounts: next));
    } catch (_) {}
  }

  Future<void> _afterFilterChange(Emitter<InfoBrowseState> emit) async {
    final open = state.expandedTitleId;
    final stillVisible =
        open != null && state.visibleTitles.any((t) => t.id == open);
    if (!stillVisible) {
      emit(state.copyWith(
        clearExpanded: true,
        rows: const [],
        rowsTotal: 0,
        page: 1,
      ));
    }
    await _refreshCounts(emit);
    if (stillVisible) {
      emit(state.copyWith(loadingRows: true, rows: const [], page: 1));
      await _loadRows(emit, page: 1);
    }
  }

  Future<void> _refreshCounts(Emitter<InfoBrowseState> emit) async {
    final ids = state.visibleTitles.map((t) => t.id).toList();
    if (ids.isEmpty) {
      emit(state.copyWith(rowCounts: const {}));
      return;
    }
    final pending = <int, int?>{};
    for (final id in ids) {
      pending[id] = null;
    }
    emit(state.copyWith(rowCounts: pending));
    final results = await Future.wait(ids.map((id) async {
      try {
        final count = await _remote.getInfoRowCount(
          titleId: id,
          mainSectionId: state.mainId,
          subMainId: state.subId,
          userId: state.effectiveUserId,
          titleCategoryId: state.titleCategoryId,
          attributeId: state.attributeId,
          confirmed: state.confirmed,
          search: state.search,
          from: state.fromIso,
          to: state.toIso,
        );
        return MapEntry(id, count);
      } catch (_) {
        return MapEntry(id, 0);
      }
    }));
    final counts = <int, int?>{};
    for (final e in results) {
      counts[e.key] = e.value;
    }
    emit(state.copyWith(rowCounts: counts));
  }

  Future<void> _loadRows(
    Emitter<InfoBrowseState> emit, {
    required int page,
    bool append = false,
  }) async {
    final titleId = state.expandedTitleId;
    if (titleId == null) {
      emit(state.copyWith(loadingRows: false, loadingMore: false));
      return;
    }
    try {
      final pageData = await _remote.queryInfoRows(
        page: page,
        pageSize: _pageSize,
        titleId: titleId,
        mainSectionId: state.mainId,
        subMainId: state.subId,
        userId: state.effectiveUserId,
        titleCategoryId: state.titleCategoryId,
        attributeId: state.attributeId,
        confirmed: state.confirmed,
        search: state.search,
        from: state.fromIso,
        to: state.toIso,
      );
      if (state.expandedTitleId != titleId) return;
      emit(state.copyWith(
        rows: append ? [...state.rows, ...pageData.results] : pageData.results,
        rowsTotal: pageData.count,
        loadingRows: false,
        loadingMore: false,
      ));
    } catch (_) {
      emit(state.copyWith(
        loadingRows: false,
        loadingMore: false,
        loadError: 'خطأ في تحميل البيانات',
      ));
    }
  }
}
