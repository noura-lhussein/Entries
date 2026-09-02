import { Component, OnInit, inject, signal, computed, DestroyRef, Input } from '@angular/core';
import { ADMIN_REPORT_PAGE_META, type AdminReportPageMode } from './admin-report-page-mode';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { catchError, filter, map, startWith } from 'rxjs';
import { ApiService, type ApiParams } from '../../core/services/api.service';
import {
  BuilderService,
  MainSection,
  SubMainSection,
  Title,
  TitleCategory,
  City,
  District,
} from '../../core/services/builder.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { Attribute, Paginated } from '../../core/models';
import type { InfoRow, PaginatedInfoRows } from '../../core/models/info-row';
import { mapInfoRowsToAdminRows } from './admin-report-row-mapper';
import { TranslationService } from '../../shared/services/translation.service';
import {
  PageHeaderComponent,
  type PageHeaderAction,
} from '../../shared/components/page-header/page-header.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { FormSelectComponent } from '../../shared/components/form-select/form-select.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';
import {
  FilterPanelComponent,
  type FilterGroup,
} from '../../shared/components/filter-panel/filter-panel.component';
import { AdminReportTitleBlockComponent } from './admin-report-title-block.component';
import {
  type AdminReportRow,
  type AdminReportRowDraft,
  type BulkConfirmResponse,
  type BulkRejectResponse,
  type InfoRecord,
  type SubSectionBlock,
  type TitleTable,
  MAX_SUB_SECTIONS_LOAD,
  confirmStatusFromRow,
  withAdminReportColumnSizing,
} from './admin-report.models';
import { parseFilterIds, serializeFilterIds } from '../../shared/utils/filter-params';
import { captureScrollPosition } from '../../shared/utils/scroll-preserve.util';
import { bulkToastRowCount } from '../../core/utils/bulk-row-count';
import { ExportReportsDownloadService } from './export-reports-download.service';
import type { ExportDownloadContext } from './export-reports-download.types';
import { regroupSubSectionBlocksByTitle, type AdminTitleGroup } from './regroup-by-title.util';
import {
  applyTitleCategoryFilterChange,
  filterTitleTablesByScope,
  hasTitleScope as hasTitleScopeFromFilters,
  isCategoryScopedView as isCategoryScopedViewFromFilters,
  titlesForCategory,
} from './admin-report-filters.util';
import {
  buildInfoQueryParams,
  overviewBulkParams,
  titleScopedQueryOpts,
} from './admin-report-query.util';

