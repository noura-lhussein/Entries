import '../../data/models/builder_models.dart';
import 'info_browse_event.dart';

class InfoBrowseState {
  final InfoBrowseMode mode;
  final int? currentUserId;
  final bool bootstrapping;
  final String? loadError;
  final List<BuilderNamedItem> mainSections;
  final List<BuilderSubSection> subSections;
  final List<BuilderTitle> titles;
  final int? mainId;
  final int? subId;
  final int? titleId;
  final String? confirmed;
  final String search;
  final Map<int, int?> rowCounts;
  final int? expandedTitleId;
  final List<InfoRecord> rows;
  final int rowsTotal;
  final int page;
  final bool loadingRows;
  final bool loadingMore;

  const InfoBrowseState({
    this.mode = InfoBrowseMode.myData,
    this.currentUserId,
    this.bootstrapping = true,
    this.loadError,
    this.mainSections = const [],
    this.subSections = const [],
    this.titles = const [],
    this.mainId,
    this.subId,
    this.titleId,
    this.confirmed,
    this.search = '',
    this.rowCounts = const {},
    this.expandedTitleId,
    this.rows = const [],
    this.rowsTotal = 0,
    this.page = 1,
    this.loadingRows = false,
    this.loadingMore = false,
  });

  bool get mineOnly => mode == InfoBrowseMode.myData && currentUserId != null;

  List<BuilderSubSection> get visibleSubs {
    if (mainId == null) return subSections;
    return subSections.where((s) => s.mainSectionId == mainId).toList();
  }

  List<BuilderTitle> get visibleTitles {
    var list = titles;
    if (titleId != null) {
      list = list.where((t) => t.id == titleId).toList();
    }
    final q = search.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list
          .where((t) => t.name.toLowerCase().contains(q))
          .toList();
    }
    return list;
  }

  InfoBrowseState copyWith({
    InfoBrowseMode? mode,
    int? currentUserId,
    bool? bootstrapping,
    String? loadError,
    bool clearError = false,
    List<BuilderNamedItem>? mainSections,
    List<BuilderSubSection>? subSections,
    List<BuilderTitle>? titles,
    int? mainId,
    bool clearMain = false,
    int? subId,
    bool clearSub = false,
    int? titleId,
    bool clearTitle = false,
    String? confirmed,
    bool clearConfirmed = false,
    String? search,
    Map<int, int?>? rowCounts,
    int? expandedTitleId,
    bool clearExpanded = false,
    List<InfoRecord>? rows,
    int? rowsTotal,
    int? page,
    bool? loadingRows,
    bool? loadingMore,
  }) {
    return InfoBrowseState(
      mode: mode ?? this.mode,
      currentUserId: currentUserId ?? this.currentUserId,
      bootstrapping: bootstrapping ?? this.bootstrapping,
      loadError: clearError ? null : (loadError ?? this.loadError),
      mainSections: mainSections ?? this.mainSections,
      subSections: subSections ?? this.subSections,
      titles: titles ?? this.titles,
      mainId: clearMain ? null : (mainId ?? this.mainId),
      subId: clearSub ? null : (subId ?? this.subId),
      titleId: clearTitle ? null : (titleId ?? this.titleId),
      confirmed: clearConfirmed ? null : (confirmed ?? this.confirmed),
      search: search ?? this.search,
      rowCounts: rowCounts ?? this.rowCounts,
      expandedTitleId:
          clearExpanded ? null : (expandedTitleId ?? this.expandedTitleId),
      rows: rows ?? this.rows,
      rowsTotal: rowsTotal ?? this.rowsTotal,
      page: page ?? this.page,
      loadingRows: loadingRows ?? this.loadingRows,
      loadingMore: loadingMore ?? this.loadingMore,
    );
  }
}
