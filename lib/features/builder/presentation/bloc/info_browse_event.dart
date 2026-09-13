import '../../data/models/builder_models.dart';

enum InfoBrowseMode { myData, submitted }

abstract class InfoBrowseEvent {
  const InfoBrowseEvent();
}

class InfoBrowseStarted extends InfoBrowseEvent {
  final InfoBrowseMode mode;
  final int? currentUserId;
  final bool canWrite;
  final bool canConfirm;
  final bool isAdmin;
  const InfoBrowseStarted({
    required this.mode,
    this.currentUserId,
    this.canWrite = false,
    this.canConfirm = false,
    this.isAdmin = false,
  });
}

class InfoBrowseSearchChanged extends InfoBrowseEvent {
  final String query;
  const InfoBrowseSearchChanged(this.query);
}

class InfoBrowseMainFilterChanged extends InfoBrowseEvent {
  final int? mainId;
  const InfoBrowseMainFilterChanged(this.mainId);
}

class InfoBrowseSubFilterChanged extends InfoBrowseEvent {
  final int? subId;
  const InfoBrowseSubFilterChanged(this.subId);
}

class InfoBrowseCategoryFilterChanged extends InfoBrowseEvent {
  final int? categoryId;
  const InfoBrowseCategoryFilterChanged(this.categoryId);
}

class InfoBrowseTitleFilterChanged extends InfoBrowseEvent {
  final int? titleId;
  const InfoBrowseTitleFilterChanged(this.titleId);
}

class InfoBrowseAttributeFilterChanged extends InfoBrowseEvent {
  final int? attributeId;
  const InfoBrowseAttributeFilterChanged(this.attributeId);
}

class InfoBrowseStatusFilterChanged extends InfoBrowseEvent {
  final String? confirmed;
  const InfoBrowseStatusFilterChanged(this.confirmed);
}

class InfoBrowseFromDateChanged extends InfoBrowseEvent {
  final DateTime? from;
  const InfoBrowseFromDateChanged(this.from);
}

class InfoBrowseToDateChanged extends InfoBrowseEvent {
  final DateTime? to;
  const InfoBrowseToDateChanged(this.to);
}

class InfoBrowseEnteredByChanged extends InfoBrowseEvent {
  final int? userId;
  const InfoBrowseEnteredByChanged(this.userId);
}

class InfoBrowseTitleToggled extends InfoBrowseEvent {
  final int titleId;
  const InfoBrowseTitleToggled(this.titleId);
}

class InfoBrowseLoadMore extends InfoBrowseEvent {
  const InfoBrowseLoadMore();
}

class InfoBrowseRefreshed extends InfoBrowseEvent {
  const InfoBrowseRefreshed();
}

class InfoBrowseRowDeleteRequested extends InfoBrowseEvent {
  final InfoRecord row;
  const InfoBrowseRowDeleteRequested(this.row);
}

class InfoBrowseRowConfirmRequested extends InfoBrowseEvent {
  final InfoRecord row;
  final bool approve;
  const InfoBrowseRowConfirmRequested(this.row, {required this.approve});
}

class InfoBrowseRowCommitNoteRequested extends InfoBrowseEvent {
  final InfoRecord row;
  final String note;
  const InfoBrowseRowCommitNoteRequested(this.row, this.note);
}

class InfoBrowseActionCleared extends InfoBrowseEvent {
  const InfoBrowseActionCleared();
}

class InfoBrowseFiltersApplied extends InfoBrowseEvent {
  final int? mainId;
  final int? subId;
  final int? titleCategoryId;
  final int? titleId;
  final int? attributeId;
  final int? enteredByUserId;
  final String? confirmed;
  final DateTime? fromDate;
  final DateTime? toDate;
  const InfoBrowseFiltersApplied({
    this.mainId,
    this.subId,
    this.titleCategoryId,
    this.titleId,
    this.attributeId,
    this.enteredByUserId,
    this.confirmed,
    this.fromDate,
    this.toDate,
  });
}

class InfoBrowseFilterCleared extends InfoBrowseEvent {
  final String key;
  const InfoBrowseFilterCleared(this.key);
}

class InfoBrowseFiltersCleared extends InfoBrowseEvent {
  const InfoBrowseFiltersCleared();
}
