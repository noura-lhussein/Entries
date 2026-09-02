import 'package:flutter/material.dart';

import '../../domain/utils/parse_oil_gas_number.dart';

double? parsePetroleumNum(String text) => parseOilGasNumber(text);

class PetroleumDynRow {
  final String id;
  final List<TextEditingController> ctrls;
  String? dropVal1;
  String? dropVal2;
  PetroleumDynRow(this.id, int count, {this.dropVal1, this.dropVal2})
      : ctrls = List.generate(count, (_) => TextEditingController());

  void dispose() {
    for (final c in ctrls) {
      c.dispose();
    }
  }
}
