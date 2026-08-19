import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { TranslationService } from '../../shared/services/translation.service';
import { ToastService } from '../../shared/services/toast.service';
import { Paginated } from '../../core/models';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import { FilterState } from '../../shared/utils/filter-state';
import { ResetPasswordDialogComponent } from '../../shared/components/reset-password-dialog/reset-password-dialog.component';
import { ProjectBudgetService } from './project-budget.service';
import type { BudgetUser } from './project-budget.models';

@Component({
  selector: 'app-budget-users-list',
  standalone: true,
  imports: [ListPageComponent],
  template: `
    <app-list-page
      [config]="pageConfig()"
      (onSearch)="fs.onSearch($event)"
      (onFilterChange)="fs.onFilterChange($event)"
      (onPrevious)="fs.previousPage()"
      (onNext)="fs.nextPage()"
      (onGoToPage)="fs.goToPage($event)"
      (onClearFilters)="fs.clearFilters()"
    ></app-list-page>
  `,
})
export class BudgetUsersListComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private router = inject(Router);
  private toast = inject(ToastService);
  private dialog = inject(MatDialog);
  translation = inject(TranslationService);

  fs = new FilterState(() => this.load(), 'search');

  users = signal<BudgetUser[]>([]);

  headerAction = computed(() => ({
    label: this.translation.t('budget.users.add-new'),
    icon: 'add',
    routerLink: '/budget/users/new',
  }));

  columns = computed(() => [
    { key: 'full_name', label: this.translation.t('budget.users.full-name'), sortable: true },
    { key: 'username', label: this.translation.t('budget.users.username'), sortable: true },
    {
      key: 'foundation_name',
      label: this.translation.t('budget.fields.foundation'),
      sortable: false,
    },
    {
      key: 'assigned_project_count',
      label: this.translation.t('budget.users.assigned-projects-count'),
      sortable: false,
    },
    {
      key: 'is_active',
      label: this.translation.t('budget.users.status'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_view_budget',
      label: this.translation.t('budget.users.can-view'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_write_budget',
      label: this.translation.t('budget.users.can-write'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_manage_budget_users',
      label: this.translation.t('budget.users.can-manage-users'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_manage_budget',
      label: this.translation.t('budget.users.can-manage-budget'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_manage_reference_data',
      label: this.translation.t('budget.users.can-manage-reference-data'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
  ]);

  actions = computed(() => [
    {
      type: 'edit',
      icon: 'edit',
      label: this.translation.t('budget.users.edit'),
      color: 'edit' as const,
      action: (id: number) => this.editUser(id),
    },
    {
      type: 'reset-password',
      icon: 'lock_reset',
      label: this.translation.t('budget.users.reset-password'),
      color: 'primary' as const,
      action: (id: number) => this.resetPassword(id),
    },
    {
      type: 'delete',
      icon: 'delete',
      label: this.translation.t('budget.users.delete'),
      color: 'delete' as const,
      action: (id: number) => this.deleteUser(id),
    },
  ]);

  pageConfig = computed(() => ({
    title: this.translation.t('budget.users.title'),
    description: this.translation.t('budget.users.description'),
    headerAction: this.headerAction(),
    searchPlaceholder: this.translation.t('budget.users.search-placeholder'),
    filterGroups: [],
    columns: this.columns(),
    data: this.users(),
    actions: this.actions(),
    loading: this.fs.loading(),
    currentPage: this.fs.currentPage(),
    totalPages: this.fs.totalPages(),
    totalItems: this.fs.totalCount(),
    pageSize: this.fs.pageSize(),
    emptyMessage: this.translation.t('budget.users.empty'),
  }));

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.fs.loading.set(true);
    this.budget.listBudgetUsers(this.fs.params).subscribe({
      next: (data: Paginated<BudgetUser>) => {
        this.users.set(data.results);
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => this.fs.loading.set(false),
    });
  }

  editUser(id: number): void {
    this.router.navigate(['/budget/users', id, 'edit']);
  }

  resetPassword(id: number): void {
    const user = this.users().find((u) => u.id === id);
    const ref = this.dialog.open(ResetPasswordDialogComponent, {
      data: { userId: id, username: user?.username ?? '' },
      disableClose: false,
      hasBackdrop: true,
    });

    ref.afterClosed().subscribe((password: string | null) => {
      if (!password) return;
      this.budget.updateBudgetUser(id, { password }).subscribe({
        next: () => this.toast.success(this.translation.t('budget.users.reset-password-success')),
        error: () => this.toast.error(this.translation.t('budget.users.reset-password-error')),
      });
    });
  }

  deleteUser(id: number): void {
    if (confirm(this.translation.t('budget.users.confirm-delete'))) {
      this.budget.deleteBudgetUser(id).subscribe({
        next: () => {
          this.toast.success(this.translation.t('budget.users.delete-success'));
          this.load();
        },
        error: () => this.toast.error(this.translation.t('budget.users.delete-error')),
      });
    }
  }
}
