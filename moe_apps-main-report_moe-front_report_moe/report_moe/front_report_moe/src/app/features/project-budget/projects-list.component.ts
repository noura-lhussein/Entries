import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import type { TableColumn } from '../../shared/components/data-table/data-table.component';
import type { FilterGroup } from '../../shared/components/filter-panel/filter-panel.component';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { DialogService } from '../../shared/services/dialog.service';
import { TranslationService } from '../../shared/services/translation.service';
import { LocationsService } from '../../shared/services/locations.service';
import { FilterState } from '../../shared/utils/filter-state';
import {
  PROJECT_STATUSES,
  type BudgetSelectOption,
  type Project,
  type ProjectStatus,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';
import { budgetExpenditurePercent } from './budget-expenditure.utils';

type ProjectRow = Project & {
  status_label: string;
  approved_budget_label: string;
  expenditure_percent: number | null;
};

@Component({
  selector: 'app-budget-projects',
  standalone: true,
  imports: [CommonModule, ListPageComponent],
  template: `
    <app-list-page
      [config]="pageConfig()"
      (onSearch)="fs.onSearch($event)"
      (onFilterChange)="onFilterChange($event)"
      (onClearFilter)="clearFilter($event)"
      (onPrevious)="fs.previousPage()"
      (onNext)="fs.nextPage()"
      (onGoToPage)="fs.goToPage($event)"
      (onClearFilters)="fs.clearFilters()"
    ></app-list-page>
  `,
})
export class ProjectsListComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private locations = inject(LocationsService);
  private router = inject(Router);
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private confirmDialog = inject(DialogService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), 'search');

  rows = signal<ProjectRow[]>([]);
  foundations = signal<BudgetSelectOption[]>([]);
  projectTypes = signal<BudgetSelectOption[]>([]);
  governorates = signal<BudgetSelectOption[]>([]);
  communities = signal<BudgetSelectOption[]>([]);
  budgetYears = signal<{ value: string; label: string }[]>([]);

  filterGroups = computed<FilterGroup[]>(() => [
    {
      label: this.t('budget.projects.status'),
      key: 'status',
      type: 'select',
      options: PROJECT_STATUSES.map((status) => ({
        value: status,
        label: this.statusLabel(status),
      })),
    },
    {
      label: this.t('budget.annual-budget.project-type'),
      key: 'project_type',
      type: 'select',
      options: this.projectTypes().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('budget.projects.filter-year'),
      key: 'year',
      type: 'select',
      options: this.budgetYears(),
    },
    {
      label: this.t('budget.fields.foundation'),
      key: 'foundation',
      type: 'select',
      options: this.foundations().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('locations.governorate'),
      key: 'governorate',
      type: 'select',
      options: this.governorates().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('locations.community'),
      key: 'community',
      type: 'select',
      options: this.communities().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
  ]);

  columns = computed<TableColumn[]>(() => [
    {
      key: 'name_ar',
      subtitleKey: 'code',
      label: this.t('budget.fields.name-ar'),
      sortable: true,
      type: 'stacked',
      align: 'start',
      minWidth: '240px',
    },
    {
      key: 'project_type_name',
      label: this.t('budget.annual-budget.project-type'),
      minWidth: '130px',
    },
    {
      key: 'annual_budget_year',
      label: this.t('budget.annual-budget.year'),
      sortable: true,
      minWidth: '72px',
    },
    {
      key: 'approved_budget_label',
      label: this.t('budget.projects.approved-budget'),
      minWidth: '120px',
    },
    {
      key: 'expenditure_percent',
      label: this.t('budget.projects.expenditure-percent'),
      type: 'progress-percent',
      minWidth: '100px',
    },
    {
      key: 'status',
      labelKey: 'status_label',
      label: this.t('budget.projects.status'),
      type: 'project-status',
      minWidth: '96px',
    },
  ]);

  actions = computed(() => [
    {
      icon: 'visibility',
      label: this.t('budget.projects.view'),
      action: (id: number) => this.viewProject(id),
    },
    {
      icon: 'edit',
      label: this.t('common.edit'),
      action: (id: number) => this.editProject(id),
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
    title: this.t('budget.projects.title'),
    description: this.t('budget.projects.page-description'),
    headerAction: {
      label: this.t('budget.projects.add-title'),
      icon: 'add',
      click: () => this.addProject(),
    },
    searchPlaceholder: this.t('budget.projects.search'),
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
    emptyMessage: this.t('budget.projects.empty'),
  }));

  ngOnInit(): void {
    this.loadDependencies();
    this.load();
  }

  clearFilter(key: string): void {
    this.fs.onFilterChange({ key, value: '' });
    if (key === 'governorate') {
      if (this.fs.filters()['community']) {
        this.fs.filters.update((f) => {
          const next = { ...f };
          delete next['community'];
          return next;
        });
      }
      this.loadCommunityOptions();
    }
  }

  onFilterChange(filter: {
    key: string;
    value: string | number | boolean | null | Array<string | number>;
  }): void {
    this.fs.onFilterChange(filter);
    if (filter.key === 'governorate') {
      if (this.fs.filters()['community']) {
        this.fs.filters.update((f) => {
          const next = { ...f };
          delete next['community'];
          return next;
        });
      }
      this.loadCommunityOptions();
    }
  }

  addProject(): void {
    this.router.navigate(['/budget/projects/new']);
  }

  viewProject(id: number): void {
    this.router.navigate(['/budget/projects', id, 'view']);
  }

  editProject(id: number): void {
    this.router.navigate(['/budget/projects', id, 'edit']);
  }

  load(): void {
    this.fs.loading.set(true);
    this.budget.listProjects(this.fs.params).subscribe({
      next: (data) => {
        this.rows.set(
          data.results.map((row) => ({
            ...row,
            status_label: this.statusLabel(row.status),
            approved_budget_label: this.formatMoney(row.approved_budget),
            expenditure_percent: budgetExpenditurePercent(
              row.approved_budget,
              row.budget_expenditure,
            ),
          })),
        );
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.projects.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  async delete(id: number): Promise<void> {
    const confirmed = await this.confirmDialog.confirm({
      title: this.t('user-data.delete-confirm-title'),
      message: this.t('budget.projects.confirm-delete'),
      type: 'error',
      icon: 'delete',
      confirmLabel: this.t('common.delete'),
      cancelLabel: this.t('common.cancel'),
    });
    if (!confirmed) return;
    this.budget.deleteProject(id).subscribe({
      next: () => {
        this.toast.success(this.t('budget.projects.delete-success'));
        this.load();
      },
      error: () => this.toast.error(this.t('budget.projects.delete-error')),
    });
  }

  statusLabel(status: ProjectStatus): string {
    return this.t(`budget.projects.status.${status}`);
  }

  private formatMoney(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return '—';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parsed);
  }

  private loadDependencies(): void {
    this.budget.listSelectOptions('foundations').subscribe({
      next: (data) => this.foundations.set(data),
    });
    this.budget.listSelectOptions('project-types').subscribe({
      next: (data) => this.projectTypes.set(data),
    });
    this.locations.listGovernorateOptions().subscribe({
      next: (data) => this.governorates.set(data),
    });
    this.loadCommunityOptions();
    this.budget.listAnnualBudgets({ page_size: 100 }).subscribe({
      next: (data) => {
        const years = [...new Set(data.results.map((item) => item.year))].sort(
          (left, right) => right - left,
        );
        this.budgetYears.set(
          years.map((year) => ({
            value: String(year),
            label: String(year),
          })),
        );
      },
    });
  }

  private loadCommunityOptions(): void {
    const governorate = this.fs.filters()['governorate'];
    if (!governorate) {
      this.communities.set([]);
      return;
    }
    this.locations.listCommunityOptions({ governorate: String(governorate) }).subscribe({
      next: (data) => this.communities.set(data),
      error: () => this.communities.set([]),
    });
  }
}
