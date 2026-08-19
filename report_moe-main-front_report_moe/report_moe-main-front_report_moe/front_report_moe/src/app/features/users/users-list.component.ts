import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { BuilderService } from '../../core/services/builder.service';
import { TranslationService } from '../../shared/services/translation.service';
import { ToastService } from '../../shared/services/toast.service';
import { User, Paginated } from '../../core/models';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import type { FilterGroup } from '../../shared/components/filter-panel/filter-panel.component';
import { FilterState } from '../../shared/utils/filter-state';
import { ResetPasswordDialogComponent } from '../../shared/components/reset-password-dialog/reset-password-dialog.component';
import { UserInfoDialogComponent } from '../../shared/components/user-info-dialog/user-info-dialog.component';

@Component({
  selector: 'app-users-list',
  standalone: true,
  imports: [ListPageComponent],
  template: `
    <app-list-page
      [config]="pageConfig()"
      (onSearch)="fs.onSearch($event)"
      (onFilterChange)="fs.onFilterChange($event)"
      (onClearFilter)="fs.clearFilter($event)"
      (onPrevious)="fs.previousPage()"
      (onNext)="fs.nextPage()"
      (onGoToPage)="fs.goToPage($event)"
      (onClearFilters)="fs.clearFilters()"
    ></app-list-page>
  `,
})
export class UsersListComponent implements OnInit {
  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private toast = inject(ToastService);
  private dialog = inject(MatDialog);
  translation = inject(TranslationService);

  fs = new FilterState(() => this.load(), 'search');

  users = signal<User[]>([]);
  titleCategoryOptions = signal<{ value: string; label: string }[]>([]);
  subMainOptions = signal<{ value: string; label: string }[]>([]);
  parentOptions = signal<{ value: string; label: string }[]>([]);

  headerAction = computed(() => ({
    label: this.translation.t('users.add-new'),
    icon: 'add',
    routerLink: '/users/new',
  }));

  yesNoOptions = computed(() => [
    { value: 'true', label: this.translation.t('filter.yes') },
    { value: 'false', label: this.translation.t('filter.no') },
  ]);

  filterGroups = computed<FilterGroup[]>(() => [
    {
      label: this.translation.t('users.status'),
      key: 'is_active',
      type: 'select',
      options: [
        { value: 'true', label: this.translation.t('users.info-dialog.active') },
        { value: 'false', label: this.translation.t('users.info-dialog.inactive') },
      ],
    },
    {
      label: this.translation.t('users.filter-sub-section'),
      key: 'sub_main',
      type: 'select',
      options: this.subMainOptions(),
    },
    {
      label: this.translation.t('users.filter-title-category'),
      key: 'title_category',
      type: 'select',
      options: this.titleCategoryOptions(),
    },
    {
      label: this.translation.t('users.parent-name'),
      key: 'parent',
      type: 'select',
      options: this.parentOptions(),
    },
    {
      label: this.translation.t('users.can-write'),
      key: 'can_write_info',
      type: 'select',
      options: this.yesNoOptions(),
    },
    {
      label: this.translation.t('users.can-view'),
      key: 'can_view_info',
      type: 'select',
      options: this.yesNoOptions(),
    },
    {
      label: this.translation.t('users.can-confirm'),
      key: 'can_confirm_info',
      type: 'select',
      options: this.yesNoOptions(),
    },
    {
      label: this.translation.t('users.can-export'),
      key: 'can_export_reports',
      type: 'select',
      options: this.yesNoOptions(),
    },
    {
      label: this.translation.t('users.can-add-user'),
      key: 'can_add_user',
      type: 'select',
      options: this.yesNoOptions(),
    },
  ]);

