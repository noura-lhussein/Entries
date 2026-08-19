export type BudgetReferenceType =
  | 'categories'
  | 'foundations'
  | 'responsibles'
  | 'project-types'
  | 'targets'
  | 'policies'
  | 'measure-units'
  | 'currencies';

export type BudgetOptionsType =
  | 'categories'
  | 'foundations'
  | 'project-types'
  | 'targets'
  | 'policies'
  | 'measure-units'
  | 'currencies';

export interface BudgetSelectOption {
  id: number;
  name: string;
}

export interface CategorySelectOption extends BudgetSelectOption {
  code?: string;
  parent: number | null;
  breadcrumb: string[];
  depth: number;
}

export interface AnnualBudgetSelectOption extends BudgetSelectOption {
  code: string;
  year: number;
}

export interface BudgetReferenceBase {
  id: number;
  name_ar?: string;
  name_en?: string;
  deleted?: boolean;
}

export interface ProjectCategory extends BudgetReferenceBase {
  parent: number | null;
  parent_name: string | null;
}

export type Foundation = BudgetReferenceBase;

export interface Responsible extends BudgetReferenceBase {
  foundation: number;
  foundation_name: string;
  phone: string;
  email: string;
}

export type ProjectType = BudgetReferenceBase;

export interface Target extends BudgetReferenceBase {
  description?: string;
}

export type Policy = Target;

export interface MeasureUnit extends BudgetReferenceBase {
  symbol?: string;
}

export interface Currency extends BudgetReferenceBase {
  code: string;
  symbol: string;
  exchange_rate: string | number;
}

export interface Currency extends BudgetReferenceBase {
  code: string;
  symbol: string;
  exchange_rate: string | number;
}

export interface BudgetReferencePayload {
  name_ar?: string;
  name_en?: string;
  description?: string;
  parent?: number | null;
  foundation?: number | null;
  phone?: string;
  email?: string;
  code?: string;
  symbol?: string;
  exchange_rate?: number | string;
}

export interface AnnualBudget {
  id: number;
  project_type: number;
  project_type_name: string;
  currency: number;
  currency_code: string;
  code: string;
  year: number;
  amount: string | number;
  notes: string;
  approved_at: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AnnualBudgetPayload {
  project_type?: number | null;
  currency?: number | null;
  year?: number | null;
  amount?: number | string | null;
  notes?: string | null;
  approved_at?: string | null;
}

export type ProjectStatus = 'draft' | 'active' | 'on_hold' | 'completed' | 'cancelled';

export interface PreviousProjectOption {
  id: number;
  code: string;
  name_ar: string;
  annual_budget_year: number;
}

export interface Project {
  id: number;
  annual_budget: number;
  annual_budget_year: number;
  annual_budget_code: string;
  project_type_id: number;
  project_type_name: string;
  foundation: number;
  foundation_name: string;
  governorate: number;
  governorate_name: string;
  district: number;
  district_name: string;
  subdistrict: number;
  subdistrict_name: string;
  community: number;
  community_name: string;
  previous_project: number | null;
  previous_project_name: string | null;
  is_round: boolean;
  code: string;
  name_ar: string;
  name_en: string;
  latitude: string | number | null;
  longitude: string | number | null;
  percentage_completion: string | number;
  completion_is_manual: boolean;
  proposed_budget: string | number;
  approved_budget: string | number;
  budget_expenditure: string | number;
  status: ProjectStatus;
  description: string;
  start_date: string;
  end_date: string;
  target: number | null;
  target_name: string | null;
  policy: number | null;
  policy_name: string | null;
  quantitative_target_value: string | number | null;
  quantitative_target_unit: number | null;
  quantitative_target_unit_name: string | null;
  quantitative_target_unit_symbol: string | null;
}

export interface ProjectPayload {
  annual_budget?: number | null;
  foundation?: number | null;
  community?: number | null;
  previous_project?: number | null;
  is_round?: boolean;
  name_ar?: string;
  name_en?: string;
  latitude?: number | string | null;
  longitude?: number | string | null;
  percentage_completion?: number | string | null;
  completion_is_manual?: boolean;
  proposed_budget?: number | string | null;
  approved_budget?: number | string | null;
  budget_expenditure?: number | string | null;
  status?: ProjectStatus | null;
  description?: string;
  start_date?: string | null;
  end_date?: string | null;
  target?: number | null;
  policy?: number | null;
  quantitative_target_value?: number | string | null;
  quantitative_target_unit?: number | null;
  _change_meta?: ProjectChangeMeta;
}

export interface ProjectChangeMeta {
  client_latitude?: number | null;
  client_longitude?: number | null;
}

export type ProjectChangeAction = 'create' | 'update' | 'delete';

export interface ProjectChangeLogEntry {
  id: number;
  project_id: number;
  project_name: string;
  project_code: string;
  batch_id: string;
  action: ProjectChangeAction;
  field_name: string;
  field_label: string;
  old_value: string;
  new_value: string;
  changed_by: number | null;
  changed_by_name: string;
  changed_by_username: string | null;
  changed_at: string;
  ip_address: string | null;
  client_latitude: string | number | null;
  client_longitude: string | number | null;
  user_agent: string;
}

export const PROJECT_STATUSES: ProjectStatus[] = [
  'draft',
  'active',
  'on_hold',
  'completed',
  'cancelled',
];

export type MilestoneStatus = ProjectStatus;
export const MILESTONE_STATUSES: MilestoneStatus[] = [...PROJECT_STATUSES];

export interface Milestone {
  id: number;
  project: number;
  project_name: string;
  parent: number | null;
  parent_name: string | null;
  responsible: number | null;
  responsible_name: string | null;
  category: number | null;
  category_name: string | null;
  name_ar: string;
  name_en: string;
  latitude: string | number | null;
  longitude: string | number | null;
  percentage_completion: string | number;
  start_date: string | null;
  end_date: string | null;
  order: number;
  due_date: string | null;
  status: MilestoneStatus;
}

export interface MilestonePayload {
  project?: number | null;
  parent?: number | null;
  responsible?: number | null;
  category?: number | null;
  name_ar?: string;
  name_en?: string;
  latitude?: number | string | null;
  longitude?: number | string | null;
  percentage_completion?: number | string | null;
  start_date?: string | null;
  end_date?: string | null;
  order?: number | null;
  due_date?: string | null;
  status?: MilestoneStatus | null;
}

export interface BudgetUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  status: string | null;
  is_active: boolean;
  foundation: number | null;
  foundation_name: string | null;
  assigned_project_ids?: number[];
  assigned_project_count?: number;
  can_view_budget: boolean;
  can_write_budget: boolean;
  can_manage_budget_users: boolean;
  can_manage_budget: boolean;
  can_manage_reference_data: boolean;
}

