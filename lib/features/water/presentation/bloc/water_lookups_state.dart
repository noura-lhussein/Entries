import 'package:equatable/equatable.dart';
import '../../domain/entities/water_lookups_entity.dart';

abstract class WaterLookupsState extends Equatable {
  const WaterLookupsState();

  @override
  List<Object?> get props => [];
}

class WaterLookupsInitial extends WaterLookupsState {}

class WaterLookupsLoading extends WaterLookupsState {}

class WaterLookupsLoaded extends WaterLookupsState {
  final WaterLookupsEntity lookups;

  const WaterLookupsLoaded({required this.lookups});

  @override
  List<Object?> get props => [lookups];
}

class WaterLookupsError extends WaterLookupsState {
  final String message;

  const WaterLookupsError({required this.message});

  @override
  List<Object?> get props => [message];
}