  columns = computed(() => [
    { key: 'full_name', label: this.translation.t('users.full-name'), sortable: true },
    { key: 'username', label: this.translation.t('users.username'), sortable: true },
    { key: 'parent_name', label: this.translation.t('users.parent-name'), sortable: false },
    {
      key: 'is_active',
      label: this.translation.t('users.status'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_write_info',
      label: this.translation.t('users.can-write'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_view_info',
      label: this.translation.t('users.can-view'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_confirm_info',
      label: this.translation.t('users.can-confirm'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_export_reports',
      label: this.translation.t('users.can-export'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
    {
      key: 'can_add_user',
      label: this.translation.t('users.can-add-user'),
      type: 'boolean-icon' as const,
      sortable: false,
    },
  ]);

  actions = computed(() => [
    {
      type: 'info',
      icon: 'info',
      label: this.translation.t('users.view-info'),
      color: 'primary' as const,
      action: (id: number) => this.viewUserInfo(id),
    },
    {
      type: 'edit',
      icon: 'edit',
      label: this.translation.t('users.edit'),
      color: 'edit' as const,
      action: (id: number) => this.editUser(id),
    },
    {
      type: 'assign',
      icon: 'badge',
      label: this.translation.t('users.assign'),
      color: 'primary' as const,
      action: (id: number) => this.assignPermissions(id),
      show: () => this.auth.isAdmin(),
    },
    {
      type: 'reset-password',
      icon: 'lock_reset',
      label: this.translation.t('users.reset-password'),
      color: 'primary' as const,
      action: (id: number) => this.resetPassword(id),
    },
    {
      type: 'delete',
      icon: 'delete',
      label: this.translation.t('users.delete'),
      color: 'delete' as const,
      action: (id: number) => this.deleteUser(id),
    },
  ]);

  pageConfig = computed(() => ({
    title: this.translation.t('users.title'),
    description: this.translation.t('users.description'),
    headerAction: this.headerAction(),
    searchPlaceholder: this.translation.t('users.search-placeholder'),
    filterGroups: this.filterGroups(),
    activeFilters: this.fs.filters(),
    columns: this.columns(),
    data: this.users(),
    actions: this.actions(),
    loading: this.fs.loading(),
    currentPage: this.fs.currentPage(),
    totalPages: this.fs.totalPages(),
    totalItems: this.fs.totalCount(),
    pageSize: this.fs.pageSize(),
    emptyMessage: this.translation.t('users.no-users'),
  }));

  ngOnInit(): void {
    this.loadFilterOptions();
    this.load();
  }

  loadFilterOptions(): void {
    forkJoin({
      titleCategories: this.builder.getTitleCategories(),
      subs: this.builder.getSubMainSections(),
      parents: this.api.get<Paginated<User>>('/users/', { page_size: 500 }),
    }).subscribe({
      next: ({ titleCategories, subs, parents }) => {
        this.titleCategoryOptions.set(
          (titleCategories.results || []).map((c) => ({
            value: String(c.id),
            label: c.name,
          })),
        );
        this.subMainOptions.set(
          (subs.results || []).map((s: any) => ({
            value: String(s.id),
            label: s.parent_name ? `${s.parent_name} / ${s.name}` : s.name,
          })),
        );
        this.parentOptions.set(
          (parents.results || []).map((u) => ({
            value: String(u.id),
            label: u.full_name || u.username,
          })),
        );
      },
    });
  }

  load(): void {
    this.fs.loading.set(true);
    this.api.get<Paginated<User>>('/users/', this.fs.params).subscribe({
      next: (data) => {
        this.users.set(data.results);
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => this.fs.loading.set(false),
    });
  }

  viewUserInfo(id: number): void {
    const user = this.users().find((u) => u.id === id);
    if (!user) return;
    this.dialog.open(UserInfoDialogComponent, {
      data: user,
      disableClose: false,
      hasBackdrop: true,
      width: 'min(540px, 94vw)',
      maxHeight: '90vh',
    });
  }

  editUser(id: number): void {
    this.router.navigate(['/users', id, 'edit']);
  }

  assignPermissions(id: number): void {
    this.router.navigate(['/users', id, 'permissions']);
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
      this.api.patch(`/users/${id}/`, { password }).subscribe({
        next: () => this.toast.success(this.translation.t('users.reset-password-success')),
        error: () => this.toast.error(this.translation.t('users.reset-password-error')),
      });
    });
  }

  deleteUser(id: number): void {
    if (confirm(this.translation.t('users.confirm-delete'))) {
      this.api.delete(`/users/${id}/`).subscribe({
        next: () => {
          this.toast.success(this.translation.t('user-data.delete-success'));
          this.load();
        },
        error: () => this.toast.error(this.translation.t('user-data.delete-error')),
      });
    }
  }
}
