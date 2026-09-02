import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { ToastService } from '../../shared/services/toast.service';
import { DialogService } from '../../shared/services/dialog.service';
import { TranslationService } from '../../shared/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import {
  BuilderService,
  MainSection,
  SubMainSection,
  Title,
  TitleCategory,
} from '../../core/services/builder.service';
import { parseFilterIds, serializeFilterIds } from '../../shared/utils/filter-params';
import {
  applyTitleCategoryFilterChange,
  titlesForCategory,
} from '../admin-report/admin-report-filters.util';
import { Paginated, User } from '../../core/models';
import { type InfoRow, type PaginatedInfoRows } from '../../core/models/info-row';
import {
  INFO_STATUS_ACCEPT,
  INFO_STATUS_REJECT,
  isInfoAccepted,
  normalizeInfoConfirmStatus,
} from '../../core/models/info-confirm-status';
import { TableColumn, TableAction, TableRow } from '../../shared/components/table/table.component';
import { TitleGroupedTablesComponent } from '../../shared/components/title-grouped-tables/title-grouped-tables.component';
import type { TitleGroupedBlock } from '../../shared/models/title-grouped-table.model';
import { groupInfoRowsByTitle } from '../../shared/utils/group-info-rows-by-title';
import { FilterPanelComponent } from '../../shared/components/filter-panel/filter-panel.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { FilterState } from '../../shared/utils/filter-state';
import { DATA_TABLE_PAGE_SIZE } from '../../shared/utils/data-table-page-size';
import {
  UserDataRowEditDialogComponent,
  type UserDataRowEditDialogData,
} from './user-data-row-edit-dialog.component';

interface TitleAccordionItem {
  titleId: number;
  titleName: string;
  titleOrder: number;
  rowCount: number | null;
  categoryName: string;
}

@Component({
  selector: 'app-user-data',
  standalone: true,
  styleUrl: './user-data.component.scss',
  imports: [
    CommonModule,
    MatIconModule,
    TitleGroupedTablesComponent,
    FilterPanelComponent,
    PageHeaderComponent,
  ],
  template: `
    <div class="page-shell">
      <div class="page-chrome">
        <app-page-header
          [title]="translation.t('user-data.title')"
          [description]="translation.t('user-data.description')"
        ></app-page-header>

        <div *ngIf="!canWrite()" class="no-permission-banner">
          <span class="material-icons">lock</span>
          <span>ليس لديك صلاحية إدخال بيانات. تواصل مع المدير لمنح الصلاحية.</span>
        </div>

        <app-filter-panel
          [filterGroups]="filterGroups()"
          [activeFilters]="fs.filters()"
          [searchPlaceholder]="translation.t('user-data.search-placeholder')"
          (search)="onSearch($event)"
          (filterChange)="onFilterChange($event)"
          (clearFilter)="onClearFilter($event)"
          (clearFilters)="onClearFilters()"
        ></app-filter-panel>
      </div>

      <div class="page-panel">
        <div class="page-body">
          @if (titlesLoading()) {
            <p class="titles-status">{{ translation.t('user-data.titles-loading') }}</p>
          } @else if (titleItems().length === 0) {
            <p class="titles-status">{{ translation.t('user-data.empty-message') }}</p>
          } @else {
            <div class="title-accordion">
              @for (item of titleItems(); track item.titleId) {
                <section
                  class="title-acc"
                  [class.is-open]="expandedTitleId() === item.titleId"
                >
                  <button
                    type="button"
                    class="title-acc__header"
                    (click)="toggleTitle(item.titleId)"
                    [attr.aria-expanded]="expandedTitleId() === item.titleId"
                  >
                    <mat-icon class="title-acc__chevron">
                      {{ expandedTitleId() === item.titleId ? 'expand_more' : 'chevron_left' }}
                    </mat-icon>
                    <span class="title-acc__name">{{ item.titleName }}</span>
                    @if (item.categoryName) {
                      <span class="title-acc__category">{{ item.categoryName }}</span>
                    }
                    <span class="title-acc__count" [class.is-loading]="item.rowCount == null">
                      @if (item.rowCount == null) {
                        …
                      } @else {
                        {{ item.rowCount }}
                        {{ translation.t('user-data.records-count-label') }}
                      }
                    </span>
                  </button>

                  @if (expandedTitleId() === item.titleId) {
                    <div class="title-acc__body">
                      @if (expandedLoading() && expandedGroups().length === 0) {
                        <p class="titles-status">{{ translation.t('user-data.rows-loading') }}</p>
                      } @else {
                        <app-title-grouped-tables
                          [groups]="expandedGroups()"
                          [actions]="actions()"
                          [emptyMessage]="translation.t('user-data.empty-message')"
                          [hasMore]="fs.hasMore()"
                          [loadingMore]="fs.loadingMore()"
                          [hideTitleHeaders]="true"
                          scrollRoot=".page-body"
                          (actionClicked)="onTableAction($event)"
                          (loadMore)="fs.loadMore()"
                        />
                      }
                    </div>
                  }
                </section>
              }
            </div>
          }
        </div>
      </div>
    </div>
  `,
})
export class UserDataComponent implements OnInit {
  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private toast = inject(ToastService);
  private dialog = inject(DialogService);
  private matDialog = inject(MatDialog);
  private auth = inject(AuthService);
  translation = inject(TranslationService);

