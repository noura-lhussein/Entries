import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { ApiService, type ApiParams } from '../../core/services/api.service';
import type { Paginated } from '../../core/models';
import type {
  AnnualBudget,
  AnnualBudgetPayload,
  AnnualBudgetSelectOption,
  BudgetOptionsType,
  BudgetReferenceBase,
  BudgetReferencePayload,
  BudgetReferenceType,
  BudgetSelectOption,
  CategorySelectOption,
  Currency,
  Foundation,
  PreviousProjectOption,
  Project,
  Milestone,
  MilestonePayload,
  Target,
  Policy,
  MeasureUnit,
  ProjectCategory,
  ProjectDashboardStats,
  ProjectPayload,
  ProjectChangeLogEntry,
  ProjectMapPointsResponse,
  ProjectType,
  Responsible,
  BudgetUser,
  BudgetUserPayload,
  ProjectAssignmentUser,
  ProjectAssignmentsResponse,
} from './project-budget.models';
import { environment } from '../../../environments/environment';

export type BudgetReferenceEntity =
  | ProjectCategory
  | Foundation
  | Responsible
  | ProjectType
  | Target
  | Policy
  | MeasureUnit
  | Currency;

export interface ChangeLogFieldOption {
  value: string;
  label: string;
}

@Injectable({ providedIn: 'root' })
export class ProjectBudgetService {
  private api = inject(ApiService);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private readonly base = '/budget';

  list<T extends BudgetReferenceBase>(
    type: BudgetReferenceType,
    params?: ApiParams,
  ): Observable<Paginated<T>> {
    return this.api.get<Paginated<T>>(`${this.base}/${type}/`, params);
  }

  listSelectOptions(type: BudgetOptionsType, params?: ApiParams): Observable<BudgetSelectOption[]> {
    return this.api.get<BudgetSelectOption[]>(`${this.base}/${type}/options/`, params);
  }

  listCategoryOptions(params?: ApiParams): Observable<CategorySelectOption[]> {
    return this.api.get<CategorySelectOption[]>(`${this.base}/categories/options/`, params);
  }

  listAnnualBudgetOptions(params?: ApiParams): Observable<AnnualBudgetSelectOption[]> {
    return this.api.get<AnnualBudgetSelectOption[]>(`${this.base}/annual-budgets/options/`, params);
  }

  create<T extends BudgetReferenceBase>(
    type: BudgetReferenceType,
    payload: BudgetReferencePayload,
  ): Observable<T> {
    return this.api.post<T>(`${this.base}/${type}/`, payload);
  }

  update<T extends BudgetReferenceBase>(
    type: BudgetReferenceType,
    id: number,
    payload: BudgetReferencePayload,
  ): Observable<T> {
    return this.api.patch<T>(`${this.base}/${type}/${id}/`, payload);
  }

