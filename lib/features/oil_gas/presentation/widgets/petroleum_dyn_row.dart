import 'package:flutter/material.dart';

double? parsePetroleumNum(String text) {
  final t = text.trim().replaceAll(',', '.');
  if (t.isEmpty) return null;
  return double.tryParse(t);
}

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