  canWrite = computed(() => {
    const u = this.auth.currentUser();
    return u ? u.is_admin || u.can_write_info : false;
  });

  fs = new FilterState(() => this.loadExpandedRows(), 'search', DATA_TABLE_PAGE_SIZE);
  private accumulatedRows: InfoRow[] = [];

  titlesLoading = signal(true);
  expandedTitleId = signal<number | null>(null);
  expandedLoading = signal(false);
  expandedGroups = signal<TitleGroupedBlock[]>([]);

  mainSections = signal<MainSection[]>([]);
  subSections = signal<SubMainSection[]>([]);
  titles = signal<Title[]>([]);
  titleCategories = signal<TitleCategory[]>([]);
  users = signal<User[]>([]);
  attributes = signal<{ id: number; label: string }[]>([]);
  /** Logical data-row counts per title (`GET /infos/row-count/`). */
  private rowCountByTitle = signal<Map<number, number | null>>(new Map());

  private filteredTitles = computed((): Title[] => {
    const categoryFilter = parseFilterIds(this.fs.filters()['title_category_id']);
    const titleFilter = parseFilterIds(this.fs.filters()['title_id']);
    const q = this.fs.searchQuery().trim().toLowerCase();

    let list = titlesForCategory(this.titles(), categoryFilter);
    if (titleFilter.length) {
      const allow = new Set(titleFilter.map(String));
      list = list.filter((t) => allow.has(String(t.id)));
    }
    if (q) {
      list = list.filter((t) => t.name.toLowerCase().includes(q));
    }
    return list;
  });

  titleItems = computed((): TitleAccordionItem[] => {
    const counts = this.rowCountByTitle();
    return this.filteredTitles().map((t) => ({
      titleId: t.id,
      titleName: t.name,
      titleOrder: t.order,
      rowCount: counts.has(t.id) ? (counts.get(t.id) ?? null) : null,
      categoryName: t.category_name?.trim() || '',
    }));
  });

  private titlesForFilterOptions = computed(() =>
    titlesForCategory(
      this.titles(),
      parseFilterIds(this.fs.filters()['title_category_id']),
    ),
  );

  private statusColumn = (): TableColumn => ({
    key: 'confirmed',
    type: 'badge' as const,
    label: this.translation.t('user-data.status-label'),
    sortable: false,
    format: (v: string) => this.confirmStatusLabel(v),
    badgeMap: {
      accept: { bg: '#dcfce7', color: '#166534' },
      reject: { bg: '#fee2e2', color: '#991b1b' },
      waiting: { bg: '#fef3c7', color: '#92400e' },
    },
  });

