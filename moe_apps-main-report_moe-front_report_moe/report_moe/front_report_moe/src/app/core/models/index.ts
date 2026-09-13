import type { InfoConfirmStatus } from './info-confirm-status';
import type { EntityAttributeType } from '../../features/builder/entity-attribute-types';

export type { InfoConfirmStatus };

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  status: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_admin: boolean;
  date_joined: string;
  parent_id: number | null;
  parent_name: string | null;
  can_write_info: boolean;
  can_view_info: boolean;
  can_confirm_info: boolean;
  can_export_reports: boolean;
  can_add_user: boolean;
  can_view_budget: boolean;
  can_write_budget: boolean;
  can_manage_budget_users: boolean;
  can_manage_budget: boolean;
  can_manage_reference_data: boolean;
  /** moeds portal sectors — the input; the booleans below are the derived cache. */
  portal_sectors?: string[];
  can_view_oil_gas?: boolean;
  can_write_oil_gas?: boolean;
  can_view_electricity?: boolean;
  can_write_electricity?: boolean;
  can_view_water?: boolean;
  can_write_water?: boolean;
  can_view_mineral?: boolean;
  can_write_mineral?: boolean;
  can_manage_projects?: boolean;
  can_manage_datasets?: boolean;
  can_manage_control_panel?: boolean;
  foundation_id: number | null;
  foundation_name: string | null;
  sub_main_ids: number[];
  title_ids: number[];
  title_category_ids: number[];
  sub_mains: {
    sub_main__id: number;
    sub_main__name: string;
    sub_main__main_section__name: string;
  }[];
  titles: {
    title__id: number;
    title__name: string;
    title__category_id?: number | null;
    title__category_name?: string | null;
  }[];
  title_categories: {
    category__id: number;
    category__name: string;
    category__order: number;
  }[];
}

export interface UserCreate {
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  status?: string | null;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  password: string;
  parent_id?: number | null;
  can_write_info?: boolean;
  can_view_info?: boolean;
  can_confirm_info?: boolean;
  can_export_reports?: boolean;
  can_add_user?: boolean;
  is_admin?: boolean;
  /** moeds portal sectors, subset of water|electricity|oil_gas|mineral|projects */
  portal_sectors?: string[];
  can_manage_datasets?: boolean;
  can_manage_control_panel?: boolean;
  sub_main_ids?: number[];
  title_category_ids?: number[];
  title_ids?: number[];
}

export interface UserUpdate {
  email?: string;
  first_name?: string;
  last_name?: string;
  status?: string | null;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  password?: string;
  parent_id?: number | null;
  can_write_info?: boolean;
  can_view_info?: boolean;
  can_confirm_info?: boolean;
  can_export_reports?: boolean;
  can_add_user?: boolean;
  is_admin?: boolean;
  /** moeds portal sectors, subset of water|electricity|oil_gas|mineral|projects */
  portal_sectors?: string[];
  can_manage_datasets?: boolean;
  can_manage_control_panel?: boolean;
  sub_main_ids?: number[];
  title_category_ids?: number[];
  title_ids?: number[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export interface MainSection {
  id: number;
  name: string;
}

export interface SubMainSection {
  id: number;
  name: string;
  main_section: number;
  main_section_name: string;
  district: number | null;
  district_name: string | null;
}

export interface Title {
  id: number;
  name: string;
  order: number;
  supports_excel?: boolean;
}

export type AttributeType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'date'
  | 'boolean'
  | 'select'
  | 'city'
  | 'district'
  | 'sub_district'
  | 'community'
  | 'image'
  | 'file'
  | EntityAttributeType;

export interface Attribute {
  id: number;
  label: string;
  type: AttributeType;
  required: boolean;
  title: number | null;
  title_name: string | null;
  options: Option[];
}

export interface Option {
  id: number;
  label: string;
  attribute: number;
}

export interface City {
  id: number;
  name: string;
  districts: District[];
}

export interface District {
  id: number;
  name: string;
  city: number;
}

export interface ReqReportTitle {
  id: number;
  title: number;
  title_name: string;
}

export interface ReqReport {
  id: number;
  req_report_sub_main: number;
  sub_main_name: string | null;
  user: number | null;
  user_name: string | null;
  date_from: string | null;
  date_to: string | null;
  report_titles: ReqReportTitle[];
}

export interface Info {
  id: number;
  attribute: number;
  attribute_label: string;
  title_id?: number | null;
  title_name?: string | null;
  sub_main: number | null;
  sub_main_name: string | null;
  main_section_name?: string | null;
  district_name?: string | null;
  city_name?: string | null;
  loc_governorate?: number | null;
  loc_governorate_name?: string | null;
  loc_district?: number | null;
  loc_district_name?: string | null;
  loc_subdistrict?: number | null;
  loc_subdistrict_name?: string | null;
  loc_community?: number | null;
  loc_community_name?: string | null;
  user: number | null;
  user_name: string | null;
  value: string;
  confirmed: InfoConfirmStatus;
  confirm_note?: string;
  commit_note?: string;
  created_at: string;
}

export interface UserSubMain {
  id: number;
  user: number;
  user_name?: string;
  sub_main: number;
  sub_main_name: string;
}

export interface UserTitle {
  id: number;
  user: number;
  user_name?: string;
  title: number;
  title_name: string;
}

export interface DashboardActivity {
  action: string;
  model_name: string;
  object_id: number | null;
  details: Record<string, unknown> | null;
  timestamp: string;
  user_name: string;
}

export interface DashboardStats {
  is_admin_view?: boolean;
  users_count?: number;
  main_sections_count?: number;
  sub_sections_count?: number;
  reports_count?: number;
  titles_count?: number;
  attributes_count?: number;
  infos_count: number;
  infos_confirmed_count: number;
  infos_pending_count: number;
  confirmation_rate: number;
  rows_count: number;
  rows_confirmed_count: number;
  rows_pending_count: number;
  rows_confirmation_rate: number;
  activity_rate_7d: number;
  recent_activities: DashboardActivity[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
