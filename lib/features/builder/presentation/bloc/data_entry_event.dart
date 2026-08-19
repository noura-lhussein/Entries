import '../../data/models/builder_models.dart';

abstract class DataEntryEvent {
  const DataEntryEvent();
}

class DataEntryStarted extends DataEntryEvent {
  final DataEntrySectorFilter sector;
  final bool isAdmin;
  const DataEntryStarted({
    required this.sector,
    this.isAdmin = false,
  });
}

class MainSectionSelected extends DataEntryEvent {
  final int? mainId;
  const MainSectionSelected(this.mainId);
}

class SubSectionSelected extends DataEntryEvent {
  final int? subId;
  const SubSectionSelected(this.subId);
}

class TitleSelected extends DataEntryEvent {
  final int titleId;
  const TitleSelected(this.titleId);
}

class FieldValueChanged extends DataEntryEvent {
  final String key;
  final String value;
  const FieldValueChanged(this.key, this.value);
}

class FieldBlurred extends DataEntryEvent {
  final String key;
  const FieldBlurred(this.key);
}

class GroupToggled extends DataEntryEvent {
  final String groupId;
  const GroupToggled(this.groupId);
}

class HistoryToggled extends DataEntryEvent {
  const HistoryToggled();
}

class HistoryRowToggled extends DataEntryEvent {
  final String rowId;
  const HistoryRowToggled(this.rowId);
}

class SaveDraftRequested extends DataEntryEvent {
  const SaveDraftRequested();
}

class CommitAndNextRequested extends DataEntryEvent {
  const CommitAndNextRequested();
}