  private buildFieldColumns = (fieldIds: string[]): TableColumn[] =>
    fieldIds.map((id) => ({
      key: `f_${id}`,
      label: this.attributeLabel(id),
      sortable: false,
      minWidth: '6.5rem',
      width: '8.5rem',
    }));

  actions = computed((): TableAction[] => [
    {
      type: 'edit',
      label: this.translation.t('user-data.edit-button'),
      icon: 'edit',
      color: 'edit',
      disabled: (row: TableRow) => isInfoAccepted(String(row['confirmed'])) || !this.canWrite(),
    },
    {
      type: 'delete',
      label: this.translation.t('user-data.delete-button'),
      icon: 'delete',
      color: 'delete',
      disabled: (row: TableRow) => isInfoAccepted(String(row['confirmed'])) || !this.canWrite(),
    },
  ]);

  filterGroups = computed(() => {
    const groups = [
      {
        label: this.translation.t('user-data.main-section-label'),
        key: 'main_section_id',
        type: 'select' as const,
        options: this.mainSections().map((m) => ({ value: String(m.id), label: m.name })),
      },
      {
        label: this.translation.t('user-data.sub-main-label'),
        key: 'sub_main_id',
        type: 'select' as const,
        options: this.subSections().map((s) => ({ value: String(s.id), label: s.name })),
      },
      {
        label: this.translation.t('user-data.title-category-label'),
        key: 'title_category_id',
        type: 'select' as const,
        options: this.titleCategories().map((c) => ({
          value: String(c.id),
          label: c.name,
        })),
      },
      {
        label: this.translation.t('user-data.title-label'),
        key: 'title_id',
        type: 'select' as const,
        options: this.titlesForFilterOptions().map((t) => ({
          value: String(t.id),
          label: t.name,
        })),
      },
      {
        label: this.translation.t('user-data.attribute-label'),
        key: 'attribute_id',
        type: 'select' as const,
        options: this.attributes().map((a) => ({ value: String(a.id), label: a.label })),
      },
      {
        label: this.translation.t('user-data.confirmation-state'),
        key: 'confirmed',
        type: 'select' as const,
        options: [
          { value: '', label: this.translation.t('user-data.confirmed-all') },
          { value: 'waiting', label: this.translation.t('user-data.confirmed-waiting') },
          { value: 'accept', label: this.translation.t('user-data.confirmed-true') },
          { value: 'reject', label: this.translation.t('user-data.confirmed-reject') },
        ],
      },
      {
        label: this.translation.t('reports.from-date'),
        key: 'from',
        type: 'date' as const,
      },
      {
        label: this.translation.t('reports.to-date'),
        key: 'to',
        type: 'date' as const,
      },
    ];
    if (this.auth.isAdmin()) {
      groups.splice(4, 0, {
        label: this.translation.t('info-report.entered-by'),
        key: 'user',
        type: 'select' as const,
        options: this.users().map((u) => ({
          value: String(u.id),
          label: u.full_name || u.username,
        })),
      });
    }
    return groups;
  });

  ngOnInit(): void {
    this.loadFilterOptions();
  }

  private loadFilterOptions(): void {
    this.titlesLoading.set(true);
    this.builder.getMainSections().subscribe({
      next: (data) => this.mainSections.set(data.results || []),
    });
    this.builder.getSubMainSections().subscribe({
      next: (data) => this.subSections.set(data.results || []),
    });
    this.builder.getTitles().subscribe({
      next: (data) => {
        this.titles.set(data.results || []);
        this.titlesLoading.set(false);
        this.refreshTitleRowCounts();
      },
      error: () => {
        this.titlesLoading.set(false);
        this.toast.error(this.translation.t('user-data.load-error'));
      },
    });
    this.builder.getTitleCategories().subscribe({
      next: (data) => this.titleCategories.set(data.results || []),
    });
    this.api.get<Paginated<User>>('/users/', { limit: 100 }).subscribe({
      next: (data) => this.users.set(data.results || []),
    });
    this.builder.getAllAttributes().subscribe({
      next: (data) => {
        this.attributes.set((data.results || []).map((a) => ({ id: a.id, label: a.label })));
      },
    });
  }

