String isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

String mapYesNo(String value) {
  if (value == 'نعم') return 'yes';
  if (value == 'لا') return 'no';
  return '';
}

String mapCondition(String value) {
  if (value.startsWith('1')) return '1';
  if (value.startsWith('2')) return '2';
  if (value.startsWith('3')) return '3';
  return '';
}

String mapEfficiency(String value) {
  if (value == 'غير محدد') return '';
  if (value.startsWith('1')) return '1';
  if (value.startsWith('2')) return '2';
  if (value.startsWith('3')) return '3';
  return '';
}

String mapRehabType(String value) {
  if (value == 'تأهيل جزئي') return 'partial';
  if (value == 'تأهيل كامل') return 'complete';
  if (value == 'استبدال') return 'complete';
  return '';
}

String mapProductivity(String value) {
  if (value == 'غير محدد') return '';
  if (value == '0%') return '0';
  if (value == '25%') return '1_25';
  if (value == '50%') return '26_50';
  if (value == '75%') return '51_75';
  if (value == '100%') return '100';
  return '';
}

String mapLabEquipment(String value) {
  if (value == 'غير محدد') return '';
  if (value.startsWith('1')) return 'yes';
  if (value.startsWith('2')) return 'partially';
  if (value.startsWith('3')) return 'no';
  return '';
}

String mapNonOperationalReason(String value) {
  final v = value.trim();
  if (v.isEmpty) return '';
  if (v.contains('سرقة') || v.contains('تخريب')) return 'theft_vandalism';
  if (v.contains('تدمير')) return 'completely_destroyed';
  if (v.contains('طوارئ')) return 'emergency_maintenance';
  if (v.contains('إدارية') || v.contains('اداري')) return 'administrative';
  if (v.contains('دورية')) return 'routine_maintenance';
  if (v.contains('مستمرة')) return 'ongoing_maintenance';
  return 'other';
}

void applyFormToPayload(
  Map<String, dynamic> payload, {
  required int stationId,
  required DateTime registrationDate,
  required String orgUnit,
  required Map<String, String> values,
  required String notOperatingReason,
}) {
  payload
    ..['station_id'] = stationId
    ..['enrollment_date'] = isoDate(registrationDate)
    ..['org_unit'] = orgUnit
    ..['is_operational'] = mapYesNo(values['isWorking']!)
    ..['non_operational_reason'] = mapNonOperationalReason(notOperatingReason)
    ..['building_condition'] = mapCondition(values['buildingStatus']!)
    ..['safety_procedures'] = mapYesNo(values['safetyProcedures']!)
    ..['previously_rehabilitated'] = mapYesNo(values['previousRehab']!)
    ..['rehabilitation_type'] = mapRehabType(values['rehabType']!)
    ..['has_water_hammer_protection'] =
        mapYesNo(values['waterHammerProtection']!)
    ..['water_hammer_efficiency'] =
        mapEfficiency(values['waterHammerEfficiency']!)
    ..['has_water_tanks'] = mapYesNo(values['waterTanks']!)
    ..['is_water_analyzed'] = mapYesNo(values['waterAnalysis']!)
    ..['lab_equipment_status'] = mapLabEquipment(values['labEquipment']!)
    ..['is_boosting_station'] = mapYesNo(values['pumpingStation']!)
    ..['is_well_station'] = mapYesNo(values['wellStation']!)
    ..['is_filtration_station'] = mapYesNo(values['treatmentStation']!)
    ..['has_public_grid_supply'] = mapYesNo(values['publicGrid']!)
    ..['grid_connection_working'] = mapYesNo(values['gridConnectionWorks']!)
    ..['electrical_connection_efficiency'] =
        mapCondition(values['electricalConnectionEfficiency']!)
    ..['transformer_efficiency'] = mapCondition(values['transformerEfficiency']!)
    ..['electrical_panel_efficiency'] = mapCondition(values['panelEfficiency']!)
    ..['grid_power_productivity'] =
        mapProductivity(values['gridEnergyProductivity']!)
    ..['solar_power_available'] = mapYesNo(values['solarAvailable']!)
    ..['solar_power_productivity'] =
        mapProductivity(values['solarProductivity']!)
    ..['solar_system_efficiency'] =
        mapEfficiency(values['solarSystemEfficiency']!)
    ..['generator_available'] = mapYesNo(values['generatorAvailable']!)
    ..['needs_solar_installation'] = mapYesNo(values['needsSolarInstallation']!)
    ..['solar_space_available'] = mapYesNo(values['solarSpaceAvailable']!)
    ..['alternative_power_source'] = mapYesNo(values['alternativeEnergy']!);
}
