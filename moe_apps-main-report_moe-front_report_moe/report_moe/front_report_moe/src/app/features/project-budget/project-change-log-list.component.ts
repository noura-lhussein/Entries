import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit,
  computed,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { UntypedFormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import type { TableColumn } from '../../shared/components/data-table/data-table.component';
import type { FilterGroup } from '../../shared/components/filter-panel/filter-panel.component';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { FilterState } from '../../shared/utils/filter-state';
import {
  type BudgetSelectOption,
  type ProjectChangeAction,
  type ProjectChangeLogEntry,
} from './project-budget.models';
import { PROJECT_CHANGE_LOG_FIELD_OPTIONS } from './project-change-log-fields';
import { ProjectBudgetService } from './project-budget.service';

type ChangeLogRow = ProjectChangeLogEntry & {
  action_label: string;
  changed_at_label: string;
  project_display: string;
  user_display: string;
};

@Component({
  selector: 'app-project-change-log-list',
  standalone: true,
  imports: [CommonModule, ListPageComponent, ModalComponent, FormMapPickerComponent],
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
    />

    <app-modal
      [title]="t('budget.projects.change-log-location-dialog-title')"
      [visible]="deviceLocationModalOpen()"
      size="large"
      (close)="closeDeviceLocationDialog()"
    >
      <app-form-map-picker
        [form]="deviceLocationForm"
        [readOnly]="true"
        [showCoordinates]="false"
        [mapHeight]="420"
        [minMapHeight]="320"
        [label]="t('budget.projects.change-log-location')"
        [resetViewLabel]="t('budget.projects.map-reset-view')"
        [focusMarkerLabel]="t('budget.projects.map-focus-location')"
        [fullscreenLabel]="t('budget.projects.map-fullscreen')"
        [exitFullscreenLabel]="t('budget.projects.map-exit-fullscreen')"
        [emptyCoordinatesLabel]="t('budget.projects.map-no-coordinates')"
      />
      <div footer class="device-location-modal-footer">
        <button
          type="button"
          class="device-location-close-btn"
          (click)="closeDeviceLocationDialog()"
        >
          {{ t('common.close') }}
        </button>
      </div>
    </app-modal>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styles: [
    `
      .device-location-modal-footer {
        display: flex;
        justify-content: flex-end;
        padding-top: 8px;
      }
      .device-location-close-btn {
        padding: 8px 16px;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        background: #fff;
        color: #374151;
        font-size: 0.88rem;
        cursor: pointer;
        font-family: inherit;
      }
      .device-location-close-btn:hover {
        background: #f9fafb;
      }
    `,
  ],
})
export class ProjectChangeLogListComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private fb = inject(UntypedFormBuilder);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), 'search');

  rows = signal<ChangeLogRow[]>([]);
  projects = signal<BudgetSelectOption[]>([]);
  users = signal<BudgetSelectOption[]>([]);
  deviceLocationModalOpen = signal(false);

  deviceLocationForm = this.fb.group({
    latitude: [''],
    longitude: [''],
  });

  filterGroups = computed<FilterGroup[]>(() => [
    {
      label: this.t('budget.change-log.filter-project'),
      key: 'project',
      type: 'select',
      options: this.projects().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('budget.change-log.filter-action'),
      key: 'action',
      type: 'select',
      options: [
        { value: 'create', label: this.t('budget.projects.change-log-action-create') },
        { value: 'update', label: this.t('budget.projects.change-log-action-update') },
        { value: 'delete', label: this.t('budget.projects.change-log-action-delete') },
      ],
    },
    {
      label: this.t('budget.change-log.filter-field'),
      key: 'field_name',
      type: 'select',
      options: PROJECT_CHANGE_LOG_FIELD_OPTIONS.map((item) => ({
        value: item.value,
        label: item.label,
      })),
    },
    {
      label: this.t('budget.change-log.filter-user'),
      key: 'changed_by',
      type: 'select',
      options: this.users().map((item) => ({
        value: String(item.id),
        label: item.name || String(item.id),
      })),
    },
    {
      label: this.t('budget.change-log.filter-from-date'),
      key: 'changed_after',
      type: 'date',
    },
    {
      label: this.t('budget.change-log.filter-to-date'),
      key: 'changed_before',
      type: 'date',
    },
  ]);

  columns = computed<TableColumn[]>(() => [
    {
      key: 'changed_at_label',
      label: this.t('budget.projects.change-log-datetime'),
      sortable: false,
      minWidth: '140px',
    },
    {
      key: 'project_display',
      label: this.t('budget.change-log.filter-project'),
      type: 'stacked',
      subtitleKey: 'project_code',
      minWidth: '180px',
    },
    { key: 'action_label', label: this.t('budget.change-log.filter-action'), minWidth: '90px' },
    { key: 'field_label', label: this.t('budget.projects.change-log-field'), minWidth: '140px' },
    {
      key: 'old_value',
      label: this.t('budget.projects.change-log-before'),
      minWidth: '120px',
    },
    {
      key: 'new_value',
      label: this.t('budget.projects.change-log-after'),
      minWidth: '120px',
    },
    {
      key: 'user_display',
      label: this.t('budget.projects.change-log-user'),
      minWidth: '120px',
    },
  ]);

  actions = computed(() => [
    {
      icon: 'visibility',
      label: this.t('budget.projects.view'),
      action: (id: number) => this.viewProject(id),
    },
    {
      icon: 'location_on',
      label: this.t('budget.projects.change-log-show-location'),
      action: (id: number) => this.openDeviceLocation(id),
      show: (item: ChangeLogRow) => this.hasClientLocation(item),
    },
  ]);

  pageConfig = computed(() => ({
    title: this.t('budget.change-log.title'),
    description: this.t('budget.change-log.page-description'),
    searchPlaceholder: this.t('budget.change-log.search'),
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
    emptyMessage: this.t('budget.change-log.empty'),
    tableScroll: { vertical: 'auto' as const },
  }));

  ngOnInit(): void {
    this.loadDependencies();
    this.load();
  }

  clearFilter(key: string): void {
    this.fs.onFilterChange({ key, value: '' });
  }

  viewProject(changeLogId: number): void {
    const row = this.rows().find((item) => item.id === changeLogId);
    if (!row?.project_id) return;
    this.router.navigate(['/budget/projects', row.project_id, 'view']);
  }

  openDeviceLocation(changeLogId: number): void {
    const row = this.rows().find((item) => item.id === changeLogId);
    if (!row || !this.hasClientLocation(row)) return;
    this.deviceLocationForm.patchValue({
      latitude: row.client_latitude,
      longitude: row.client_longitude,
    });
    this.deviceLocationModalOpen.set(true);
  }

  closeDeviceLocationDialog(): void {
    this.deviceLocationModalOpen.set(false);
  }

  hasClientLocation(row: ChangeLogRow): boolean {
    const lat =
      row.client_latitude != null && row.client_latitude !== '' ? Number(row.client_latitude) : NaN;
    const lng =
      row.client_longitude != null && row.client_longitude !== ''
        ? Number(row.client_longitude)
        : NaN;
    return Number.isFinite(lat) && Number.isFinite(lng);
  }

  load(): void {
    this.fs.loading.set(true);
    this.budget.listProjectChangeLogs(this.fs.params).subscribe({
      next: (data) => {
        this.rows.set(
          data.results.map((row) => ({
            ...row,
            action_label: this.actionLabel(row.action),
            changed_at_label: this.formatDateTime(row.changed_at),
            project_display: row.project_name || row.project_code || String(row.project_id),
            user_display:
              row.changed_by_name ||
              row.changed_by_username ||
              this.t('budget.projects.value-empty'),
          })),
        );
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.change-log.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  private loadDependencies(): void {
    this.budget.listProjects({ page_size: 500 }).subscribe({
      next: (data) =>
        this.projects.set(
          data.results.map((item) => ({
            id: item.id,
            name: [item.code, item.name_ar].filter(Boolean).join(' — ') || String(item.id),
          })),
        ),
    });
    this.budget.listBudgetUsers({ page_size: 500 }).subscribe({
      next: (data) =>
        this.users.set(
          data.results.map((item) => ({
            id: item.id,
            name: item.full_name || item.username || String(item.id),
          })),
        ),
    });
  }

  private actionLabel(action: ProjectChangeAction): string {
    if (action === 'create') return this.t('budget.projects.change-log-action-create');
    if (action === 'delete') return this.t('budget.projects.change-log-action-delete');
    return this.t('budget.projects.change-log-action-update');
  }

  private formatDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  }
}