  toggleTitle(titleId: number): void {
    if (this.expandedTitleId() === titleId) {
      this.collapseExpanded();
      return;
    }
    this.expandedTitleId.set(titleId);
    this.fs.currentPage.set(1);
    this.fs.loadingMore.set(false);
    this.accumulatedRows = [];
    this.expandedGroups.set([]);
    this.loadExpandedRows();
  }

  private collapseExpanded(): void {
    this.expandedTitleId.set(null);
    this.accumulatedRows = [];
    this.expandedGroups.set([]);
    this.fs.currentPage.set(1);
    this.fs.loadingMore.set(false);
    this.fs.setTotal(0);
  }

  onSearch(query: string): void {
    this.fs.searchQuery.set(query);
    const openId = this.expandedTitleId();
    if (openId != null && !this.titleItems().some((t) => t.titleId === openId)) {
      this.collapseExpanded();
    } else if (openId != null) {
      this.fs.currentPage.set(1);
      this.fs.loadingMore.set(false);
      this.loadExpandedRows();
    }
    this.refreshTitleRowCounts();
  }

  private rowCountFilterParams(): Record<string, string | number | boolean> {
    const params: Record<string, string | number | boolean> = {};
    for (const [key, value] of Object.entries(this.fs.filters())) {
      if (value === '' || value == null) continue;
      params[key] = Array.isArray(value) ? serializeFilterIds(value.map(String)) : value;
    }
    const u = this.auth.currentUser();
    if (u && !u.is_admin && params['user'] == null) {
      params['user'] = u.id;
    }
    return params;
  }

  private refreshTitleRowCounts(): void {
    const ids = this.filteredTitles().map((t) => t.id);
    if (!ids.length) {
      this.rowCountByTitle.set(new Map());
      return;
    }

    const pending = new Map<number, number | null>();
    for (const id of ids) pending.set(id, null);
    this.rowCountByTitle.set(pending);

    const base = this.rowCountFilterParams();
    forkJoin(
      ids.map((titleId) =>
        this.api
          .get<{ count: number; title_id: number }>('/infos/row-count/', {
            ...base,
            title_id: titleId,
          })
          .pipe(
            map((res) => ({ titleId, count: res.count ?? 0 })),
            catchError(() => of({ titleId, count: 0 })),
          ),
      ),
    ).subscribe((rows) => {
      const next = new Map<number, number | null>();
      for (const row of rows) next.set(row.titleId, row.count);
      this.rowCountByTitle.set(next);
    });
  }

  loadExpandedRows(): void {
    const titleId = this.expandedTitleId();
    if (titleId == null) return;

    const append = this.fs.currentPage() > 1;
    if (append) {
      this.fs.loadingMore.set(true);
    } else {
      this.expandedLoading.set(true);
      this.accumulatedRows = [];
    }

    const params: Record<string, string | number | boolean> = {
      ...this.fs.params,
      title_id: titleId,
      page_size: this.fs.pageSize(),
    };
    const u = this.auth.currentUser();
    if (u && !u.is_admin && !this.fs.filters()['user']) {
      params['user'] = u.id;
    }

    this.api.get<PaginatedInfoRows>('/info-rows/', params).subscribe({
      next: (data) => {
        if (this.expandedTitleId() !== titleId) return;
        const batch = data.results || [];
        this.accumulatedRows = append ? [...this.accumulatedRows, ...batch] : batch;
        this.expandedGroups.set(
          groupInfoRowsByTitle({
            rows: this.accumulatedRows,
            mapRow: (r) => this.mapInfoRowToTableRow(r),
            buildFieldColumns: (ids) => this.buildFieldColumns(ids),
            resolveMainSectionName: (id) => this.mainSectionNameForSubMain(id),
            titleOrder: (id) => this.titleOrder(id),
            trailingColumns: [this.statusColumn()],
          }),
        );
        this.fs.setTotal(data.count);
        this.expandedLoading.set(false);
        this.fs.loading.set(false);
        this.fs.loadingMore.set(false);
      },
      error: (err) => {
        console.error(err);
        this.toast.error(this.translation.t('user-data.load-error'));
        if (append) {
          this.fs.currentPage.update((p) => Math.max(1, p - 1));
        }
        this.expandedLoading.set(false);
        this.fs.loading.set(false);
        this.fs.loadingMore.set(false);
      },
    });
  }

