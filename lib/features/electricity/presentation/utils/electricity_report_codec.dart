import 'package:flutter/material.dart';

import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';
import '../widgets/models/electricity_fields_data.dart';

double? parseNum(String text) {
  final t = text.trim().replaceAll(',', '.');
  if (t.isEmpty) return null;
  return double.tryParse(t);
}

String fmtDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

String? fmtPeak(TimeOfDay? t) {
  if (t == null) return null;
  final h = t.hour.toString().padLeft(2, '0');
  final m = t.minute.toString().padLeft(2, '0');
  return '$h:$m';
}

class ElectricityAppliedReport {
  final TimeOfDay? peak;
  final List<DynamicRow> maintenanceRows;
  final List<DynamicRow> generationIncidentRows;
  final List<DynamicRow> gridIncidentRows;

  const ElectricityAppliedReport({
    required this.peak,
    required this.maintenanceRows,
    required this.generationIncidentRows,
    required this.gridIncidentRows,
  });
}

Map<String, dynamic> buildPayload({
  required ElectricityState state,
  required Map<String, TextEditingController> fieldCtrls,
  required Map<String, TextEditingController> consumedCtrls,
  required Map<String, TextEditingController> allocatedCtrls,
  required Map<String, TextEditingController> tankCtrls,
  required Map<String, TextEditingController> tankMaxCtrls,
  required Map<String, TextEditingController> hydraulicCtrls,
  required TextEditingController arabicNotesCtrl,
  required TextEditingController englishNotesCtrl,
  required List<List<String>> generationIncidentRows,
  required List<List<String>> gridIncidentRows,
  required List<List<String>> maintenanceRows,
}) {
  final metrics = <Map<String, dynamic>>[];
  for (final entry in fieldCtrls.entries) {
    final v = parseNum(entry.value.text);
    if (v != null) {
      metrics.add({
        'metric_key': entry.key,
        'dimension': '',
        'value': v,
      });
    }
  }

  final governorateLoads = <Map<String, dynamic>>[];
  for (final g in kGovernorates) {
    final consumed = parseNum(consumedCtrls[g.code]?.text ?? '');
    final allocated = parseNum(allocatedCtrls[g.code]?.text ?? '');
    if (consumed != null || allocated != null) {
      governorateLoads.add({
        'governorate_code': g.code,
        'consumed_mw': consumed,
        'allocated_mw': allocated,
      });
    }
  }

  final hydroReadings = <Map<String, dynamic>>[];
  for (final dam in kHydraulicDams) {
    final front =
        parseNum(hydraulicCtrls['${dam.code}_front_level']?.text ?? '');
    final back =
        parseNum(hydraulicCtrls['${dam.code}_back_level']?.text ?? '');
    final gen =
        parseNum(hydraulicCtrls['${dam.code}_generation']?.text ?? '');
    final outflow =
        parseNum(hydraulicCtrls['${dam.code}_outflow']?.text ?? '');
    final inflow =
        parseNum(hydraulicCtrls['${dam.code}_inflow']?.text ?? '');
    final expected =
        parseNum(hydraulicCtrls['${dam.code}_expected']?.text ?? '');
    if (front != null ||
        back != null ||
        gen != null ||
        outflow != null ||
        inflow != null ||
        expected != null) {
      hydroReadings.add({
        'dam_code': dam.code,
        'front_level_m': front,
        'back_level_m': back,
        'generation_mwh': gen,
        'outflow_m3s': outflow,
        'inflow_m3s': inflow,
        'expected_m3s': expected,
      });
    }
  }

  final fuelTankReadings = <Map<String, dynamic>>[];
  for (final tank in kFuelTanks) {
    final current = parseNum(tankCtrls[tank.code]?.text ?? '');
    if (current != null) {
      fuelTankReadings.add({
        'station_code': tank.code,
        'current_tons': current,
        'max_capacity_tons':
            parseNum(tankMaxCtrls[tank.code]?.text ?? '') ?? tank.maxCapacity,
      });
    }
  }

  final genIncidents = <Map<String, dynamic>>[];
  for (final row in generationIncidentRows) {
    if (row.length < 2) continue;
    if (row[1].isEmpty) continue;
    genIncidents.add({
      'event_time': row[0],
      'description_ar': row[1],
      'description_en': '',
    });
  }

  final gridIncidents = <Map<String, dynamic>>[];
  for (final row in gridIncidentRows) {
    if (row.length < 2) continue;
    if (row[0].isEmpty && row[1].isEmpty) continue;
    gridIncidents.add({
      'line_name': row[0],
      'action_ar': row[1],
      'action_en': '',
      'voltage_kv': null,
    });
  }

  final maintenanceGroups = <String>[];
  for (final row in maintenanceRows) {
    if (row.isNotEmpty && row.first.isNotEmpty) {
      maintenanceGroups.add(row.first);
    }
  }

  final peak = fmtPeak(state.peakTime);
  return {
    'report_date': fmtDate(state.reportDate),
    'status': state.publishAfterSave ? 'published' : 'draft',
    'peak_generation_time': peak,
    'reference_hour': peak,
    'notes_ar': arabicNotesCtrl.text.trim(),
    'notes_en': englishNotesCtrl.text.trim(),
    'maintenance_groups_ar': maintenanceGroups.join('\n'),
    'metrics': metrics,
    'governorate_loads': governorateLoads,
    'hydro_readings': hydroReadings,
    'fuel_tank_readings': fuelTankReadings,
    'generation_incidents': genIncidents,
    'grid_incidents': gridIncidents,
  };
}