  delete(type: BudgetReferenceType, id: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/${type}/${id}/`);
  }

  listAnnualBudgets(params?: ApiParams): Observable<Paginated<AnnualBudget>> {
    return this.api.get<Paginated<AnnualBudget>>(`${this.base}/annual-budgets/`, params);
  }

  createAnnualBudget(payload: AnnualBudgetPayload): Observable<AnnualBudget> {
    return this.api.post<AnnualBudget>(`${this.base}/annual-budgets/`, payload);
  }

  updateAnnualBudget(id: number, payload: AnnualBudgetPayload): Observable<AnnualBudget> {
    return this.api.patch<AnnualBudget>(`${this.base}/annual-budgets/${id}/`, payload);
  }

  deleteAnnualBudget(id: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/annual-budgets/${id}/`);
  }

  listProjects(params?: ApiParams): Observable<Paginated<Project>> {
    return this.api.get<Paginated<Project>>(`${this.base}/projects/`, params);
  }

  getProjectDashboard(params?: ApiParams): Observable<ProjectDashboardStats> {
    return this.api.get<ProjectDashboardStats>(`${this.base}/projects/dashboard/`, params);
  }

  getProjectMapPoints(params?: ApiParams): Observable<ProjectMapPointsResponse> {
    return this.api.get<ProjectMapPointsResponse>(`${this.base}/projects/map-points/`, params);
  }

  listEligiblePreviousProjects(
    annualBudgetId: number,
    excludeProjectId?: number,
  ): Observable<PreviousProjectOption[]> {
    const params: ApiParams = { annual_budget: annualBudgetId };
    if (excludeProjectId != null) {
      params['exclude'] = excludeProjectId;
    }
    return this.api.get<PreviousProjectOption[]>(
      `${this.base}/projects/eligible-previous/`,
      params,
    );
  }

  getProject(id: number): Observable<Project> {
    return this.api.get<Project>(`${this.base}/projects/${id}/`);
  }

  createProject(payload: ProjectPayload): Observable<Project> {
    return this.api.post<Project>(`${this.base}/projects/`, payload);
  }

  updateProject(id: number, payload: ProjectPayload): Observable<Project> {
    return this.api.patch<Project>(`${this.base}/projects/${id}/`, payload);
  }

  deleteProject(id: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/projects/${id}/`);
  }

  listProjectChangeLog(
    projectId: number,
    params?: ApiParams,
  ): Observable<Paginated<ProjectChangeLogEntry>> {
    return this.api.get<Paginated<ProjectChangeLogEntry>>(
      `${this.base}/projects/${projectId}/change-log/`,
      params,
    );
  }

  listProjectChangeLogs(params?: ApiParams): Observable<Paginated<ProjectChangeLogEntry>> {
    return this.api.get<Paginated<ProjectChangeLogEntry>>(
      `${this.base}/project-change-logs/`,
      params,
    );
  }

  listMilestones(params?: ApiParams): Observable<Paginated<Milestone>> {
    return this.api.get<Paginated<Milestone>>(`${this.base}/milestones/`, params);
  }

  getMilestone(id: number): Observable<Milestone> {
    return this.api.get<Milestone>(`${this.base}/milestones/${id}/`);
  }

  createMilestone(payload: MilestonePayload): Observable<Milestone> {
    return this.api.post<Milestone>(`${this.base}/milestones/`, payload);
  }

  updateMilestone(id: number, payload: MilestonePayload): Observable<Milestone> {
    return this.api.patch<Milestone>(`${this.base}/milestones/${id}/`, payload);
  }

  deleteMilestone(id: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/milestones/${id}/`);
  }

  listBudgetUsers(params?: ApiParams): Observable<Paginated<BudgetUser>> {
    return this.api.get<Paginated<BudgetUser>>(`${this.base}/users/`, params);
  }

  getBudgetUser(id: number): Observable<BudgetUser> {
    return this.api.get<BudgetUser>(`${this.base}/users/${id}/`);
  }

  createBudgetUser(payload: BudgetUserPayload): Observable<BudgetUser> {
    return this.api.post<BudgetUser>(`${this.base}/users/`, payload);
  }

  updateBudgetUser(id: number, payload: BudgetUserPayload): Observable<BudgetUser> {
    return this.api.patch<BudgetUser>(`${this.base}/users/${id}/`, payload);
  }

  deleteBudgetUser(id: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/users/${id}/`);
  }

  listProjectAssignments(projectId: number): Observable<ProjectAssignmentUser[]> {
    return this.api.get<ProjectAssignmentUser[]>(`${this.base}/projects/${projectId}/assignments/`);
  }

  addProjectAssignment(projectId: number, userId: number): Observable<ProjectAssignmentUser> {
    return this.api.post<ProjectAssignmentUser>(`${this.base}/projects/${projectId}/assignments/`, {
      user_id: userId,
    });
  }

  removeProjectAssignment(projectId: number, userId: number): Observable<void> {
    return this.api.delete<void>(`${this.base}/projects/${projectId}/assignments/${userId}/`);
  }

  getUserAssignments(userId: number): Observable<ProjectAssignmentsResponse> {
    return this.api.get<ProjectAssignmentsResponse>(`${this.base}/users/${userId}/assignments/`);
  }

  syncUserAssignments(
    userId: number,
    projectIds: number[],
  ): Observable<ProjectAssignmentsResponse> {
    return this.api.put<ProjectAssignmentsResponse>(`${this.base}/users/${userId}/assignments/`, {
      project_ids: projectIds,
    });
  }

  getChangeLogFieldOptions(): Observable<ChangeLogFieldOption[]> {
    return this.http.get<ChangeLogFieldOption[]>(
      `${this.apiUrl}/budget/projects/change-log-fields/`,
    );
  }
}