  onFilterChange(change: { key: string; value: unknown }): void {
    if (change.key === 'title_category_id') {
      const categoryIds = parseFilterIds(change.value);
      this.fs.filters.update((prev) => {
        const patch = applyTitleCategoryFilterChange(prev, categoryIds, this.titles());
        const next = { ...prev };
        if (patch.title_category_id) next['title_category_id'] = patch.title_category_id;
        else delete next['title_category_id'];
        if (patch.title_id) next['title_id'] = patch.title_id;
        else delete next['title_id'];
        return next;
      });
      this.afterTitleListFilterChange();
      return;
    }
    this.fs.filters.update((f) => {
      const next = { ...f };
      if (change.value === '' || change.value == null) delete next[change.key];
      else if (Array.isArray(change.value)) {
        const ids = parseFilterIds(change.value);
        if (ids.length) next[change.key] = serializeFilterIds(ids);
        else delete next[change.key];
      } else {
        next[change.key] = change.value as string | number | boolean;
      }
      return next;
    });
    this.afterTitleListFilterChange();
  }

  private afterTitleListFilterChange(): void {
    const openId = this.expandedTitleId();
    if (openId != null && !this.titleItems().some((t) => t.titleId === openId)) {
      this.collapseExpanded();
    } else if (openId != null) {
      this.fs.currentPage.set(1);
      this.fs.loadingMore.set(false);
      this.loadExpandedRows();
    }
    this.refreshTitleRowCounts();
  }

  onClearFilter(key: string): void {
    if (key === 'title_category_id') {
      this.onFilterChange({ key, value: '' });
      return;
    }
    this.fs.filters.update((f) => {
      const next = { ...f };
      delete next[key];
      return next;
    });
    this.afterTitleListFilterChange();
  }

  onClearFilters(): void {
    this.fs.filters.set({});
    this.fs.searchQuery.set('');
    this.collapseExpanded();
    this.refreshTitleRowCounts();
  }

  onTableAction(event: { type: string; row: TableRow; origin?: DOMRect }): void {
    if (isInfoAccepted(String(event.row['confirmed']))) {
      this.toast.error(this.translation.t('user-data.cannot-modify-approved'));
      return;
    }
    const infoIds = (event.row['_infoIds'] as number[]) || [];
    if (event.type === 'edit') {
      this.openEditRowDialog(event.row, infoIds, event.origin);
    } else if (event.type === 'delete') {
      this.deleteRow(infoIds);
    }
  }

  private mapInfoRowToTableRow(r: InfoRow): TableRow {
    const row: TableRow = {
      id: r.row_id,
      sub_main_name: r.sub_main_name ?? '—',
      title_name: r.title_name ?? '—',
      confirmed: r.confirmed,
      _infoIds: r.info_ids,
      _fields: r.fields || {},
    };
    for (const [attrId, val] of Object.entries(r.fields || {})) {
      row[`f_${attrId}`] = val;
    }
    return row;
  }

  private attributeLabel(attrId: string): string {
    const found = this.attributes().find((a) => String(a.id) === attrId);
    return found?.label ?? attrId;
  }

  private mainSectionNameForSubMain(subMainId: number | null): string {
    if (subMainId == null) return '—';
    const sub = this.subSections().find((s) => s.id === subMainId);
    if (!sub) return '—';
    const main = this.mainSections().find((m) => m.id === sub.main_section_id);
    return main?.name ?? '—';
  }

  private titleOrder(titleId: number | null): number {
    if (titleId == null) return 9999;
    const t = this.titles().find((x) => x.id === titleId);
    return t?.order ?? 9999;
  }

