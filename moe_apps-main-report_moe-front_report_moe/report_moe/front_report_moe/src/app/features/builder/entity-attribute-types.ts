/** Form Builder entity attribute types (Master dropdowns). Keep in sync with backend ENTITY_TYPE_SPECS. */
export const ENTITY_ATTRIBUTE_TYPES = [
  'drinking_station',
  'dam',
  'rainfall_station',
  'rainfall_basin',
  'spring',
  'lake',
  'river',
  'stream',
  'geology_unit',
  'power_plant',
  'substation',
  'transmission_line',
  'power_gis_substation_66',
  'power_gis_substation_230',
  'power_gis_substation_400',
  'power_gis_renewable',
  'fuel_tank_station',
  'hydro_dam',
  'load_governorate',
  'oil_field',
  'oil_well',
  'oil_refinery',
  'fuel_station',
  'storage_depot',
  'pipeline',
] as const;

export type EntityAttributeType = (typeof ENTITY_ATTRIBUTE_TYPES)[number];

export function isEntityAttributeType(type: string): boolean {
  return (ENTITY_ATTRIBUTE_TYPES as readonly string[]).includes(type);
}
