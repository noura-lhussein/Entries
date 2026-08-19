export type MasterFieldType =
  | 'string'
  | 'textarea'
  | 'number'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'choice'
  | 'foreign_key';

export type MasterSector = 'oil_gas' | 'electricity' | 'water' | 'mineral';

export interface MasterFieldChoice {
  value: string;
  label: string;
}

export interface MasterFieldSchema {
  name: string;
  type: MasterFieldType;
  required: boolean;
  read_only: boolean;
  choices?: MasterFieldChoice[];
  related_slug?: string | null;
  related_model?: string;
  max_length?: number;
  decimal_places?: number;
}

export interface MasterResourceMeta {
  slug: string;
  label_en: string;
  label_ar: string;
  group_en: string;
  group_ar: string;
  sector: MasterSector;
  list_display: string[];
  read_only: boolean;
  lookup_field: string;
  default_sort_column?: string | null;
  default_sort_direction?: 'asc' | 'desc';
  default_create_values?: Record<string, unknown>;
  fields: MasterFieldSchema[];
  gis_layer_id?: string | null;
  entity_attr_type?: string | null;
  has_map?: boolean;
}

export interface MasterRegistryGroup {
  group_en: string;
  group_ar: string;
  sector: MasterSector;
  resources: string[];
}

export interface MasterRegistryResponse {
  resources: MasterResourceMeta[];
  groups: MasterRegistryGroup[];
}

export interface MasterListResponse {
  slug: string;
  count: number;
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: Record<string, unknown>[];
}

export interface MasterFkOption {
  value: string | number;
  label: string;
}

/** Entity attribute type → master-data admin slug (keep in sync with entity_registry.admin_slug). */
export const ENTITY_ADMIN_SLUGS: Record<string, string> = {
  drinking_station: 'drinking-water-stations',
  dam: 'dams',
  rainfall_station: 'rainfall-stations',
  rainfall_basin: 'rainfall-basins',
  spring: 'springs',
  lake: 'lakes',
  river: 'rivers',
  stream: 'streams',
  geology_unit: 'gis-geology-official',
  power_plant: 'power-plants',
  substation: 'substations',
  transmission_line: 'transmission-lines',
  power_gis_substation_66: 'gis-substations-66',
  power_gis_substation_230: 'gis-substations-230',
  power_gis_substation_400: 'gis-substations-400',
  power_gis_renewable: 'gis-renewable-sites',
  fuel_tank_station: 'fuel-tank-stations',
  hydro_dam: 'hydro-dams',
  load_governorate: 'load-governorates',
  oil_field: 'fields',
  oil_well: 'wells',
  oil_refinery: 'refineries',
  fuel_station: 'fuel-stations',
  storage_depot: 'storage-depots',
  pipeline: 'pipelines',
};
