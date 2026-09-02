import 'package:equatable/equatable.dart';

abstract class PetroleumOpsEvent extends Equatable {
  const PetroleumOpsEvent();
  @override
  List<Object?> get props => [];
}

class PetroleumOpsStarted extends PetroleumOpsEvent {
  const PetroleumOpsStarted();
}

class PetroleumOpsDateChanged extends PetroleumOpsEvent {
  const PetroleumOpsDateChanged(this.date);
  final DateTime date;
  @override
  List<Object?> get props => [date];
}

class PetroleumOpsPublishToggled extends PetroleumOpsEvent {
  const PetroleumOpsPublishToggled(this.value);
  final bool value;
  @override
  List<Object?> get props => [value];
}

class PetroleumOpsSaveRequested extends PetroleumOpsEvent {
  const PetroleumOpsSaveRequested({
    required this.oilTexts,
    required this.gasTexts,
    required this.refineryTexts,
    required this.inventory,
    required this.exports,
    required this.losses,
    required this.supply,
    required this.requirement,
  });

  final Map<String, String> oilTexts;
  final Map<String, String> gasTexts;
  final Map<String, String> refineryTexts;
  final List<Map<String, dynamic>> inventory;
  final List<Map<String, dynamic>> exports;
  final List<Map<String, dynamic>> losses;
  final List<Map<String, dynamic>> supply;
  final List<Map<String, dynamic>> requirement;

  @override
  List<Object?> get props => [
        oilTexts,
        gasTexts,
        refineryTexts,
        inventory,
        exports,
        losses,
        supply,
        requirement,
      ];
}