export interface ProjectAssignmentUser {
  id: number;
  username: string;
  full_name: string;
  email: string;
}

export interface ProjectAssignmentsResponse {
  project_ids: number[];
}

export interface BudgetUserPayload {
  username?: string;
  password?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  status?: string | null;
  is_active?: boolean;
  foundation?: number | null;
  can_view_budget?: boolean;
  can_write_budget?: boolean;
  can_manage_budget_users?: boolean;
  can_manage_budget?: boolean;
  can_manage_reference_data?: boolean;
}

export interface ProjectDashboardSummary {
  total_projects: number;
  active_projects: number;
  avg_completion: number;
  total_approved_budget: string;
  total_expenditure: string;
  expenditure_percent: number | null;
  remaining_budget: string;
  over_budget_count: number;
  overdue_count: number;
  milestones_count: number;
  avg_milestone_completion: number;
  projects_without_milestones?: number;
}

export interface ProjectDashboardCategoryItem {
  id: number;
  parent_id: number | null;
  code: string;
  name: string;
  project_count: number;
  total_expenditure: string;
}

export interface ProjectDashboardCategorySection {
  prefix: string;
  project_count: number;
  total_expenditure: string;
}

export interface ProjectDashboardBreakdownItem {
  id?: number | null;
  name?: string;
  status?: string;
  count: number;
}

export interface ProjectDashboardProjectRow {
  id: number;
  code: string;
  name_ar: string;
  status: ProjectStatus;
  percentage_completion: number;
  end_date: string | null;
  approved_budget: string;
  budget_expenditure: string;
  expenditure_percent: number | null;
}

export interface ProjectDashboardStats {
  summary: ProjectDashboardSummary;
  by_status: ProjectDashboardBreakdownItem[];
  by_governorate: ProjectDashboardBreakdownItem[];
  by_project_type: ProjectDashboardBreakdownItem[];
  by_category: ProjectDashboardCategoryItem[];
  by_category_section: ProjectDashboardCategorySection[];
  uncategorized_projects: number;
  uncategorized_expenditure: string;
  low_completion_projects: ProjectDashboardProjectRow[];
  overdue_projects: ProjectDashboardProjectRow[];
}

export interface ProjectMapPoint {
  id: number;
  name_ar: string;
  name_en: string;
  code: string;
  status: ProjectStatus;
  governorate_id: number | null;
  governorate_name: string;
  community_id: number | null;
  community_name: string;
  latitude: number;
  longitude: number;
}

export interface ProjectMapPointsResponse {
  count: number;
  total_projects: number;
  without_coordinates: number;
  truncated: boolean;
  results: ProjectMapPoint[];
}
