enum InfoBrowseMode { myData, submitted }

abstract class InfoBrowseEvent {
  const InfoBrowseEvent();
}

class InfoBrowseStarted extends InfoBrowseEvent {
  final InfoBrowseMode mode;
  final int? currentUserId;
  const InfoBrowseStarted({required this.mode, this.currentUserId});
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

class InfoBrowseTitleFilterChanged extends InfoBrowseEvent {
  final int? titleId;
  const InfoBrowseTitleFilterChanged(this.titleId);
}

class InfoBrowseStatusFilterChanged extends InfoBrowseEvent {
  final String? confirmed;
  const InfoBrowseStatusFilterChanged(this.confirmed);
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
