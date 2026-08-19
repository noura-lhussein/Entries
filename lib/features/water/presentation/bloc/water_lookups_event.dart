import 'package:equatable/equatable.dart';

abstract class WaterLookupsEvent extends Equatable {
  const WaterLookupsEvent();

  @override
  List<Object?> get props => [];
}

class GetWaterLookupsStarted extends WaterLookupsEvent {
  const GetWaterLookupsStarted();
}
