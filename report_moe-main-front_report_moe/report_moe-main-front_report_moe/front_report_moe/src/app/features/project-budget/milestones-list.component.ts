import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import type { TableColumn } from '../../shared/components/data-table/data-table.component';
import type { FilterGroup } from '../../shared/components/filter-panel/filter-panel.component';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { FilterState } from '../../shared/utils/filter-state';
import {
  MILESTONE_STATUSES,
  type BudgetSelectOption,
  type Milestone,
  type MilestoneStatus,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';

type MilestoneRow = Milestone & { status_label: string };

@Component({
  selector: 'app-budget-milestones',
  standalone: true,
  imports: [CommonModule, ListPageComponent],
  template: `
    <app-list-page
      [config]="pageConfig()"
      (onSearch)="fs.onSearch($event)"
      (onFilterChange)="fs.onFilterChange($event)"
      (onClearFilter)="clearFilter($event)"
      (onPrevious)="fs.previousPage()"
      (onNext)="fs.nextPage()"
      (onGoToPage)="fs.goToPage($event)"
      (onClearFilters)="fs.clearFilters()"
    ></app-list-page>
  `,
})
export class MilestonesListComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private router = inject(Router);
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), 'search');

  rows = signal<MilestoneRow[]>([]);
  projects = signal<BudgetSelectOption[]>([]);
  responsibles = signal<BudgetSelectOption[]>([]);

  filterGroups = computed<FilterGroup[]>(() => [
    {
      label: this.t('budget.milestones.status'),
      key: 'status',
      type: 'select',
      options: MILESTONE_STATUSES.map((status) => ({
        value: status,
        label: this.statusLabel(status),
      })),
    },
    {
      label: this.t('budget.milestones.project'),
      key: 'project',
      type: 'select',
      options: this.projects().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('budget.milestones.responsible'),
      key: 'responsible',
      type: 'select',
      options: this.responsibles().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
  ]);

  columns = computed<TableColumn[]>(() => [
    { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
    { key: 'project_name', label: this.t('budget.milestones.project') },
    { key: 'category_name', label: this.t('budget.milestones.category') },
    { key: 'parent_name', label: this.t('budget.milestones.parent') },
    { key: 'responsible_name', label: this.t('budget.milestones.responsible') },
    { key: 'order', label: this.t('budget.milestones.order') },
    { key: 'due_date', label: this.t('budget.milestones.due-date') },
    { key: 'percentage_completion', label: this.t('budget.milestones.percentage') },
    { key: 'status_label', label: this.t('budget.milestones.status') },
  ]);

  actions = computed(() => [
    {
      icon: 'visibility',
      label: this.t('budget.milestones.view'),
      action: (id: number) => this.viewMilestone(id),
    },
    {
      icon: 'edit',
      label: this.t('common.edit'),
      action: (id: number) => this.editMilestone(id),
      show: () => this.auth.canWriteBudget(),
    },
    {
      icon: 'delete',
      label: this.t('common.delete'),
      action: (id: number) => this.delete(id),
      show: () => this.auth.canWriteBudget(),
    },
  ]);

  pageConfig = computed(() => ({
    title: this.t('budget.milestones.title'),
    description: this.t('budget.milestones.page-description'),
    headerAction: this.auth.canWriteBudget()
      ? {
          label: this.t('budget.milestones.add-title'),
          icon: 'add',
          click: () => this.addMilestone(),
        }
      : undefined,
    searchPlaceholder: this.t('budget.milestones.search'),
    filterGroups: this.filterGroups(),
    activeFilters: this.fs.filters(),
    columns: this.columns(),
    data: this.rows(),
    actions: this.actions(),
    loading: this.fs.loading(),
    currentPage: this.fs.currentPage(),
    totalPages: this.fs.totalPages(),
    totalItems: this.fs.totalCount(),
    pageSize: this.fs.pageSize(),
    emptyMessage: this.t('budget.milestones.empty'),
  }));

  ngOnInit(): void {
    this.loadDependencies();
    this.load();
  }

  clearFilter(key: string): void {
    this.fs.onFilterChange({ key, value: '' });
  }

  viewMilestone(id: number): void {
    this.router.navigate(['/budget/milestones', id, 'view']);
  }

  addMilestone(): void {
    this.router.navigate(['/budget/milestones/new']);
  }

  editMilestone(id: number): void {
    this.router.navigate(['/budget/milestones', id, 'edit']);
  }

  load(): void {
    this.fs.loading.set(true);
    this.budget.listMilestones(this.fs.params).subscribe({
      next: (data) => {
        this.rows.set(
          data.results.map((row) => ({
            ...row,
            status_label: this.statusLabel(row.status),
          })),
        );
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.milestones.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  delete(id: number): void {
    if (!confirm(this.t('budget.milestones.confirm-delete'))) return;
    this.budget.deleteMilestone(id).subscribe({
      next: () => {
        this.toast.success(this.t('budget.milestones.delete-success'));
        this.load();
      },
      error: () => this.toast.error(this.t('budget.milestones.delete-error')),
    });
  }

  statusLabel(status: MilestoneStatus): string {
    return this.t(`budget.milestones.status.${status}`);
  }

  private loadDependencies(): void {
    this.budget.listProjects({ page_size: 500 }).subscribe({
      next: (data) =>
        this.projects.set(
          data.results.map((item) => ({
            id: item.id,
            name: item.name_ar || item.code || String(item.id),
          })),
        ),
    });
    this.budget.list('responsibles', { page_size: 500 }).subscribe({
      next: (data) =>
        this.responsibles.set(
          data.results.map((item) => ({
            id: item.id,
            name: item.name_ar || item.name_en || String(item.id),
          })),
        ),
    });
  }
}