  private openEditRowDialog(row: TableRow, infoIds: number[], origin?: DOMRect): void {
    if (!infoIds.length) return;
    const rowId = String(row['id'] ?? '');
    const sourceRow = rowId
      ? (document.querySelector(`tr[data-row-id="${CSS.escape(rowId)}"]`) as HTMLElement | null)
      : null;
    sourceRow?.classList.add('user-data-row-expanding');

    const fields = (row['_fields'] as Record<string, string> | undefined) || {};
    const dialogData: UserDataRowEditDialogData = {
      infoIds,
      fieldColumns: Object.keys(fields)
        .sort((a, b) => this.attributeLabel(a).localeCompare(this.attributeLabel(b), 'ar'))
        .map((id) => ({
          id,
          label: this.attributeLabel(id),
          preview: String(fields[id] ?? '—'),
        })),
    };
    const ref = this.matDialog.open(UserDataRowEditDialogComponent, {
      width: '95vw',
      maxWidth: '95vw',
      minHeight: '62vh',
      maxHeight: '94vh',
      disableClose: false,
      hasBackdrop: true,
      backdropClass: ['export-dialog-backdrop', 'user-data-row-expand-backdrop'],
      panelClass: ['export-dialog-panel', 'user-data-row-expand-panel'],
      data: dialogData,
    });
    ref.afterOpened().subscribe(() => this.playRowExpandAnimation(origin));
    ref.afterClosed().subscribe((saved) => {
      sourceRow?.classList.remove('user-data-row-expanding');
      document
        .querySelector('.user-data-row-expand-panel')
        ?.classList.remove('user-data-row-expand-ready');
      if (saved) {
        this.fs.currentPage.set(1);
        this.loadExpandedRows();
        this.refreshTitleRowCounts();
      }
    });
  }

  private playRowExpandAnimation(origin?: DOMRect): void {
    const pane = document.querySelector('.user-data-row-expand-panel') as HTMLElement | null;
    const surface = pane?.querySelector('.mat-mdc-dialog-surface') as HTMLElement | null;
    if (!pane || !surface) return;

    if (origin) {
      const panel = surface.getBoundingClientRect();
      const cx = origin.left + origin.width / 2;
      const cy = origin.top + origin.height / 2;
      const ox = ((cx - panel.left) / Math.max(panel.width, 1)) * 100;
      const oy = ((cy - panel.top) / Math.max(panel.height, 1)) * 100;
      const scaleX = origin.width / Math.max(panel.width, 1);
      const scaleY = origin.height / Math.max(panel.height, 1);
      const fromScale = Math.min(Math.max(Math.min(scaleX, scaleY), 0.04), 0.28);
      surface.style.setProperty('--expand-origin-x', `${ox}%`);
      surface.style.setProperty('--expand-origin-y', `${oy}%`);
      surface.style.setProperty('--expand-from-scale', String(fromScale));
    }

    requestAnimationFrame(() => {
      requestAnimationFrame(() => pane.classList.add('user-data-row-expand-ready'));
    });
  }

  confirmStatusLabel(status: string): string {
    const s = normalizeInfoConfirmStatus(status);
    if (s === INFO_STATUS_ACCEPT) return this.translation.t('user-data.confirmed-true');
    if (s === INFO_STATUS_REJECT) return this.translation.t('user-data.confirmed-reject');
    return this.translation.t('user-data.confirmed-waiting');
  }

  async deleteRow(infoIds: number[]): Promise<void> {
    if (!infoIds.length) return;
    const confirmed = await this.dialog.confirm({
      title: this.translation.t('user-data.delete-confirm-title'),
      message: this.translation.t('user-data.delete-row-confirm-message'),
    });
    if (!confirmed) return;
    let done = 0;
    for (const id of infoIds) {
      this.api.delete(`/infos/${id}/`).subscribe({
        next: () => {
          done++;
          if (done === infoIds.length) {
            this.toast.success(this.translation.t('user-data.delete-success'));
            this.fs.currentPage.set(1);
            this.loadExpandedRows();
            this.refreshTitleRowCounts();
          }
        },
        error: () => this.toast.error(this.translation.t('user-data.delete-error')),
      });
    }
  }
}
