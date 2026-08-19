import 'package:flutter/material.dart';

class OreTypeLine {
  String productionType;
  String unit;
  final annualCtrl = TextEditingController();
  final h1PlanCtrl = TextEditingController();
  final h1ExecCtrl = TextEditingController();
  final pctCtrl = TextEditingController();

  OreTypeLine({
    this.productionType = '',
    this.unit = 'طن',
  });

  void dispose() {
    annualCtrl.dispose();
    h1PlanCtrl.dispose();
    h1ExecCtrl.dispose();
    pctCtrl.dispose();
  }
}

class OreProductGroup {
  String productNameAr;
  String productNameEn;
  final contractsCtrl = TextEditingController();
  final reserveCtrl = TextEditingController();
  List<OreTypeLine> lines;

  OreProductGroup({
    this.productNameAr = '',
    this.productNameEn = '',
    List<OreTypeLine>? lines,
  }) : lines = lines ?? [OreTypeLine()];

  void dispose() {
    contractsCtrl.dispose();
    reserveCtrl.dispose();
    for (final line in lines) {
      line.dispose();
    }
  }
}
