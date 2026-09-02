import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/datasources/builder_remote_data_source.dart';
import 'info_browse_event.dart';
import 'info_browse_state.dart';

class InfoBrowseBloc extends Bloc<InfoBrowseEvent, InfoBrowseState> {
  InfoBrowseBloc(this._remote) : super(const InfoBrowseState()) {
    on<InfoBrowseStarted>(_onStarted);
    on<InfoBrowseSearchChanged>(_onSearch);
    on<InfoBrowseMainFilterChanged>(_onMain);
    on<InfoBrowseSubFilterChanged>(_onSub);
    on<InfoBrowseTitleFilterChanged>(_onTitle);
    on<InfoBrowseStatusFilterChanged>(_onStatus);
    on<InfoBrowseTitleToggled>(_onToggle);
    on<InfoBrowseLoadMore>(_onLoadMore);
    on<InfoBrowseRefreshed>(_onRefresh);
  }

  final BuilderRemoteDataSource _remote;
  static const _pageSize = 20;

  Future<void> _onStarted(
    InfoBrowseStarted event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(InfoBrowseState(
      mode: event.mode,
      currentUserId: event.currentUserId,
      bootstrapping: true,
    ));
    try {
      final mains = await _remote.getMainSections();
      final subs = await _remote.getSubSections();
      final titles = await _remote.getTitles();
      emit(state.copyWith(
        bootstrapping: false,
        clearError: true,
        mainSections: mains,
        subSections: subs,
        titles: titles,
      ));
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
    emit(state.copyWith(
      mainId: event.mainId,
      clearMain: event.mainId == null,
      clearSub: true,
    ));
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

  Future<void> _onTitle(
    InfoBrowseTitleFilterChanged event,
    Emitter<InfoBrowseState> emit,
  ) async {
    emit(state.copyWith(
      titleId: event.titleId,
      clearTitle: event.titleId == null,
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
    await _afterFilterChange(emit);
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
    final pending = <int, int?>{for (final id in ids) id: null};
    emit(state.copyWith(rowCounts: pending));
    final userId = state.mineOnly ? state.currentUserId : null;
    final results = await Future.wait(ids.map((id) async {
      try {
        final count = await _remote.getInfoRowCount(
          titleId: id,
          mainSectionId: state.mainId,
          subMainId: state.subId,
          userId: userId,
          confirmed: state.confirmed,
          search: state.search,
        );
        return MapEntry(id, count);
      } catch (_) {
        return MapEntry(id, 0);
      }
    }));
    emit(state.copyWith(rowCounts: {
      for (final e in results) e.key: e.value,
    }));
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
        userId: state.mineOnly ? state.currentUserId : null,
        confirmed: state.confirmed,
        search: state.search,
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