ElectricityAppliedReport applyReportDetail(
  Map<String, dynamic> detail, {
  required Map<String, TextEditingController> fieldCtrls,
  required Map<String, TextEditingController> consumedCtrls,
  required Map<String, TextEditingController> allocatedCtrls,
  required Map<String, TextEditingController> tankCtrls,
  required Map<String, TextEditingController> tankMaxCtrls,
  required Map<String, TextEditingController> hydraulicCtrls,
  required TextEditingController arabicNotesCtrl,
  required TextEditingController englishNotesCtrl,
}) {
  for (final c in [
    ...fieldCtrls.values,
    ...consumedCtrls.values,
    ...allocatedCtrls.values,
    ...tankCtrls.values,
    ...hydraulicCtrls.values,
  ]) {
    c.clear();
  }
  for (final t in kFuelTanks) {
    tankMaxCtrls[t.code]?.text = '${t.maxCapacity?.toInt() ?? ''}';
  }
  final metrics = detail['metrics'] as List? ?? const [];
  for (final raw in metrics.whereType<Map>()) {
    final key = raw['metric_key']?.toString();
    if (key == null || !fieldCtrls.containsKey(key)) continue;
    final v = raw['value'];
    fieldCtrls[key]!.text = v == null ? '' : '$v';
  }
  for (final raw
      in (detail['governorate_loads'] as List? ?? const []).whereType<Map>()) {
    final code = raw['governorate_code']?.toString();
    if (code == null) continue;
    if (consumedCtrls.containsKey(code) && raw['consumed_mw'] != null) {
      consumedCtrls[code]!.text = '${raw['consumed_mw']}';
    }
    if (allocatedCtrls.containsKey(code) && raw['allocated_mw'] != null) {
      allocatedCtrls[code]!.text = '${raw['allocated_mw']}';
    }
  }
  for (final raw
      in (detail['fuel_tank_readings'] as List? ?? const []).whereType<Map>()) {
    final code = raw['station_code']?.toString();
    if (code == null || !tankCtrls.containsKey(code)) continue;
    if (raw['current_tons'] != null) {
      tankCtrls[code]!.text = '${raw['current_tons']}';
    }
    if (raw['max_capacity_tons'] != null) {
      tankMaxCtrls[code]?.text = '${raw['max_capacity_tons']}';
    }
  }
  for (final raw
      in (detail['hydro_readings'] as List? ?? const []).whereType<Map>()) {
    final code = raw['dam_code']?.toString();
    if (code == null) continue;
    void setH(String k, dynamic v) {
      final key = '${code}_$k';
      if (hydraulicCtrls.containsKey(key) && v != null) {
        hydraulicCtrls[key]!.text = '$v';
      }
    }
    setH('front_level', raw['front_level_m']);
    setH('back_level', raw['back_level_m']);
    setH('generation', raw['generation_mwh']);
    setH('outflow', raw['outflow_m3s']);
    setH('inflow', raw['inflow_m3s']);
    setH('expected', raw['expected_m3s']);
  }
  arabicNotesCtrl.text = detail['notes_ar']?.toString() ?? '';
  englishNotesCtrl.text = detail['notes_en']?.toString() ?? '';

  final peakRaw = detail['peak_generation_time']?.toString() ?? '';
  TimeOfDay? peak;
  final peakParts = peakRaw.split(':');
  if (peakParts.length >= 2) {
    final h = int.tryParse(peakParts[0]);
    final m = int.tryParse(peakParts[1]);
    if (h != null && m != null) peak = TimeOfDay(hour: h, minute: m);
  }

  final maintText = detail['maintenance_groups_ar']?.toString() ?? '';
  final maintRows = <DynamicRow>[];
  for (final line in maintText.split('\n')) {
    final t = line.trim();
    if (t.isEmpty) continue;
    maintRows.add(DynamicRow('m_${maintRows.length}_$t', [t]));
  }
  final genRows = <DynamicRow>[];
  for (final raw
      in (detail['generation_incidents'] as List? ?? const []).whereType<Map>()) {
    genRows.add(DynamicRow(
      'g_${genRows.length}',
      [
        raw['event_time']?.toString() ?? '',
        raw['description_ar']?.toString() ?? '',
      ],
    ));
  }
  final gridRows = <DynamicRow>[];
  for (final raw
      in (detail['grid_incidents'] as List? ?? const []).whereType<Map>()) {
    gridRows.add(DynamicRow(
      'l_${gridRows.length}',
      [
        raw['line_name']?.toString() ?? '',
        raw['action_ar']?.toString() ?? '',
      ],
    ));
  }

  return ElectricityAppliedReport(
    peak: peak,
    maintenanceRows: maintRows,
    generationIncidentRows: genRows,
    gridIncidentRows: gridRows,
  );
}
