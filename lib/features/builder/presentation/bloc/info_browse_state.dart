import '../../data/models/builder_models.dart';
import '../utils/filter_defaults.dart';
import 'info_browse_event.dart';

class InfoBrowseState {
  final InfoBrowseMode mode;
  final int? currentUserId;
  final bool canWrite;
  final bool canConfirm;
  final bool isAdmin;
  final bool bootstrapping;
  final String? loadError;
  final List<BuilderNamedItem> mainSections;
  final List<BuilderSubSection> subSections;
  final List<BuilderTitle> titles;
  final List<BuilderNamedItem> titleCategories;
  final List<BuilderAttribute> attributes;
  final List<BuilderNamedItem> users;
  final Map<String, String> attributeLabels;
  final int? mainId;
  final int? subId;
  final int? titleCategoryId;
  final int? titleId;
  final int? attributeId;
  final int? enteredByUserId;
  final String? confirmed;
  final DateTime? fromDate;
  final DateTime? toDate;
  final String search;
  final Map<int, int?> rowCounts;
  final int? expandedTitleId;
  final List<InfoRecord> rows;
  final int rowsTotal;
  final int page;
  final bool loadingRows;
  final bool loadingMore;
  final String? actionMessage;
  final String? actionError;

  const InfoBrowseState({
    this.mode = InfoBrowseMode.myData,
    this.currentUserId,
    this.canWrite = false,
    this.canConfirm = false,
    this.isAdmin = false,
    this.bootstrapping = true,
    this.loadError,
    this.mainSections = const [],
    this.subSections = const [],
    this.titles = const [],
    this.titleCategories = const [],
    this.attributes = const [],
    this.users = const [],
    this.attributeLabels = const {},
    this.mainId,
    this.subId,
    this.titleCategoryId,
    this.titleId,
    this.attributeId,
    this.enteredByUserId,
    this.confirmed,
    this.fromDate,
    this.toDate,
    this.search = '',
    this.rowCounts = const {},
    this.expandedTitleId,
    this.rows = const [],
    this.rowsTotal = 0,
    this.page = 1,
    this.loadingRows = false,
    this.loadingMore = false,
    this.actionMessage,
    this.actionError,
  });

  bool get mineOnly =>
      mode == InfoBrowseMode.myData && !isAdmin && currentUserId != null;

  /// Web user-data: admin only. Infos-overview / admin-report: always.
  bool get showEnteredBy =>
      isAdmin || mode == InfoBrowseMode.submitted;

  int? get effectiveUserId {
    if (mode == InfoBrowseMode.myData && !isAdmin) return currentUserId;
    return enteredByUserId;
  }

  /// Web user-data lists every assigned sub, not only those under the selected main.
  List<BuilderSubSection> get visibleSubs => subSections;

  List<BuilderTitle> get titlesForCategory =>
      titleCategoryId == null
          ? titles
          : titles.where((t) => t.categoryId == titleCategoryId).toList();

  List<BuilderTitle> get visibleTitles {
    var list = titlesForCategory;
    if (titleId != null) {
      list = list.where((t) => t.id == titleId).toList();
    }
    final q = search.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list.where((t) => t.name.toLowerCase().contains(q)).toList();
    }
    return list;
  }

  /// Web attribute filter is the full attributes list, not narrowed by title.
  List<BuilderAttribute> get visibleAttributes => attributes;

  String? get fromIso => isoDate(fromDate);
  String? get toIso => isoDate(toDate);

  InfoBrowseState copyWith({
    InfoBrowseMode? mode,
    int? currentUserId,
    bool? canWrite,
    bool? canConfirm,
    bool? isAdmin,
    bool? bootstrapping,
    String? loadError,
    bool clearError = false,
    List<BuilderNamedItem>? mainSections,
    List<BuilderSubSection>? subSections,
    List<BuilderTitle>? titles,
    List<BuilderNamedItem>? titleCategories,
    List<BuilderAttribute>? attributes,
    List<BuilderNamedItem>? users,
    Map<String, String>? attributeLabels,
    int? mainId,
    bool clearMain = false,
    int? subId,
    bool clearSub = false,
    int? titleCategoryId,
    bool clearCategory = false,
    int? titleId,
    bool clearTitle = false,
    int? attributeId,
    bool clearAttribute = false,
    int? enteredByUserId,
    bool clearEnteredBy = false,
    String? confirmed,
    bool clearConfirmed = false,
    DateTime? fromDate,
    bool clearFrom = false,
    DateTime? toDate,
    bool clearTo = false,
    String? search,
    Map<int, int?>? rowCounts,
    int? expandedTitleId,
    bool clearExpanded = false,
    List<InfoRecord>? rows,
    int? rowsTotal,
    int? page,
    bool? loadingRows,
    bool? loadingMore,
    String? actionMessage,
    String? actionError,
    bool clearAction = false,
  }) {
    return InfoBrowseState(
      mode: mode ?? this.mode,
      currentUserId: currentUserId ?? this.currentUserId,
      canWrite: canWrite ?? this.canWrite,
      canConfirm: canConfirm ?? this.canConfirm,
      isAdmin: isAdmin ?? this.isAdmin,
      bootstrapping: bootstrapping ?? this.bootstrapping,
      loadError: clearError ? null : (loadError ?? this.loadError),
      mainSections: mainSections ?? this.mainSections,
      subSections: subSections ?? this.subSections,
      titles: titles ?? this.titles,
      titleCategories: titleCategories ?? this.titleCategories,
      attributes: attributes ?? this.attributes,
      users: users ?? this.users,
      attributeLabels: attributeLabels ?? this.attributeLabels,
      mainId: clearMain ? null : (mainId ?? this.mainId),
      subId: clearSub ? null : (subId ?? this.subId),
      titleCategoryId:
          clearCategory ? null : (titleCategoryId ?? this.titleCategoryId),
      titleId: clearTitle ? null : (titleId ?? this.titleId),
      attributeId: clearAttribute ? null : (attributeId ?? this.attributeId),
      enteredByUserId:
          clearEnteredBy ? null : (enteredByUserId ?? this.enteredByUserId),
      confirmed: clearConfirmed ? null : (confirmed ?? this.confirmed),
      fromDate: clearFrom ? null : (fromDate ?? this.fromDate),
      toDate: clearTo ? null : (toDate ?? this.toDate),
      search: search ?? this.search,
      rowCounts: rowCounts ?? this.rowCounts,
      expandedTitleId:
          clearExpanded ? null : (expandedTitleId ?? this.expandedTitleId),
      rows: rows ?? this.rows,
      rowsTotal: rowsTotal ?? this.rowsTotal,
      page: page ?? this.page,
      loadingRows: loadingRows ?? this.loadingRows,
      loadingMore: loadingMore ?? this.loadingMore,
      actionMessage: clearAction ? null : (actionMessage ?? this.actionMessage),
      actionError: clearAction ? null : (actionError ?? this.actionError),
    );
  }
}
