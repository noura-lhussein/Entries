import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { ReqReport, Paginated } from '../../core/models';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import { FilterState } from '../../shared/utils/filter-state';

@Component({
  selector: 'app-reports-list',
  standalone: true,
  imports: [ListPageComponent],
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
export class ReportsListComponent implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);
  translation = inject(TranslationService);

  // no full-text search on reports endpoint
  fs = new FilterState(() => this.load(), '');

  reports = signal<ReqReport[]>([]);

  filterGroups = computed(() => [
    {
      label: this.translation.t('reports.report-type'),
      key: 'type',
      type: 'select' as const,
      options: [
        { value: 'monthly', label: this.translation.t('reports.monthly') },
        { value: 'quarterly', label: this.translation.t('reports.quarterly') },
        { value: 'annual', label: this.translation.t('reports.annual') },
      ],
    },
    { label: this.translation.t('reports.from-date'), key: 'from', type: 'date' as const },
    { label: this.translation.t('reports.to-date'), key: 'to', type: 'date' as const },
  ]);

  columns = computed(() => [
    { key: 'sub_main_name', label: this.translation.t('reports.section'), sortable: true },
    { key: 'report_titles', label: this.translation.t('reports.requirements'), sortable: true },
    { key: 'date_from', label: this.translation.t('reports.date'), sortable: true },
  ]);

  actions = computed(() => [
    {
      type: 'view',
      icon: 'visibility',
      label: this.translation.t('reports.view'),
      color: 'view' as const,
      action: (id: number) => this.viewReport(id),
    },
    {
      type: 'delete',
      icon: 'delete',
      label: this.translation.t('sidebar.delete'),
      color: 'delete' as const,
      action: (id: number) => this.deleteReport(id),
    },
  ]);

  pageConfig = computed(() => ({
    title: this.translation.t('reports.title'),
    description: this.translation.t('reports.description'),
    searchPlaceholder: this.translation.t('reports.search-placeholder'),
    filterGroups: this.filterGroups(),
    activeFilters: this.fs.filters(),
    columns: this.columns(),
    data: this.reports(),
    actions: this.actions(),
    loading: this.fs.loading(),
    currentPage: this.fs.currentPage(),
    totalPages: this.fs.totalPages(),
    totalItems: this.fs.totalCount(),
    pageSize: this.fs.pageSize(),
    emptyMessage: this.translation.t('reports.no-reports'),
  }));

  clearFilter(key: string): void {
    this.fs.onFilterChange({ key, value: '' });
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.fs.loading.set(true);
    this.api.get<Paginated<ReqReport>>('/reports/', this.fs.params).subscribe({
      next: (data) => {
        this.reports.set(data.results);
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => this.fs.loading.set(false),
    });
  }

  viewReport(_id: number): void {
    this.toast.info(this.translation.t('reports.view'));
  }

  deleteReport(id: number): void {
    if (confirm(this.translation.t('reports.confirm-delete'))) {
      this.api.delete(`/reports/${id}/`).subscribe({
        next: () => {
          this.toast.success(this.translation.t('user-data.delete-success'));
          this.load();
        },
        error: () => this.toast.error(this.translation.t('user-data.delete-error')),
      });
    }
  }
}