@Component({
  selector: 'app-admin-report',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    FormsModule,
    PageHeaderComponent,
    AdminReportTitleBlockComponent,
    FilterPanelComponent,
    ModalComponent,
    ButtonComponent,
    FormSelectComponent,
    FormInputComponent,
    EmptyStateComponent,
  ],
  templateUrl: './admin-report.component.html',
  styleUrl: './admin-report.component.scss',
})
export class AdminReportComponent implements OnInit {
  /** Set by thin route wrappers (`export`, `overview`); default `admin` uses route data. */
  @Input() pageMode: AdminReportPageMode = 'admin';

  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);
  /** Present only on /export-reports (provided by ExportReportsPageComponent). */
  private exportDownload = inject(ExportReportsDownloadService, { optional: true });

  private urlSignal = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map(() => this.router.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  t = (key: string) => this.translation.t(key);

  private pageTitleKey = signal<string | null>(null);
  private pageDescriptionKey = signal<string | null>(null);
  exportMode = signal(false);

  isExportReports = computed(() => this.exportMode());

  headerTitle = computed(() => {
    const k = this.pageTitleKey();
    return k ? this.t(k) : this.t('admin-report.title');
  });

  headerDescription = computed(() => {
    const k = this.pageDescriptionKey();
    return k ? this.t(k) : '';
  });

  /** Header actions: show-all on the opposite side of the title, plus context actions. */
  pageHeaderActions = computed((): PageHeaderAction[] => {
    const showAllAction: PageHeaderAction = {
      label: this.showAll() ? this.t('admin-report.show-one') : this.t('admin-report.show-all'),
      icon: this.showAll() ? 'view_list' : 'grid_view',
      variant: 'ghost',
      click: () => this.toggleShowAll(),
    };

    if (this.isExportReports() && this.exportDownload) {
      const download = this.exportDownload;
      return [
        showAllAction,
        {
          label: this.t('export-reports.full-report'),
          icon: 'article',
          variant: 'primary',
          click: () => download.prompt(this.buildExportDownloadContext(), true),
        },
        {
          label: this.t('export-reports.download'),
          icon: 'download',
          variant: 'secondary',
          click: () => download.prompt(this.buildExportDownloadContext(), false),
        },
      ];
    }

    const actions: PageHeaderAction[] = [showAllAction];
    if (this.isInfosOverview() && this.canConfirm() && !this.showAll() && this.selectedSubId()) {
      actions.push(
        {
          label: this.t('info-report.bulk-reject'),
          icon: 'cancel',
          variant: 'danger',
          iconOnly: true,
          click: () => this.overviewBulkReject(),
        },
        {
          label: this.t('info-report.bulk-confirm'),
          icon: 'check_circle',
          variant: 'success',
          iconOnly: true,
          click: () => this.overviewBulkConfirm(),
        },
      );
    }
    return actions;
  });

  canConfirm = computed(() => {
    if (this.isExportReports()) return false;
    const u = this.auth.currentUser();
    return u ? u.is_admin || u.can_confirm_info : false;
  });

  cities = signal<City[]>([]);
  districts = signal<District[]>([]);

  mainSections = signal<MainSection[]>([]);
  /** Sub-sections for the currently selected main section (lazy-loaded). */
  subSectionsForMain = signal<SubMainSection[]>([]);
  titles = signal<Title[]>([]);
  titleCategories = signal<TitleCategory[]>([]);
  userOptions = signal<Array<{ value: string; label: string }>>([]);
  allAttributes = signal<Attribute[]>([]);
  selectedMainId = signal<number | null>(null);
  selectedSubId = signal<number | null>(null);
  selectedTitleId = signal<number | null>(null);
  selectedUserId = signal<number | null>(null);
  selectedDate = signal<string | null>(null);
  singleViewTitleTables = signal<TitleTable[]>([]);
  showAll = signal(false);
  subSectionBlocks = signal<SubSectionBlock[]>([]);
  activeFilters = signal<Record<string, string>>({});

  confirmNoteModalVisible = signal(false);
  confirmNoteDraft = signal('');
  noteModalKind = signal<'confirm' | 'commit'>('confirm');
  private pendingNoteAction: ((draft: string) => void) | null = null;

  /** Sub-sections in the filter dropdown (empty until a main section is selected). */
  private subSectionsForFilterOptions = computed(() => {
    if (!this.resolvedMainSectionIds().length) return [];
    return this.subSectionsForMain();
  });

  /** Titles available in the title filter (optionally narrowed by category). */
  private titlesForFilterOptions = computed(() =>
    titlesForCategory(
      this.titles(),
      parseFilterIds(this.activeFilters()['title_category_id']),
    ),
  );

  /** Sub-sections to load in tables (respects multi sub-section filter). */
  filteredSubSections = computed(() => {
    const subIds = parseFilterIds(this.activeFilters()['sub_main_id']);
    let all = this.subSectionsForFilterOptions();
    if (subIds.length) {
      all = all.filter((s) => subIds.includes(String(s.id)));
    }
    return all;
  });

  filteredDistricts = computed(() => {
    const cityIds = parseFilterIds(this.activeFilters()['city_id']);
    if (!cityIds.length) return this.districts();
    return this.districts().filter((d) => cityIds.includes(String(d.city)));
  });

  private resolvedMainSectionIds(): string[] {
    const mainIds = [...parseFilterIds(this.activeFilters()['main_section_id'])];
    const toolbarMain = this.selectedMainId();
    if (!mainIds.length && toolbarMain != null) mainIds.push(String(toolbarMain));
    return mainIds;
  }

  private filterValueUnchanged(key: string, value: unknown): boolean {
    if (
      key === 'archive_status' ||
      key === 'entry_date' ||
      key === 'from' ||
      key === 'to'
    ) {
      return String(this.activeFilters()[key] || '').trim() === String(value || '').trim();
    }
    const prev = serializeFilterIds(parseFilterIds(this.activeFilters()[key]))
      .split(',')
      .sort()
      .join(',');
    const next = serializeFilterIds(parseFilterIds(value)).split(',').sort().join(',');
    return prev === next;
  }

  isInfosOverview = computed(() => this.urlSignal().includes('/infos-overview'));

  /** True when title category and/or title filter is set. */
  hasTitleScope = computed(() => hasTitleScopeFromFilters(this.activeFilters()));

  /** View titles by category/title filter without selecting a sub-section. */
  isCategoryScopedView = computed(() =>
    isCategoryScopedViewFromFilters(
      this.activeFilters(),
      this.selectedSubId(),
      this.showAll(),
    ),
  );

  showSelectPrompt = computed(
    () => !this.selectedSubId() && !this.showAll() && !this.isCategoryScopedView(),
  );

  showSingleEmpty = computed(
    () =>
      !this.showAll() &&
      (this.selectedSubId() != null || this.isCategoryScopedView()) &&
      this.singleViewTitleTables().length === 0,
  );

  showSingleTitleTables = computed(
    () =>
      !this.showAll() &&
      (this.selectedSubId() != null || this.isCategoryScopedView()) &&
      this.singleViewTitleTables().length > 0,
  );

  mainSectionOptions = computed(() =>
    this.mainSections().map((m) => ({ value: m.id, label: m.name })),
  );

  mainSectionToolbarLabel = computed(() => {
    const id = this.selectedMainId();
    if (id == null) return this.t('admin-report.main-section');
    const name = this.mainSections().find((m) => m.id === id)?.name ?? '';
    return `${this.t('admin-report.main-section')}: ${name}`;
  });

  noteModalPlaceholder = computed(() =>
    this.noteModalKind() === 'commit'
      ? this.t('admin-report.commit-note-placeholder')
      : this.t('admin-report.confirm-note-placeholder'),
  );

  filterGroups = computed<FilterGroup[]>(() => {
    const mainGroup: FilterGroup = {
      label: this.t('admin-report.main-section'),
      key: 'main_section_id',
      type: 'select',
      options: this.mainSections().map((m) => ({ value: String(m.id), label: m.name })),
    };
    const rest: FilterGroup[] = [
      {
        label: this.t('admin-report.sub-section'),
        key: 'sub_main_id',
        type: 'select',
        options: this.subSectionsForFilterOptions().map((s) => ({
          value: String(s.id),
          label: s.name,
        })),
      },
      {
        label: this.t('admin-report.title-category-filter'),
        key: 'title_category_id',
        type: 'select',
        options: this.titleCategories().map((c) => ({
          value: String(c.id),
          label: c.name,
        })),
      },
      {
        label: this.t('admin-report.title-filter'),
        key: 'title_id',
        type: 'select',
        options: this.titlesForFilterOptions().map((tItem) => ({
          value: String(tItem.id),
          label: tItem.name,
        })),
      },
      {
        label: this.t('admin-report.archive-status'),
        key: 'archive_status',
        type: 'select',
        options: [
          { value: 'active', label: this.t('admin-report.archive-active') },
          { value: 'include', label: this.t('admin-report.archive-include') },
          { value: 'archived_only', label: this.t('admin-report.archive-only') },
        ],
      },
      {
        label: this.t('admin-report.user-entry-filter'),
        key: 'user',
        type: 'select',
        options: this.userOptions(),
      },
    ];

    if (this.isExportReports()) {
      rest.push(
        {
          label: this.t('builder.city'),
          key: 'city_id',
          type: 'select',
          options: this.cities().map((c) => ({ value: String(c.id), label: c.name })),
        },
        {
          label: this.t('builder.district'),
          key: 'district_id',
          type: 'select',
          options: this.filteredDistricts().map((d) => ({ value: String(d.id), label: d.name })),
        },
        {
          label: this.t('reports.from-date'),
          key: 'from',
          type: 'date',
        },
        {
          label: this.t('reports.to-date'),
          key: 'to',
          type: 'date',
        },
      );
    } else {
      rest.push({
        label: this.t('admin-report.date-filter'),
        key: 'entry_date',
        type: 'date',
      });
    }

    if (this.isInfosOverview()) return rest;
    return [mainGroup, ...rest];
  });

  displayedSubSectionBlocks = computed<SubSectionBlock[]>(() => {
    const allowedSubIds = new Set(this.filteredSubSections().map((s) => String(s.id)));
    const blocks = this.subSectionBlocks().filter((b) =>
      allowedSubIds.has(String(b.subSection.id)),
    );
    const af = this.activeFilters();
    const titles = this.titles();
    return blocks.map((b) => ({
      ...b,
      titleTables: filterTitleTablesByScope(b.titleTables, af, titles),
    }));
  });

  /** Show-all: group by title, then main/sub section (unified table layout). */
  displayedTitleGroups = computed<AdminTitleGroup[]>(() =>
    regroupSubSectionBlocksByTitle(
      this.displayedSubSectionBlocks(),
      (subMainId) => this.mainSectionNameForSubMain(subMainId),
      (titleId) => this.titleOrderFor(titleId),
    ),
  );

  ngOnInit(): void {
    this.syncRoutePageMeta();
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => this.syncRoutePageMeta());

    forkJoin({
      mainSections: this.builder.getMainSections(),
      titles: this.builder.getTitles(),
      titleCategories: this.builder.getTitleCategories(),
      attributes: this.builder.getAllAttributes(),
    }).subscribe({
      next: ({ mainSections, titles, titleCategories, attributes }) => {
        this.mainSections.set(mainSections.results || []);
        this.titles.set(titles.results || []);
        this.titleCategories.set(titleCategories.results || []);
        this.allAttributes.set((attributes.results || []) as unknown as Attribute[]);
      },
    });
  }

  private loadSubSectionsForCurrentMain(): void {
    const mainIds = this.resolvedMainSectionIds();
    if (!mainIds.length) {
      this.subSectionsForMain.set([]);
      return;
    }
    const mainId = Number(mainIds[0]);
    if (Number.isNaN(mainId)) {
      this.subSectionsForMain.set([]);
      return;
    }
    this.builder.getSubMainSections(mainId).subscribe({
      next: (res) => this.subSectionsForMain.set(res.results || []),
      error: () => this.subSectionsForMain.set([]),
    });
  }

  onFilterPanelOpened(): void {
    this.loadUserOptionsForFilterIfNeeded();
  }

  private syncRoutePageMeta(): void {
    if (this.pageMode !== 'admin') {
      const meta = ADMIN_REPORT_PAGE_META[this.pageMode];
      this.pageTitleKey.set(meta.pageTitleKey);
      this.pageDescriptionKey.set(meta.pageDescriptionKey);
      this.exportMode.set(meta.exportMode);
      if (meta.exportMode && !this.cities().length) {
        this.loadExportLocationFilters();
      }
      return;
    }

    let r: ActivatedRoute | null = this.route;
    while (r?.firstChild) {
      r = r.firstChild;
    }
    const data = (r?.snapshot.data ?? {}) as {
      pageTitleKey?: string;
      pageDescriptionKey?: string;
      exportMode?: boolean;
    };
    this.pageTitleKey.set(data['pageTitleKey'] ?? null);
    this.pageDescriptionKey.set(data['pageDescriptionKey'] ?? null);
    const exportMode = !!data['exportMode'];
    this.exportMode.set(exportMode);
    if (exportMode && !this.cities().length) {
      this.loadExportLocationFilters();
    }
  }

  private loadExportLocationFilters(cityId?: number): void {
    this.builder.getCities().subscribe({
      next: (res) => this.cities.set(res.results || []),
    });
    this.builder.getDistricts(cityId).subscribe({
      next: (res) => this.districts.set(res.results || []),
    });
  }

  private setMainSection(id: number | null): void {
    this.selectedMainId.set(id || null);
    this.selectedSubId.set(null);
    this.selectedUserId.set(null);
    this.singleViewTitleTables.set([]);
    this.subSectionBlocks.set([]);
    this.activeFilters.update((prev) => ({
      ...prev,
      main_section_id: id ? String(id) : '',
      sub_main_id: '',
      user: '',
    }));
    this.userOptions.set([]);
    this.loadSubSectionsForCurrentMain();
    if (this.showAll()) this.prepareShowAllShells();
  }

  private setSubSection(id: number | null): void {
    this.selectedSubId.set(id || null);
    this.activeFilters.update((prev) => ({
      ...prev,
      sub_main_id: id ? String(id) : '',
    }));
    if (!id) {
      this.singleViewTitleTables.set([]);
    } else {
      this.prepareSingleView();
    }
  }

  private setTitle(id: number | null): void {
    this.selectedTitleId.set(id || null);
    this.activeFilters.update((prev) => ({
      ...prev,
      title_id: id ? String(id) : '',
    }));
    this.reloadExpandedTitles();
  }

  private setUser(id: number | null): void {
    this.selectedUserId.set(id || null);
    this.activeFilters.update((prev) => ({
      ...prev,
      user: id ? String(id) : '',
    }));
    this.reloadExpandedTitles();
  }

  private setDate(value: string | null): void {
    this.selectedDate.set(value || null);
    this.activeFilters.update((prev) => ({
      ...prev,
      entry_date: value || '',
    }));
    this.reloadExpandedTitles();
    this.refreshTitleFieldCounts();
  }

  onFilterChange(change: { key: string; value: unknown }): void {
    if (this.filterValueUnchanged(change.key, change.value)) return;

    if (change.key === 'main_section_id') {
      const ids = parseFilterIds(change.value);
      this.activeFilters.update((prev) => ({
        ...prev,
        main_section_id: ids.length ? serializeFilterIds(ids) : '',
        sub_main_id: '',
        user: '',
      }));
      this.selectedMainId.set(ids.length === 1 ? Number(ids[0]) : null);
      this.selectedSubId.set(null);
      this.selectedUserId.set(null);
      this.singleViewTitleTables.set([]);
      this.subSectionBlocks.set([]);
      this.userOptions.set([]);
      this.loadSubSectionsForCurrentMain();
      if (this.showAll() && this.canLoadAllSubSections()) this.prepareShowAllShells();
      return;
    }
    if (change.key === 'sub_main_id') {
      const ids = parseFilterIds(change.value);
      this.activeFilters.update((prev) => ({
        ...prev,
        sub_main_id: ids.length ? serializeFilterIds(ids) : '',
      }));
      this.selectedSubId.set(ids.length === 1 ? Number(ids[0]) : null);
      if (!ids.length) {
        this.singleViewTitleTables.set([]);
      } else {
        this.prepareSingleView();
      }
      return;
    }
    if (change.key === 'title_category_id') {
      const ids = parseFilterIds(change.value);
      this.activeFilters.update((prev) => ({
        ...prev,
        ...applyTitleCategoryFilterChange(prev, ids, this.titles()),
      }));
      const keptTitleIds = parseFilterIds(this.activeFilters()['title_id']);
      this.selectedTitleId.set(
        keptTitleIds.length === 1 ? Number(keptTitleIds[0]) : null,
      );
      if (this.showAll()) {
        this.prepareShowAllShells();
      } else {
        this.prepareSingleView();
      }
      return;
    }
    if (change.key === 'title_id') {
      const ids = parseFilterIds(change.value);
      this.selectedTitleId.set(ids.length === 1 ? Number(ids[0]) : null);
      this.activeFilters.update((prev) => ({
        ...prev,
        title_id: ids.length ? serializeFilterIds(ids) : '',
      }));
      if (this.showAll()) {
        this.prepareShowAllShells();
      } else {
        this.prepareSingleView();
      }
      return;
    }
    if (change.key === 'user') {
      const ids = parseFilterIds(change.value);
      this.selectedUserId.set(ids.length === 1 ? Number(ids[0]) : null);
      this.activeFilters.update((prev) => ({
        ...prev,
        user: ids.length ? serializeFilterIds(ids) : '',
      }));
      this.reloadExpandedTitles();
      this.refreshTitleFieldCounts();
      return;
    }
    if (change.key === 'archive_status') {
      const value = String(change.value || '').trim();
      this.activeFilters.update((prev) => ({
        ...prev,
        archive_status: value && value !== 'active' ? value : '',
      }));
      this.reloadExpandedTitles();
      this.refreshTitleFieldCounts();
      return;
    }
    if (change.key === 'entry_date') {
      const value = String(change.value || '').trim();
      this.setDate(value || null);
      return;
    }
    if (change.key === 'from' || change.key === 'to') {
      const value = String(change.value || '').trim();
      this.activeFilters.update((prev) => ({
        ...prev,
        [change.key]: value,
      }));
      this.reloadExpandedTitles();
      this.refreshTitleFieldCounts();
      return;
    }
    if (change.key === 'city_id') {
      const ids = parseFilterIds(change.value);
      this.activeFilters.update((prev) => ({
        ...prev,
        city_id: ids.length ? serializeFilterIds(ids) : '',
        district_id: '',
      }));
      this.loadExportLocationFilters(ids.length === 1 ? Number(ids[0]) : undefined);
      this.reloadExpandedTitles();
      this.refreshTitleFieldCounts();
      return;
    }
    if (change.key === 'district_id') {
      const ids = parseFilterIds(change.value);
      this.activeFilters.update((prev) => ({
        ...prev,
        district_id: ids.length ? serializeFilterIds(ids) : '',
      }));
      this.reloadExpandedTitles();
      this.refreshTitleFieldCounts();
    }
  }

  onClearFilter(key: string): void {
    this.onFilterChange({ key, value: '' });
  }

  onClearFilters(): void {
    this.setMainSection(null);
    this.setSubSection(null);
    this.setTitle(null);
    this.setUser(null);
    this.setDate(null);
    this.userOptions.set([]);
    this.subSectionsForMain.set([]);
    this.activeFilters.set({});
    if (this.isExportReports()) {
      this.loadExportLocationFilters();
    }
  }

  onMainToolbarModelChange(value: number | null): void {
    this.setMainSection(value);
  }

  toggleShowAll(): void {
    // Leaving section show-all → restore single / category title list.
    if (this.showAll()) {
      this.showAll.set(false);
      this.subSectionBlocks.set([]);
      if (this.selectedSubId() != null || this.hasTitleScope()) {
        this.prepareSingleView();
      }
      return;
    }

    const mainIds = this.resolvedMainSectionIds();
    const subs = this.filteredSubSections();

    // Category/title scope without loaded sub-sections: keep listing all matching titles
    // (do not wipe the view or demand a main section).
    if (!subs.length) {
      if (this.hasTitleScope()) {
        this.selectedSubId.set(null);
        this.subSectionBlocks.set([]);
        this.prepareSingleView();
        return;
      }
      this.toast.error(this.t('admin-report.select-main-first'));
      return;
    }
    if (!mainIds.length && subs.length > MAX_SUB_SECTIONS_LOAD) {
      this.toast.error(this.t('admin-report.select-main-first'));
      return;
    }
    if (subs.length > MAX_SUB_SECTIONS_LOAD) {
      this.toast.error(
        this.t('admin-report.too-many-sections').replace('{max}', String(MAX_SUB_SECTIONS_LOAD)),
      );
      return;
    }

    this.showAll.set(true);
    this.selectedSubId.set(null);
    this.singleViewTitleTables.set([]);
    this.prepareShowAllShells();
  }

  /** Whether section show-all can run with the current main/sub selection. */
  private canLoadAllSubSections(): boolean {
    const mainIds = this.resolvedMainSectionIds();
    const subs = this.filteredSubSections();
    if (!subs.length) return false;
    if (!mainIds.length && subs.length > MAX_SUB_SECTIONS_LOAD) return false;
    if (subs.length > MAX_SUB_SECTIONS_LOAD) return false;
    return true;
  }

  // ── Title-level confirm/reject ───────────────────────────────────────────────

  confirmTitle(
    tt: TitleTable,
    approve: boolean,
    subId: number | null,
    withOptionalNote = false,
  ): void {
    const restoreUi = this.captureUiState();
    const ids = tt.allInfoIds;
    if (!ids.length) return;
    const post = (draft: string) => {
      const body: Record<string, unknown> = {
        ids,
        status: approve ? 'accept' : 'reject',
      };
      if (draft) body['note'] = draft;
      this.api
        .post<{ updated: number; updated_rows?: number }>('/infos/confirm-ids/', body)
        .subscribe({
          next: (res) => {
            this.toast.success(
              this.t(approve ? 'info-report.bulk-confirmed' : 'info-report.bulk-rejected').replace(
                '{count}',
                String(bulkToastRowCount(res)),
              ),
            );
            this.reloadAfterAction(subId, tt.titleId, restoreUi);
          },
          error: () => this.toast.error(this.t('user-data.update-error')),
        });
    };
    if (withOptionalNote) {
      this.openNoteModal('confirm', post);
    } else {
      post('');
    }
  }

  // ── Row-level confirm/reject ─────────────────────────────────────────────────

  confirmRow(
    row: AdminReportRow,
    approve: boolean,
    subId: number | null,
    withOptionalNote = false,
    titleId?: number | null,
  ): void {
    const restoreUi = this.captureUiState();
    const ids: number[] = row._infoIds;
    const post = (draft: string) => {
      const body: Record<string, unknown> = {
        ids,
        status: approve ? 'accept' : 'reject',
      };
      if (draft) body['note'] = draft;
      this.api
        .post<{ updated: number; updated_rows?: number }>('/infos/confirm-ids/', body)
        .subscribe({
          next: () => {
            this.toast.success(this.t(approve ? 'info-report.approved' : 'info-report.rejected'));
            this.reloadAfterAction(subId, titleId ?? null, restoreUi);
          },
          error: () => this.toast.error(this.t('user-data.update-error')),
        });
    };
    if (withOptionalNote) {
      this.openNoteModal('confirm', post);
    } else {
      post('');
    }
  }

  // ── Bulk confirm/reject (all in sub-section) ─────────────────────────────────

  bulkConfirmSub(subId: number): void {
    const restoreUi = this.captureUiState();
    this.api
      .post<
        BulkConfirmResponse & { updated_rows?: number }
      >('/infos/bulk-confirm/', {}, { sub_main_id: subId })
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-confirmed').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  bulkRejectSub(subId: number): void {
    const restoreUi = this.captureUiState();
    this.api
      .post<
        BulkRejectResponse & { updated_rows?: number }
      >('/infos/bulk-reject/', {}, { sub_main_id: subId })
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-rejected').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  bulkConfirmBlock(subMainId: number): void {
    const restoreUi = this.captureUiState();
    const body: Record<string, unknown> = {};
    this.api
      .post<BulkConfirmResponse>('/infos/bulk-confirm/', body, { sub_main_id: subMainId })
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-confirmed').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subMainId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  bulkRejectBlock(subMainId: number): void {
    const restoreUi = this.captureUiState();
    this.api
      .post<
        BulkRejectResponse & { updated_rows?: number }
      >('/infos/bulk-reject/', {}, { sub_main_id: subMainId })
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-rejected').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subMainId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  /** Query params for bulk confirm/reject on Submitted data (current sub + optional filters). */
  private overviewBulkFilterParams(): ApiParams {
    return overviewBulkParams({
      subMainId: this.selectedSubId(),
      titleId: this.selectedTitleId(),
      userId: this.selectedUserId(),
      date: this.selectedDate(),
      titleCategoryIds: parseFilterIds(this.activeFilters()['title_category_id']),
    });
  }

  overviewBulkConfirm(): void {
    const subId = this.selectedSubId();
    if (subId == null) return;
    const restoreUi = this.captureUiState();
    this.api
      .post<BulkConfirmResponse>('/infos/bulk-confirm/', {}, this.overviewBulkFilterParams())
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-confirmed').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  overviewBulkReject(): void {
    const subId = this.selectedSubId();
    if (subId == null) return;
    const restoreUi = this.captureUiState();
    this.api
      .post<
        BulkRejectResponse & { updated_rows?: number }
      >('/infos/bulk-reject/', {}, this.overviewBulkFilterParams())
      .subscribe({
        next: (res) => {
          this.toast.success(
            this.t('info-report.bulk-rejected').replace('{count}', String(bulkToastRowCount(res))),
          );
          this.reloadExpandedTitles(subId, restoreUi);
        },
        error: () => this.toast.error(this.t('user-data.update-error')),
      });
  }

  /** Follow-up note only — does not change confirmed (uses commit_note on Info). */
  commitRowNote(row: AdminReportRow, subId: number | null, titleId?: number | null): void {
    const restoreUi = this.captureUiState();
    const ids: number[] = row._infoIds;
    if (!ids.length) return;
    this.openNoteModal('commit', (draft) => {
      this.api
        .post<{ updated: number }>('/infos/commit-note-ids/', { ids, note: draft })
        .subscribe({
          next: (res) => {
            this.toast.success(
              this.t('admin-report.commit-note-saved').replace('{count}', String(res.updated)),
            );
            this.reloadAfterAction(subId, titleId ?? null, restoreUi);
          },
          error: () => this.toast.error(this.t('user-data.update-error')),
        });
    });
  }

  commitTitleNote(tt: TitleTable, subId: number | null): void {
    const restoreUi = this.captureUiState();
    const ids = tt.allInfoIds;
    if (!ids.length) return;
    this.openNoteModal('commit', (draft) => {
      this.api
        .post<{ updated: number }>('/infos/commit-note-ids/', { ids, note: draft })
        .subscribe({
          next: (res) => {
            this.toast.success(
              this.t('admin-report.commit-note-saved').replace('{count}', String(res.updated)),
            );
            this.reloadAfterAction(subId, tt.titleId, restoreUi);
          },
          error: () => this.toast.error(this.t('user-data.update-error')),
        });
    });
  }

  commitBlockNote(subMainId: number): void {
    const restoreUi = this.captureUiState();
    const block = this.subSectionBlocks().find((b) => b.subSection.id === subMainId);
    if (!block) return;
    const ids = block.titleTables.flatMap((tt) => tt.rows.flatMap((row) => row._infoIds ?? []));
    if (!ids.length) return;
    this.openNoteModal('commit', (draft) => {
      this.api
        .post<{ updated: number }>('/infos/commit-note-ids/', { ids, note: draft })
        .subscribe({
          next: (res) => {
            this.toast.success(
              this.t('admin-report.commit-note-saved').replace('{count}', String(res.updated)),
            );
            this.reloadExpandedTitles(subMainId, restoreUi);
          },
          error: () => this.toast.error(this.t('user-data.update-error')),
        });
    });
  }

  // ── Data loading (lazy per title) ───────────────────────────────────────────

  onTitleToggle(subMainId: number | null, titleTable: TitleTable): void {
    const titleId = titleTable.titleId;
    if (titleId == null) return;
    if (titleTable.rowCount === 0) return;

    if (this.showAll()) {
      if (subMainId == null) return;
      this.toggleTitleInBlock(subMainId, titleId);
      return;
    }
    this.toggleTitleInSingleView(titleId);
  }

  private prepareSingleView(): void {
    this.singleViewTitleTables.set(this.buildEmptyTitleTables());
    const subId = this.selectedSubId();
    if (subId != null) {
      this.loadTitleFieldCounts(subId);
    } else if (this.hasTitleScope()) {
      this.loadTitleFieldCounts(null);
    }
  }

  private prepareShowAllShells(): void {
    const subs = this.filteredSubSections();
    if (!subs.length) {
      this.subSectionBlocks.set([]);
      return;
    }
    const shells = this.buildEmptyTitleTables();
    this.subSectionBlocks.set(
      subs.map((subSection) => ({
        subSection,
        titleTables: shells.map((shell) => ({ ...shell })),
        isLoading: false,
      })),
    );
    for (const subSection of subs) {
      this.loadTitleFieldCounts(subSection.id);
    }
  }

  /** Accordion: only one title panel open at a time. */
  private collapseOtherTitles(keepSubMainId: number | null, keepTitleId: number): void {
    if (this.showAll()) {
      this.subSectionBlocks.update((blocks) =>
        blocks.map((block) => ({
          ...block,
          titleTables: block.titleTables.map((table) => {
            const keep =
              keepSubMainId != null &&
              block.subSection.id === keepSubMainId &&
              table.titleId === keepTitleId;
            return keep || !table.isExpanded ? table : { ...table, isExpanded: false };
          }),
        })),
      );
      return;
    }

    this.singleViewTitleTables.update((tables) =>
      tables.map((table) =>
        table.titleId === keepTitleId || !table.isExpanded
          ? table
          : { ...table, isExpanded: false },
      ),
    );
  }

  private toggleTitleInSingleView(titleId: number): void {
    const restoreScroll = this.captureUiState();
    const tables = [...this.singleViewTitleTables()];
    const index = tables.findIndex((t) => t.titleId === titleId);
    if (index < 0) return;

    const current = tables[index];
    if (current.isExpanded && current.isLoaded) {
      tables[index] = { ...current, isExpanded: false };
      this.singleViewTitleTables.set(tables);
      restoreScroll();
      return;
    }
    if (current.isLoaded) {
      this.collapseOtherTitles(this.selectedSubId(), titleId);
      const next = [...this.singleViewTitleTables()];
      const i = next.findIndex((t) => t.titleId === titleId);
      if (i >= 0) next[i] = { ...next[i], isExpanded: true };
      this.singleViewTitleTables.set(next);
      restoreScroll();
      return;
    }

    const subId = this.selectedSubId();
    if (subId == null && !this.hasTitleScope()) return;
    this.loadTitleData(subId, titleId, restoreScroll);
  }

  private toggleTitleInBlock(subMainId: number, titleId: number): void {
    const restoreScroll = this.captureUiState();
    const blocks = [...this.subSectionBlocks()];
    const blockIndex = blocks.findIndex((b) => b.subSection.id === subMainId);
    if (blockIndex < 0) return;

    const block = blocks[blockIndex];
    const tables = [...block.titleTables];
    const titleIndex = tables.findIndex((t) => t.titleId === titleId);
    if (titleIndex < 0) return;

    const current = tables[titleIndex];
    if (current.isExpanded && current.isLoaded) {
      tables[titleIndex] = { ...current, isExpanded: false };
      blocks[blockIndex] = { ...block, titleTables: tables };
      this.subSectionBlocks.set(blocks);
      restoreScroll();
      return;
    }
    if (current.isLoaded) {
      this.collapseOtherTitles(subMainId, titleId);
      this.subSectionBlocks.update((list) =>
        list.map((b) => {
          if (b.subSection.id !== subMainId) return b;
          return {
            ...b,
            titleTables: b.titleTables.map((t) =>
              t.titleId === titleId ? { ...t, isExpanded: true } : t,
            ),
          };
        }),
      );
      restoreScroll();
      return;
    }

    this.loadTitleData(subMainId, titleId, restoreScroll);
  }

  private loadTitleData(
    subMainId: number | null,
    titleId: number,
    restoreUi?: () => void,
    append = false,
  ): void {
    const restoreScroll = restoreUi ?? this.captureUiState();
    const current = this.findTitleTable(subMainId, titleId);
    const nextPage = append ? (current?.loadedPage ?? 1) + 1 : 1;
    if (append) {
      if (
        !current ||
        current.isLoading ||
        current.isLoadingMore ||
        (current.totalCount != null && current.rows.length >= current.totalCount)
      ) {
        return;
      }
      this.patchTitleTable(subMainId, titleId, (table) => ({
        ...table,
        isLoadingMore: true,
        isExpanded: true,
      }));
    } else {
      this.collapseOtherTitles(subMainId, titleId);
      this.patchTitleTable(subMainId, titleId, (table) => ({
        ...table,
        isLoading: true,
        isLoadingMore: false,
        loadedPage: 0,
        isExpanded: true,
      }));
    }
    restoreScroll();

    const queryOpts = {
      ...titleScopedQueryOpts(subMainId, titleId),
      page: nextPage,
    };

    this.api.get<PaginatedInfoRows>(this.infoRowsUrl(this.buildInfoQuery(queryOpts))).subscribe({
      next: (res) => {
        const built = this.buildTitleTableFromApiRows(res.results || [], titleId);
        this.patchTitleTable(subMainId, titleId, (table) => {
          const newRows = built?.rows ?? [];
          const rows = append ? [...table.rows, ...newRows] : newRows;
          const columns = built?.columns?.length ? built.columns : table.columns;
          const allInfoIds = rows.flatMap((r) => r._infoIds);
          return {
            ...table,
            titleName: built?.titleName ?? table.titleName,
            columns,
            rows,
            allInfoIds,
            totalCount: res.count ?? rows.length,
            rowCount: res.count ?? rows.length,
            loadedPage: nextPage,
            isLoading: false,
            isLoadingMore: false,
            isLoaded: true,
            isExpanded: true,
          };
        });
        restoreScroll();
      },
      error: () => {
        this.patchTitleTable(subMainId, titleId, (table) => ({
          ...table,
          isLoading: false,
          isLoadingMore: false,
          isLoaded: true,
          isExpanded: true,
          ...(append
            ? {}
            : {
                rows: [],
                allInfoIds: [],
                rowCount: 0,
                totalCount: 0,
                loadedPage: 0,
              }),
        }));
        restoreScroll();
      },
    });
  }

  loadMoreTitleData(subMainId: number | null, titleId: number): void {
    this.loadTitleData(subMainId, titleId, undefined, true);
  }

  private findTitleTable(subMainId: number | null, titleId: number): TitleTable | undefined {
    if (this.showAll() && subMainId != null) {
      const block = this.subSectionBlocks().find((b) => b.subSection.id === subMainId);
      return block?.titleTables.find((t) => t.titleId === titleId);
    }
    return this.singleViewTitleTables().find((t) => t.titleId === titleId);
  }

  private patchTitleTable(
    subMainId: number | null,
    titleId: number,
    updater: (table: TitleTable) => TitleTable,
  ): void {
    if (this.showAll() && subMainId != null) {
      this.subSectionBlocks.update((blocks) =>
        blocks.map((block) => {
          if (block.subSection.id !== subMainId) return block;
          return {
            ...block,
            titleTables: block.titleTables.map((table) =>
              table.titleId === titleId ? updater(table) : table,
            ),
          };
        }),
      );
      return;
    }

    this.singleViewTitleTables.update((tables) =>
      tables.map((table) => (table.titleId === titleId ? updater(table) : table)),
    );
  }

  private reloadAfterAction(
    subMainId: number | null,
    titleId: number | null,
    restoreUi?: () => void,
  ): void {
    if (titleId != null) {
      this.loadTitleData(subMainId, titleId, restoreUi);
      return;
    }
    this.reloadExpandedTitles(subMainId ?? undefined, restoreUi);
  }

  private reloadExpandedTitles(subMainId?: number | null, restoreUi?: () => void): void {
    if (this.showAll()) {
      const blocks = this.subSectionBlocks();
      for (const block of blocks) {
        if (subMainId != null && block.subSection.id !== subMainId) continue;
        for (const table of block.titleTables) {
          if (table.isLoaded && table.isExpanded && table.titleId != null) {
            this.loadTitleData(block.subSection.id, table.titleId);
          }
        }
      }
      restoreUi?.();
      return;
    }

    const subId = subMainId !== undefined ? subMainId : this.selectedSubId();
    if (subId == null && !this.hasTitleScope()) {
      restoreUi?.();
      return;
    }

    const expanded = this.singleViewTitleTables().filter(
      (table) => table.isLoaded && table.isExpanded && table.titleId != null,
    );
    if (!expanded.length) {
      restoreUi?.();
      return;
    }

    let pending = expanded.length;
    const done = () => {
      pending -= 1;
      if (pending <= 0) restoreUi?.();
    };

    for (const table of expanded) {
      this.loadTitleData(subId, table.titleId!, done);
    }
  }

  private refreshTitleFieldCounts(): void {
    if (this.showAll()) {
      for (const block of this.subSectionBlocks()) {
        this.loadTitleFieldCounts(block.subSection.id);
      }
      return;
    }
    const subId = this.selectedSubId();
    if (subId != null) this.loadTitleFieldCounts(subId);
    else if (this.hasTitleScope()) this.loadTitleFieldCounts(null);
  }

  private loadTitleFieldCounts(subMainId: number | null): void {
    if (this.showAll() && subMainId != null) {
      this.subSectionBlocks.update((blocks) =>
        blocks.map((block) => {
          if (block.subSection.id !== subMainId) return block;
          return {
            ...block,
            titleTables: block.titleTables.map((table) => ({ ...table, rowCount: null })),
          };
        }),
      );
    } else {
      this.singleViewTitleTables.update((tables) =>
        tables.map((table) => ({ ...table, rowCount: null })),
      );
    }

    const tables =
      this.showAll() && subMainId != null
        ? (this.subSectionBlocks().find((b) => b.subSection.id === subMainId)?.titleTables ?? [])
        : this.singleViewTitleTables();

    const titleIds = tables.map((table) => table.titleId).filter((id): id is number => id != null);
    if (!titleIds.length) return;

    forkJoin(
      titleIds.map((titleId) =>
        this.api
          .get<{ count: number; title_id: number }>(
            this.rowCountUrl(this.buildInfoQuery(titleScopedQueryOpts(subMainId, titleId))),
          )
          .pipe(
            map((res) => ({ titleId, count: res.count ?? 0 })),
            catchError(() => of({ titleId, count: 0 })),
          ),
      ),
    ).subscribe((counts) => {
      const countByTitle = new Map(counts.map((item) => [item.titleId, item.count]));
      const applyCounts = (list: TitleTable[]): TitleTable[] =>
        list.map((table) =>
          table.titleId != null && countByTitle.has(table.titleId)
            ? { ...table, rowCount: countByTitle.get(table.titleId)! }
            : table,
        );

      if (this.showAll() && subMainId != null) {
        this.subSectionBlocks.update((blocks) =>
          blocks.map((block) =>
            block.subSection.id === subMainId
              ? { ...block, titleTables: applyCounts(block.titleTables) }
              : block,
          ),
        );
      } else {
        this.singleViewTitleTables.update((list) => applyCounts(list));
      }
    });
  }

  private buildEmptyTitleTables(): TitleTable[] {
    const allAttrs = this.allAttributes();
    const titleIdsFilter = parseFilterIds(this.activeFilters()['title_id']);
    let titleList = [...this.titlesForFilterOptions()].sort(
      (a, b) => (a.order ?? Number.MAX_SAFE_INTEGER) - (b.order ?? Number.MAX_SAFE_INTEGER),
    );

    if (titleIdsFilter.length) {
      titleList = titleList.filter((title) => titleIdsFilter.includes(String(title.id)));
    }

    return titleList
      .map((title) => {
        const schemaAttrs = allAttrs.filter((attr) => attr.title === title.id);
        if (schemaAttrs.length === 0) return null;

        const columns = withAdminReportColumnSizing([
          { key: 'user_name', label: this.t('admin-report.user-col') },
          ...schemaAttrs.map((attr) => ({ key: `attr_${attr.id}`, label: attr.label })),
          { key: '_commit_note', label: this.t('admin-report.commit-note-col') },
          { key: '_confirm_note', label: this.t('admin-report.confirm-note-col') },
          { key: '_confirm_status', label: this.t('admin-report.confirmed-col') },
        ]);

        return {
          titleId: title.id,
          titleName: title.name,
          columns,
          rows: [],
          allInfoIds: [],
          rowCount: null,
          isLoading: false,
          isLoaded: false,
          isExpanded: false,
        };
      })
      .filter((table) => table !== null) as TitleTable[];
  }

  private infoListUrl(query: string): string {
    const base = this.isExportReports() ? '/export-reports/' : '/infos/';
    return query ? `${base}?${query}` : base;
  }

  private rowCountUrl(query: string): string {
    return query ? `/infos/row-count/?${query}` : '/infos/row-count/';
  }

  private infoRowsUrl(query: string): string {
    return query ? `/info-rows/?${query}` : '/info-rows/';
  }

  /** Build one title table from GET /info-rows/ (canonical row grouping). */
  private buildTitleTableFromApiRows(
    apiRows: InfoRow[],
    titleId: number | null,
  ): Pick<TitleTable, 'columns' | 'rows' | 'allInfoIds' | 'titleName'> | null {
    const allAttrs = this.allAttributes();
    const schemaAttrs = allAttrs.filter((a) => (a.title ?? null) === titleId);
    const attrsForColumns =
      schemaAttrs.length > 0 ? schemaAttrs.map((a) => ({ id: a.id, label: a.label })) : [];

    if (attrsForColumns.length === 0 && apiRows.length === 0) {
      return null;
    }

    const titleName =
      titleId !== null
        ? (schemaAttrs[0]?.title_name ?? apiRows[0]?.title_name ?? `Title ${titleId}`)
        : (apiRows[0]?.title_name ?? '—');

    const columns = withAdminReportColumnSizing([
      { key: 'user_name', label: this.t('admin-report.user-col') },
      ...attrsForColumns.map((a) => ({ key: `attr_${a.id}`, label: a.label })),
      { key: '_commit_note', label: this.t('admin-report.commit-note-col') },
      { key: '_confirm_note', label: this.t('admin-report.confirm-note-col') },
      { key: '_confirm_status', label: this.t('admin-report.confirmed-col') },
    ]);

    const rows = mapInfoRowsToAdminRows(apiRows);
    return {
      titleName,
      columns,
      rows,
      allInfoIds: rows.flatMap((r) => r._infoIds),
    };
  }

  private buildExportDownloadContext(): ExportDownloadContext {
    return {
      hasScope: this.hasInfoQueryScope(),
      scope: {
        activeFilters: this.activeFilters(),
        selectedMainId: this.selectedMainId(),
        scopedInfoQuery: this.buildInfoQuery({ includeUser: true }),
      },
    };
  }

  private buildInfoQuery(opts?: {
    subMainId?: number;
    titleId?: number;
    includeUser?: boolean;
    includeTitleFilter?: boolean;
    pageSize?: number;
    page?: number;
  }): string {
    return buildInfoQueryParams({
      activeFilters: this.activeFilters(),
      selectedMainId: this.selectedMainId(),
      selectedDate: this.selectedDate(),
      isExportReports: this.isExportReports(),
      opts,
    });
  }

  private hasInfoQueryScope(): boolean {
    const af = this.activeFilters();
    if (parseFilterIds(af['sub_main_id']).length) return true;
    if (parseFilterIds(af['main_section_id']).length) return true;
    if (this.selectedMainId() != null) return true;
    return hasTitleScopeFromFilters(af);
  }

  private mergeUserOptionsFromRecords(records: InfoRecord[]): void {
    if (!records.length) return;
    const map = new Map(this.userOptions().map((o) => [o.value, o.label]));
    for (const r of records) {
      if (r.user) map.set(String(r.user), r.user_name || `User ${r.user}`);
    }
    this.userOptions.set(Array.from(map.entries()).map(([value, label]) => ({ value, label })));
  }

  /** Lazy user dropdown: only when filters open, scope set, and list still empty. */
  private loadUserOptionsForFilterIfNeeded(): void {
    if (!this.hasInfoQueryScope() || this.userOptions().length > 0) return;
    this.api
      .get<{ results: InfoRecord[] }>(this.infoListUrl(this.buildInfoQuery({ includeUser: false })))
      .subscribe({
        next: (res) => this.mergeUserOptionsFromRecords(res.results || []),
        error: () => this.userOptions.set([]),
      });
  }

  private openNoteModal(kind: 'confirm' | 'commit', onDraft: (draft: string) => void): void {
    this.noteModalKind.set(kind);
    this.pendingNoteAction = onDraft;
    this.confirmNoteDraft.set('');
    this.confirmNoteModalVisible.set(true);
  }

  submitConfirmNoteModal(): void {
    const fn = this.pendingNoteAction;
    this.pendingNoteAction = null;
    this.confirmNoteModalVisible.set(false);
    if (!fn) return;
    fn(this.confirmNoteDraft().trim());
  }

  cancelConfirmNoteModal(): void {
    this.pendingNoteAction = null;
    this.confirmNoteModalVisible.set(false);
  }

  private captureUiState(): () => void {
    const restoreScroll = captureScrollPosition();
    const active = document.activeElement as HTMLElement | null;
    const focusKey = active?.getAttribute('data-focus-key') ?? null;

    return () => {
      restoreScroll();
      if (!focusKey) return;
      requestAnimationFrame(() => {
        const target = Array.from(document.querySelectorAll<HTMLElement>('[data-focus-key]')).find(
          (el) => el.getAttribute('data-focus-key') === focusKey,
        );
        target?.focus({ preventScroll: true });
      });
    };
  }

  trackByTitleId(_index: number, table: TitleTable): string | number {
    return table.titleId ?? _index;
  }

  trackByTitleGroupId(_index: number, group: AdminTitleGroup): string {
    return String(group.titleId ?? 'none');
  }

  trackByAdminTitleSlice(_index: number, slice: { subMainId: number }): number {
    return slice.subMainId;
  }

  mainSectionNameForSubMain(subMainId: number): string {
    const sub =
      this.filteredSubSections().find((s) => s.id === subMainId) ??
      this.subSectionsForMain().find((s) => s.id === subMainId);
    if (!sub) return '—';
    const main = this.mainSections().find((m) => m.id === sub.main_section_id);
    return main?.name ?? '—';
  }

  titleOrderFor(titleId: number | null): number {
    if (titleId == null) return 9999;
    const t = this.titles().find((x) => x.id === titleId);
    return t?.order ?? 9999;
  }

  trackBySubSectionId(_index: number, block: SubSectionBlock): number {
    return block.subSection.id;
  }

  private compareTitleIdsForDisplay(a: number | null, b: number | null): number {
    if (a === null && b === null) return 0;
    if (a === null) return 1;
    if (b === null) return -1;
    const ta = this.titles().find((t) => t.id === a);
    const tb = this.titles().find((t) => t.id === b);
    const oa = ta?.order ?? Number.MAX_SAFE_INTEGER;
    const ob = tb?.order ?? Number.MAX_SAFE_INTEGER;
    return oa - ob || a - b;
  }

  private buildTitleTableFromRecords(
    records: InfoRecord[],
    titleId: number | null,
  ): TitleTable | null {
    const tables = this.buildTitleTables(
      records.filter((record) => (record.title_id ?? null) === titleId),
    );
    return tables.find((table) => table.titleId === titleId) ?? tables[0] ?? null;
  }

  private buildTitleTables(records: InfoRecord[]): TitleTable[] {
    const allAttrs = this.allAttributes();

    const titleIds = new Set<number | null>();
    for (const r of records) titleIds.add(r.title_id ?? null);

    const recordsByTitle = new Map<number | null, InfoRecord[]>();
    for (const r of records) {
      const key = r.title_id ?? null;
      if (!recordsByTitle.has(key)) recordsByTitle.set(key, []);
      recordsByTitle.get(key)!.push(r);
    }

    const sortedTitleIds = Array.from(titleIds).sort((a, b) =>
      this.compareTitleIdsForDisplay(a, b),
    );

    return sortedTitleIds
      .map((titleId) => {
        const titleRecords = recordsByTitle.get(titleId) ?? [];

        const schemaAttrs = allAttrs.filter((a) => (a.title ?? null) === titleId);
        const attrsForColumns =
          schemaAttrs.length > 0
            ? schemaAttrs.map((a) => ({ id: a.id, label: a.label }))
            : [
                ...new Map(
                  titleRecords.map((r) => [
                    r.attribute,
                    { id: r.attribute, label: r.attribute_label },
                  ]),
                ).values(),
              ];

        if (attrsForColumns.length === 0) return null;

        const titleName =
          titleId !== null
            ? (schemaAttrs[0]?.title_name ?? titleRecords[0]?.title_name ?? `Title ${titleId}`)
            : (titleRecords[0]?.attribute_label ?? '—');

        const columns = withAdminReportColumnSizing([
          { key: 'user_name', label: this.t('admin-report.user-col') },
          ...attrsForColumns.map((a) => ({ key: `attr_${a.id}`, label: a.label })),
          { key: '_commit_note', label: this.t('admin-report.commit-note-col') },
          { key: '_confirm_note', label: this.t('admin-report.confirm-note-col') },
          { key: '_confirm_status', label: this.t('admin-report.confirmed-col') },
        ]);

        const emptyRow: Record<string, string> = Object.fromEntries(
          attrsForColumns.map((a) => [`attr_${a.id}`, '—']),
        );
        emptyRow['_commit_note'] = '—';
        emptyRow['_confirm_note'] = '—';
        const rowBuckets = new Map<number, AdminReportRowDraft[]>();
        for (const r of titleRecords) {
          const userRows = rowBuckets.get(r.user) ?? [];
          let targetRow = userRows.find((row) => row[`attr_${r.attribute}`] === '—');

          if (!targetRow) {
            targetRow = {
              id: `${r.user}-${userRows.length + 1}`,
              user_name: r.user_name ?? '—',
              ...emptyRow,
              _infoIds: [],
              _acceptedCount: 0,
              _waitingCount: 0,
              _rejectedCount: 0,
              _commitSet: new Set<string>(),
              _noteSet: new Set<string>(),
            };
            userRows.push(targetRow);
          }

          targetRow[`attr_${r.attribute}`] = r.value;
          targetRow._infoIds.push(r.id);
          if (r.confirmed === 'accept') targetRow._acceptedCount++;
          else if (r.confirmed === 'reject') targetRow._rejectedCount++;
          else targetRow._waitingCount++;
          if (r.commit_note?.trim()) targetRow._commitSet.add(r.commit_note.trim());
          if (r.confirm_note?.trim()) targetRow._noteSet.add(r.confirm_note.trim());

          rowBuckets.set(r.user, userRows);
        }

        const rows: AdminReportRow[] = Array.from(rowBuckets.values())
          .flat()
          .map((row) => {
            const noteText = row._noteSet.size ? Array.from(row._noteSet).join(' ; ') : '—';
            const commitText = row._commitSet.size ? Array.from(row._commitSet).join(' ; ') : '—';
            const { _noteSet, _commitSet, _acceptedCount, _waitingCount, _rejectedCount, ...rest } =
              row;
            const total = row._infoIds.length;
            const allAccepted = _acceptedCount === total;
            const allRejected = _rejectedCount === total;
            return {
              ...rest,
              _commit_note: commitText,
              _confirm_note: noteText,
              _allAccepted: allAccepted,
              _allRejected: allRejected,
              _confirmStatus: confirmStatusFromRow({
                _allAccepted: allAccepted,
                _allRejected: allRejected,
              }),
            } as AdminReportRow;
          });

        const allInfoIds = rows.flatMap((row) => row._infoIds);

        return {
          titleId,
          titleName,
          columns,
          rows,
          allInfoIds,
          isLoading: false,
          isLoaded: true,
          isExpanded: true,
        };
      })
      .filter((t) => t !== null) as TitleTable[];
  }
}
