import 'package:equatable/equatable.dart';

class OilField extends Equatable {
  final String nameAr;
  final String code;
  const OilField(this.nameAr, this.code);

  @override
  List<Object?> get props => [nameAr, code];
}
