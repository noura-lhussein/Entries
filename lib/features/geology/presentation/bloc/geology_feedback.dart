import 'package:equatable/equatable.dart';

class GeologyFeedback extends Equatable {
  GeologyFeedback({
    required this.message,
    required this.isSuccess,
    this.floating = true,
  }) : id = DateTime.now().microsecondsSinceEpoch;

  final int id;
  final String message;
  final bool isSuccess;
  final bool floating;

  @override
  List<Object?> get props => [id, message, isSuccess, floating];
}
