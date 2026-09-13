import { CommonModule, NgTemplateOutlet } from '@angular/common';
import {
  Component,
  OnInit,
  computed,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { LocationsService } from '../../shared/services/locations.service';
import { FilterState } from '../../shared/utils/filter-state';
import { isEmptyFilterValue } from '../../shared/utils/filter-params';
import {
  PROJECT_STATUSES,
  type BudgetSelectOption,
  type ProjectDashboardStats,
  type ProjectMapPoint,
  type ProjectMapPointsResponse,
  type ProjectStatus,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';
import { formatBudgetExpenditurePercent } from './budget-expenditure.utils';
import { CATEGORY_SECTION_DEFS } from './category-tree.utils';
import { PageLoaderComponent } from '../../shared/components/page-loader/page-loader.component';
import { ProjectsMapComponent } from '../../shared/components/projects-map/projects-map.component';
import { forkJoin } from 'rxjs';

interface StatCard {
  id: string;
  label: string;
  value: string;
  subValue?: string;
  icon: string;
  color: string;
  hintKey: string;
}

interface ActiveFilterChip {
  key: string;
  label: string;
  value: string;
}

interface DashboardCategoryNode {
  id: number;
  code: string;
  name: string;
  projectCount: number;
  totalExpenditure: string;
  children: DashboardCategoryNode[];
}

@Component({
  selector: 'app-project-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    NgTemplateOutlet,
    PageLoaderComponent,
    ProjectsMapComponent,
  ],
  templateUrl: './project-dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './project-dashboard.component.scss',
})
export class ProjectDashboardComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private locations = inject(LocationsService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), '');

  data = signal<ProjectDashboardStats | null>(null);
  mapPoints = signal<ProjectMapPoint[]>([]);
  mapMeta = signal<Pick<
    ProjectMapPointsResponse,
    'count' | 'total_projects' | 'without_coordinates' | 'truncated'
  > | null>(null);
  foundations = signal<BudgetSelectOption[]>([]);
  projectTypes = signal<BudgetSelectOption[]>([]);
  governorates = signal<BudgetSelectOption[]>([]);
  communities = signal<BudgetSelectOption[]>([]);
  budgetYears = signal<{ value: string; label: string }[]>([]);
  showEmptyCategories = signal(false);

  statCards = computed<StatCard[]>(() => {
    const summary = this.data()?.summary;
    if (!summary) return [];
    return [
      {
        id: 'total-projects',
        label: this.t('budget.dashboard.total-projects'),
        value: String(summary.total_projects),
        icon: 'folder',
        color: 'primary',
        hintKey: 'budget.dashboard.hint.total-projects',
      },
      {
        id: 'active-projects',
        label: this.t('budget.dashboard.active-projects'),
        value: String(summary.active_projects),
        icon: 'play_circle',
        color: 'green',
        hintKey: 'budget.dashboard.hint.active-projects',
      },
      {
        id: 'avg-completion',
        label: this.t('budget.dashboard.avg-completion'),
        value: `${summary.avg_completion}%`,
        icon: 'trending_up',
        color: 'blue',
        hintKey: 'budget.dashboard.hint.avg-completion',
      },
      {
        id: 'total-approved',
        label: this.t('budget.dashboard.total-approved'),
        value: this.formatMoney(summary.total_approved_budget),
        icon: 'account_balance',
        color: 'indigo',
        hintKey: 'budget.dashboard.hint.total-approved',
      },
      {
        id: 'total-expenditure',
        label: this.t('budget.dashboard.total-expenditure'),
        value: this.formatMoney(summary.total_expenditure),
        icon: 'payments',
        color: 'amber',
        hintKey: 'budget.dashboard.hint.total-expenditure',
      },
      {
        id: 'expenditure-percent',
        label: this.t('budget.dashboard.expenditure-percent'),
        value: formatBudgetExpenditurePercent(summary.expenditure_percent),
        icon: 'percent',
        color: 'slate',
        hintKey: 'budget.dashboard.hint.expenditure-percent',
      },
      {
        id: 'remaining-budget',
        label: this.t('budget.dashboard.remaining-budget'),
        value: this.formatMoney(summary.remaining_budget),
        icon: 'savings',
        color: 'green',
        hintKey: 'budget.dashboard.hint.remaining-budget',
      },
      {
        id: 'over-budget',
        label: this.t('budget.dashboard.over-budget'),
        value: String(summary.over_budget_count),
        icon: 'warning',
        color: 'amber',
        hintKey: 'budget.dashboard.hint.over-budget',
      },
      {
        id: 'overdue',
        label: this.t('budget.dashboard.overdue'),
        value: String(summary.overdue_count),
        icon: 'schedule',
        color: 'amber',
        hintKey: 'budget.dashboard.hint.overdue',
      },
    ];
  });

  categoryStatCards = computed<StatCard[]>(() => {
    const sections = this.data()?.by_category_section ?? [];
    const cardConfig: Record<string, { icon: string; color: string; hintKey: string }> = {
      '31': {
        icon: 'add_circle',
        color: 'blue',
        hintKey: 'budget.dashboard.hint.category-section-31',
      },
      '32': {
        icon: 'sync',
        color: 'green',
        hintKey: 'budget.dashboard.hint.category-section-32',
      },
      '33': {
        icon: 'autorenew',
        color: 'indigo',
        hintKey: 'budget.dashboard.hint.category-section-33',
      },
    };

    return CATEGORY_SECTION_DEFS.map((section) => {
      const stats = sections.find((item) => item.prefix === section.prefix);
      const config = cardConfig[section.prefix];
      return {
        id: `category-section-${section.prefix}`,
        label: this.t(section.labelKey),
        value: this.formatMoney(stats?.total_expenditure ?? '0'),
        subValue: `${stats?.project_count ?? 0} ${this.t('budget.dashboard.category-projects-count')}`,
        icon: config.icon,
        color: config.color,
        hintKey: config.hintKey,
      };
    });
  });

  statusChart = computed(() => {
    const items = this.data()?.by_status ?? [];
    const max = Math.max(...items.map((item) => item.count), 1);
    return items.map((item) => ({
      ...item,
      label: this.statusLabel(item.status as ProjectStatus),
      width: Math.round((item.count / max) * 100),
    }));
  });

  governorateChart = computed(() => {
    const items = this.data()?.by_governorate ?? [];
    const max = Math.max(...items.map((item) => item.count), 1);
    return items.map((item) => ({
      ...item,
      label: item.name || '—',
      width: Math.round((item.count / max) * 100),
    }));
  });

  projectTypeChart = computed(() => {
    const items = this.data()?.by_project_type ?? [];
    const max = Math.max(...items.map((item) => item.count), 1);
    return items.map((item) => ({
      ...item,
      label: item.name || '—',
      width: Math.round((item.count / max) * 100),
    }));
  });

  categoryTree = computed<DashboardCategoryNode[]>(() => {
    const items = this.data()?.by_category ?? [];
    if (items.length === 0) return [];

    const nodes = new Map<number, DashboardCategoryNode>();
    for (const item of items) {
      nodes.set(item.id, {
        id: item.id,
        code: item.code,
        name: item.name,
        projectCount: item.project_count,
        totalExpenditure: item.total_expenditure,
        children: [],
      });
    }

    const roots: DashboardCategoryNode[] = [];
    for (const item of items) {
      const node = nodes.get(item.id);
      if (!node) continue;
      if (item.parent_id != null && nodes.has(item.parent_id)) {
        nodes.get(item.parent_id)!.children.push(node);
      } else {
        roots.push(node);
      }
    }

    const sortRecursive = (list: DashboardCategoryNode[]): void => {
      list.sort((left, right) =>
        (left.code || left.name).localeCompare(right.code || right.name, 'ar', { numeric: true }),
      );
      list.forEach((node) => sortRecursive(node.children));
    };
    sortRecursive(roots);
    return roots;
  });

  categorySections = computed(() => {
    const showEmpty = this.showEmptyCategories();
    const sectionStats = this.data()?.by_category_section ?? [];
    const roots = this.categoryTree()
      .map((node) => this.filterCategoryNode(node, showEmpty))
      .filter((node): node is DashboardCategoryNode => node !== null);

    return CATEGORY_SECTION_DEFS.map((section) => {
      const stats = sectionStats.find((item) => item.prefix === section.prefix);
      return {
        prefix: section.prefix,
        label: this.t(section.labelKey),
        projectCount: stats?.project_count ?? 0,
        totalExpenditure: stats?.total_expenditure ?? '0',
        roots: roots.filter((root) => root.code.startsWith(section.prefix)),
      };
    }).filter((section) => showEmpty || section.roots.length > 0);
  });

  uncategorizedProjectsCount = computed(() => this.data()?.uncategorized_projects ?? 0);

  uncategorizedExpenditure = computed(() => this.data()?.uncategorized_expenditure ?? '0');

  hasCategoryPanelContent = computed(
    () =>
      this.categorySections().length > 0 ||
      this.uncategorizedProjectsCount() > 0 ||
      Number(this.uncategorizedExpenditure()) > 0,
  );

  showFoundationFilter = computed(() => this.auth.isAdmin());

  hasActiveFilters = computed(() => this.activeFilterChips().length > 0);

  activeFilterChips = computed<ActiveFilterChip[]>(() => {
    const filters = this.fs.filters();
    const chips: ActiveFilterChip[] = [];

    const add = (key: string, label: string, raw: unknown, display: string) => {
      if (isEmptyFilterValue(raw)) return;
      chips.push({ key, label, value: display });
    };

    const status = filters['status'];
    if (!isEmptyFilterValue(status)) {
      add(
        'status',
        this.t('budget.projects.status'),
        status,
        this.statusLabel(String(status) as ProjectStatus),
      );
    }

    const projectTypeId = filters['project_type'];
    if (!isEmptyFilterValue(projectTypeId)) {
      const name = this.optionName(this.projectTypes(), projectTypeId);
      add('project_type', this.t('budget.annual-budget.project-type'), projectTypeId, name);
    }

    const year = filters['year'];
    if (!isEmptyFilterValue(year)) {
      add('year', this.t('budget.projects.filter-year'), year, String(year));
    }

    const foundationId = filters['foundation'];
    if (!isEmptyFilterValue(foundationId)) {
      const name = this.optionName(this.foundations(), foundationId);
      add('foundation', this.t('budget.fields.foundation'), foundationId, name);
    }

    const governorateId = filters['governorate'];
    if (!isEmptyFilterValue(governorateId)) {
      const name = this.optionName(this.governorates(), governorateId);
      add('governorate', this.t('locations.governorate'), governorateId, name);
    }

    const communityId = filters['community'];
    if (!isEmptyFilterValue(communityId)) {
      const name = this.optionName(this.communities(), communityId);
      add('community', this.t('locations.community'), communityId, name);
    }

    return chips;
  });

  ngOnInit(): void {
    this.loadDependencies();
    this.load();
  }

  load(): void {
    this.fs.loading.set(true);
    const params = { ...this.fs.params };
    delete params['search'];
    forkJoin({
      stats: this.budget.getProjectDashboard(params),
      map: this.budget.getProjectMapPoints(params),
    }).subscribe({
      next: ({ stats, map }) => {
        this.data.set(stats);
        this.mapPoints.set(map.results);
        this.mapMeta.set({
          count: map.count,
          total_projects: map.total_projects,
          without_coordinates: map.without_coordinates,
          truncated: map.truncated,
        });
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.dashboard.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  onFilterChange(key: string, value: string): void {
    this.fs.onFilterChange({ key, value: value || '' });
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

  clearFilters(): void {
    this.fs.clearFilters();
    this.loadCommunityOptions();
  }

  clearFilter(key: string): void {
    this.fs.clearFilter(key);
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

  isFilterActive(key: string): boolean {
    return !isEmptyFilterValue(this.fs.filters()[key]);
  }

  viewProject(id: number): void {
    this.router.navigate(['/budget/projects', id, 'view']);
  }

  toggleEmptyCategories(): void {
    this.showEmptyCategories.update((value) => !value);
  }

  statusLabel(status: ProjectStatus | undefined): string {
    if (!status) return '—';
    return this.t(`budget.projects.status.${status}`);
  }

  statusLabelFn = (status: string) => this.statusLabel(status as ProjectStatus);

  formatMoney(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return '—';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parsed);
  }

  formatDate(value: string | null): string {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString();
  }

  private optionName(options: BudgetSelectOption[], id: unknown): string {
    const key = String(id);
    return options.find((item) => String(item.id) === key)?.name || key;
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
        const years = [...new Set(data.results.map((item) => item.year))].sort((a, b) => b - a);
        this.budgetYears.set(years.map((year) => ({ value: String(year), label: String(year) })));
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

  private filterCategoryNode(
    node: DashboardCategoryNode,
    showEmpty: boolean,
  ): DashboardCategoryNode | null {
    const children = node.children
      .map((child) => this.filterCategoryNode(child, showEmpty))
      .filter((child): child is DashboardCategoryNode => child !== null);
    const hasContent =
      node.projectCount > 0 || Number(node.totalExpenditure) > 0 || children.length > 0;
    if (!showEmpty && !hasContent) {
      return null;
    }
    return { ...node, children };
  }

  protected readonly PROJECT_STATUSES = PROJECT_STATUSES;
  protected readonly Number = Number;
}
