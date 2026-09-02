import 'package:flutter/material.dart';

import '../../../domain/services/geology_ore_math.dart';
import 'geology_ore_form_models.dart';

void setNum(TextEditingController c, dynamic v) {
  c.text = v == null ? '' : '$v';
}

List<OreProductGroup> groupOreRows(List rawRows) {
  if (rawRows.isEmpty) return [OreProductGroup()];
  final groups = <OreProductGroup>[];
  final indexByKey = <String, int>{};

  for (final raw in rawRows.whereType<Map>()) {
    final nameAr = (raw['product_name_ar'] ?? '').toString().trim();
    final nameEn = (raw['product_name_en'] ?? '').toString().trim();
    final key = '${nameAr.toLowerCase()}||${nameEn.toLowerCase()}';
    var gi = indexByKey[key];
    late OreProductGroup group;
    if (gi == null) {
      group = OreProductGroup(productNameAr: nameAr, productNameEn: nameEn)
        ..lines.clear();
      if (raw['contract_count'] != null) {
        group.contractsCtrl.text = '${raw['contract_count']}';
      }
      group.reserveCtrl.text = raw['reserve_text']?.toString() ?? '';
      indexByKey[key] = groups.length;
      groups.add(group);
    } else {
      group = groups[gi];
      if (group.contractsCtrl.text.isEmpty && raw['contract_count'] != null) {
        group.contractsCtrl.text = '${raw['contract_count']}';
      }
      if (group.reserveCtrl.text.isEmpty && raw['reserve_text'] != null) {
        group.reserveCtrl.text = raw['reserve_text'].toString();
      }
    }

    var productionType = raw['production_type']?.toString() ?? '';
    var unit = raw['unit']?.toString() ?? '';
    if (productionType.isEmpty && unit.contains('/')) {
      final parsed = parseLegacyUnit(unit);
      productionType = parsed.productionType;
      unit = parsed.unit;
    }
    final line = OreTypeLine(productionType: productionType, unit: unit);
    setNum(line.annualCtrl, raw['annual_plan_tons']);
    setNum(line.h1PlanCtrl, raw['h1_plan_tons']);
    setNum(line.h1ExecCtrl, raw['h1_executed_tons']);
    setNum(line.pctCtrl, raw['execution_pct']);
    group.lines.add(line);
  }

  for (final group in groups) {
    if (group.lines.isEmpty) group.lines.add(OreTypeLine());
  }
  return groups.isEmpty ? [OreProductGroup()] : groups;
}

List<Map<String, dynamic>> flattenOreGroups(List<OreProductGroup> groups) {
  final rows = <Map<String, dynamic>>[];
  var sortOrder = 0;
  for (final group in groups) {
    final nameAr = group.productNameAr.trim();
    if (nameAr.isEmpty) continue;
    final contracts = parseGeologyNum(group.contractsCtrl.text)?.round();
    final reserve = group.reserveCtrl.text.trim();
    final lines = group.lines.isEmpty ? [OreTypeLine()] : group.lines;
    for (final line in lines) {
      final plan = parseGeologyNum(line.h1PlanCtrl.text);
      final executed = parseGeologyNum(line.h1ExecCtrl.text);
      rows.add({
        'product_name_ar': nameAr,
        'product_name_en': group.productNameEn.trim(),
        'production_type': line.productionType.trim(),
        'unit': line.unit.trim(),
        'annual_plan_tons': parseGeologyNum(line.annualCtrl.text),
        'h1_plan_tons': plan,
        'h1_executed_tons': executed,
        'execution_pct':
            parseGeologyNum(line.pctCtrl.text) ?? executionPct(plan, executed),
        'contract_count': contracts,
        'reserve_text': reserve,
        'sort_order': sortOrder++,
      });
    }
  }
  return rows;
}
