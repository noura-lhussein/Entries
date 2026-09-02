import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { UntypedFormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  PageHeaderComponent,
  type PageHeaderAction,
} from '../../shared/components/page-header/page-header.component';
import { CodeBannerComponent } from '../../shared/components/code-banner/code-banner.component';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { TranslationService } from '../../shared/services/translation.service';
import { ToastService } from '../../shared/services/toast.service';
import { AuthService } from '../../core/services/auth.service';
import type {
  CategorySelectOption,
  Milestone,
  Project,
  ProjectChangeLogEntry,
  ProjectStatus,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';
import { projectTypeCategoryPrefix } from './category-options.utils';
import { formatQuantitativeTarget } from './quantitative-target.utils';
import {
  budgetExpenditureOverBudget,
  budgetExpenditurePercent,
  budgetExpenditureProgressWidth,
  formatBudgetExpenditurePercent,
} from './budget-expenditure.utils';

interface ProjectCategoryNode {
  id: number;
  code: string;
  name: string;
  milestones: Milestone[];
  children: ProjectCategoryNode[];
  totalMilestones: number;
}

const CATEGORY_SECTIONS = [
  { prefix: '31', labelKey: 'budget.projects.category-section-new' },
  { prefix: '32', labelKey: 'budget.projects.category-section-ongoing' },
  { prefix: '33', labelKey: 'budget.projects.category-section-renewal' },
] as const;

interface ChangeLogBatch {
  batchId: string;
  action: ProjectChangeLogEntry['action'];
  userLabel: string;
  changedAt: string;
  ipAddress: string | null;
  clientLatitude: number | null;
  clientLongitude: number | null;
  changes: ProjectChangeLogEntry[];
}

@Component({
  selector: 'app-project-view',
  standalone: true,
  imports: [
    CommonModule,
    PageHeaderComponent,
    CodeBannerComponent,
    EmptyStateComponent,
    FormMapPickerComponent,
    ModalComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header
        [title]="t('budget.projects.view-title')"
        [action]="backAction"
        [actions]="headerActions()"
      />

      @if (loading()) {
        <section class="skeleton-grid">
          @for (item of skeletonItems; track item) {
            <div class="skeleton-card"></div>
          }
        </section>
      } @else if (!project()) {
        <app-empty-state icon="inbox" [message]="t('budget.projects.empty')" />
      } @else {
        <app-code-banner
          [label]="t('budget.projects.code')"
          [code]="projectCode()"
          [hint]="t('budget.projects.code-assigned')"
          [preview]="false"
        />

        <section class="hero">
          <div class="hero-main">
            <p class="hero-subtitle">{{ t('budget.projects.view-subtitle') }}</p>
            <h2 class="hero-title">{{ project()!.name_ar || emptyValue() }}</h2>
            <p class="hero-secondary">{{ project()!.name_en || emptyValue() }}</p>
            <div class="quick-chips">
              <span class="chip">{{ project()!.foundation_name || emptyValue() }}</span>
              <span class="chip">{{ project()!.annual_budget_year || emptyValue() }}</span>
              <span class="chip">{{ project()!.project_type_name || emptyValue() }}</span>
              <span class="chip">{{ project()!.community_name || emptyValue() }}</span>
            </div>
          </div>
          <span class="status-badge" [ngClass]="statusClass(project()!.status)">
            {{ statusLabel(project()!.status) }}
          </span>
        </section>

        <section class="stats-grid">
          <article class="stat-card">
            <p class="stat-label">{{ t('budget.projects.proposed-budget') }}</p>
            <p class="stat-value">{{ moneyDisplay(project()!.proposed_budget) }}</p>
          </article>
          <article class="stat-card">
            <p class="stat-label">{{ t('budget.projects.approved-budget') }}</p>
            <p class="stat-value">{{ moneyDisplay(project()!.approved_budget) }}</p>
          </article>
          <article class="stat-card expenditure" [class.expenditure-over]="expenditureOverBudget()">
            <p class="stat-label">{{ t('budget.projects.budget-expenditure') }}</p>
            <p class="stat-value">{{ moneyDisplay(project()!.budget_expenditure) }}</p>
            <div class="progress-wrap">
              <div class="progress-track">
                <div
                  class="progress-fill expenditure-fill"
                  [style.width.%]="expenditureProgressWidth()"
                ></div>
              </div>
              <small
                >{{ expenditurePercentDisplay() }}
                {{ t('budget.projects.expenditure-percent-of-approved') }}</small
              >
            </div>
          </article>
          <article class="stat-card completion">
            <p class="stat-label">{{ t('budget.projects.percentage-completion') }}</p>
            <p class="stat-value">{{ percentDisplay(project()!.percentage_completion) }}</p>
            <div class="progress-wrap">
              <div class="progress-track">
                <div class="progress-fill" [style.width.%]="progressPercent()"></div>
              </div>
              <small>{{
                project()!.completion_is_manual
                  ? t('budget.projects.completion-manual')
                  : t('budget.projects.completion-auto')
              }}</small>
            </div>
          </article>
        </section>

        <section class="variance-card" [ngClass]="varianceClass()">
          <p class="variance-label">{{ t('budget.projects.remaining-budget') }}</p>
          <p class="variance-value">{{ moneyDisplay(remainingBudget()) }}</p>
          <small>{{ t('budget.projects.remaining-budget-hint') }}</small>
        </section>

        <section class="details-grid">
          <article class="panel">
            <h3>{{ t('budget.projects.section-budget') }}</h3>
            <div class="kv">
              <span>{{ t('budget.projects.annual-budget') }}</span
              ><strong>{{ project()!.annual_budget_code || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.annual-budget.year') }}</span
              ><strong>{{ project()!.annual_budget_year || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.annual-budget.project-type') }}</span
              ><strong>{{ project()!.project_type_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.is-round') }}</span
              ><strong>{{
                project()!.is_round ? t('budget.projects.round-yes') : t('budget.projects.round-no')
              }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.previous-project') }}</span
              ><strong>{{ project()!.previous_project_name || emptyValue() }}</strong>
            </div>
          </article>

          <article class="panel">
            <h3>{{ t('budget.projects.section-location') }}</h3>
            <div class="kv">
              <span>{{ t('budget.fields.foundation') }}</span
              ><strong>{{ project()!.foundation_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('locations.governorate') }}</span
              ><strong>{{ project()!.governorate_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('locations.district') }}</span
              ><strong>{{ project()!.district_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('locations.subdistrict') }}</span
              ><strong>{{ project()!.subdistrict_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('locations.community') }}</span
              ><strong>{{ project()!.community_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.latitude') }}</span
              ><strong>{{ coordDisplay(project()!.latitude) }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.longitude') }}</span
              ><strong>{{ coordDisplay(project()!.longitude) }}</strong>
            </div>
          </article>

          <article class="panel">
            <h3>{{ t('budget.projects.section-progress') }}</h3>
            <div class="kv">
              <span>{{ t('budget.projects.start-date') }}</span
              ><strong>{{ dateDisplay(project()!.start_date) }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.end-date') }}</span
              ><strong>{{ dateDisplay(project()!.end_date) }}</strong>
            </div>
          </article>

          <article class="panel description-panel">
            <h3>{{ t('budget.projects.description') }}</h3>
            <p>{{ descriptionText() }}</p>
            @if (isDescriptionExpandable()) {
              <button type="button" class="read-more-btn" (click)="toggleDescription()">
                {{
                  descriptionExpanded()
                    ? t('budget.projects.read-less')
                    : t('budget.projects.read-more')
                }}
              </button>
            }
          </article>
        </section>

        <section class="details-grid">
          <article class="panel">
            <h3>{{ t('budget.projects.target-policy-section') }}</h3>
            <div class="kv">
              <span>{{ t('budget.projects.target') }}</span
              ><strong>{{ project()!.target_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.policy') }}</span
              ><strong>{{ project()!.policy_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.quantitative-target-section') }}</span
              ><strong>{{ quantitativeTargetDisplay() }}</strong>
            </div>
          </article>
        </section>

        <section class="change-log-panel">
          <div class="change-log-head">
            <h3>{{ t('budget.projects.change-log-title') }}</h3>
          </div>
          @if (changeLogLoading()) {
            <p class="change-log-state">{{ t('dashboard.loading') }}</p>
          } @else if (changeLogBatches().length === 0) {
            <p class="change-log-state">{{ t('budget.projects.change-log-empty') }}</p>
          } @else {
            @for (batch of changeLogBatches(); track batch.batchId) {
              <article class="change-log-batch">
                <header class="change-log-batch-head">
                  <div class="change-log-meta">
                    <span class="change-log-action">{{ changeActionLabel(batch.action) }}</span>
                    <strong>{{ batch.userLabel }}</strong>
                    <time>{{ formatChangeDateTime(batch.changedAt) }}</time>
                  </div>
                  <div class="change-log-context">
                    @if (hasClientLocation(batch)) {
                      <button
                        type="button"
                        class="change-log-location-btn"
                        (click)="openDeviceLocationDialog(batch)"
                      >
                        <span class="material-icons" aria-hidden="true">location_on</span>
                        {{ t('budget.projects.change-log-show-location') }}
                      </button>
                    }
                    @if (batch.ipAddress) {
                      <span>{{ t('budget.projects.change-log-ip') }}: {{ batch.ipAddress }}</span>
                    }
                  </div>
                </header>
                <div class="change-log-table-wrap">
                  <table class="change-log-table">
                    <thead>
                      <tr>
                        <th>{{ t('budget.projects.change-log-field') }}</th>
                        <th>{{ t('budget.projects.change-log-before') }}</th>
                        <th>{{ t('budget.projects.change-log-after') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (row of batch.changes; track row.id) {
                        <tr>
                          <td>{{ row.field_label }}</td>
                          <td>{{ row.old_value || emptyValue() }}</td>
                          <td>{{ row.new_value || emptyValue() }}</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </article>
            }
          }
        </section>

        <section class="categories-panel">
          <div class="milestones-head">
            <div>
              <h3>{{ t('budget.projects.categories-title') }}</h3>
              <p class="categories-hint">{{ t('budget.projects.categories-view-hint') }}</p>
            </div>
            <div class="milestones-head-actions">
              <span class="milestones-count"
                >{{ milestones().length }} {{ t('budget.projects.milestones-count-label') }}</span
              >
              <button
                type="button"
                class="toggle-empty-btn"
                [class.active]="showEmptyCategories()"
                (click)="toggleEmptyCategories()"
              >
                {{
                  showEmptyCategories()
                    ? t('budget.projects.categories-hide-empty')
                    : t('budget.projects.categories-show-empty')
                }}
              </button>
            </div>
          </div>

          @if (milestonesLoading()) {
            <div class="milestones-loading">
              @for (item of [1, 2, 3]; track item) {
                <div class="milestone-skeleton"></div>
              }
            </div>
          } @else if (categorySections().length === 0 && uncategorizedMilestones().length === 0) {
            <p class="milestones-empty">{{ t('budget.projects.categories-empty-filtered') }}</p>
          } @else {
            @for (section of categorySections(); track section.prefix) {
              <div class="category-section">
                <h4 class="category-section-title">{{ section.label }}</h4>
                <div class="category-tree">
                  @for (root of section.roots; track root.id) {
                    <details class="category-branch" [open]="root.totalMilestones > 0">
                      <summary class="category-branch-summary">
                        <span class="code-badge">{{ root.code || '—' }}</span>
                        <span class="branch-name">{{ root.name }}</span>
                        <span class="branch-count">{{ root.totalMilestones }}</span>
                      </summary>
                      <div class="category-branch-body">
                        <ng-container
                          *ngTemplateOutlet="catNode; context: { $implicit: root }"
                        ></ng-container>
                      </div>
                    </details>
                  }
                </div>
              </div>
            }

            @if (uncategorizedMilestones().length > 0) {
              <div class="category-section uncategorized-section">
                <h4 class="category-section-title">{{ t('budget.projects.uncategorized') }}</h4>
                <div class="milestone-list">
                  @for (milestone of uncategorizedMilestones(); track milestone.id) {
                    <ng-container
                      *ngTemplateOutlet="milestoneItem; context: { $implicit: milestone }"
                    ></ng-container>
                  }
                </div>
              </div>
            }
          }
        </section>

        <section class="map-panel">
          <div class="map-panel-head">
            <h3>{{ t('budget.projects.map-location') }}</h3>
            @if (canOpenMap()) {
              <a class="map-link" [href]="mapExternalUrl()" target="_blank" rel="noopener">
                {{ t('budget.projects.map-open-external') }}
              </a>
            }
          </div>
          <app-form-map-picker
            [form]="mapForm"
            [readOnly]="true"
            [mapHeight]="520"
            [minMapHeight]="340"
            [label]="t('budget.projects.map-location')"
            [hint]="t('budget.projects.map-hint')"
            [latitudeLabel]="t('budget.projects.latitude')"
            [longitudeLabel]="t('budget.projects.longitude')"
            [clearLabel]="t('budget.projects.map-clear')"
            [searchPlaceholder]="t('budget.projects.map-search-placeholder')"
            [searchNoResultsLabel]="t('budget.projects.map-search-no-results')"
            [searchLoadingLabel]="t('budget.projects.map-search-loading')"
            [resetViewLabel]="t('budget.projects.map-reset-view')"
            [focusMarkerLabel]="t('budget.projects.map-focus-location')"
            [zoomLockHintLabel]="t('budget.projects.map-enable-zoom')"
            [fullscreenLabel]="t('budget.projects.map-fullscreen')"
            [exitFullscreenLabel]="t('budget.projects.map-exit-fullscreen')"
            [emptyCoordinatesLabel]="t('budget.projects.map-no-coordinates')"
          />
        </section>
      }
    </div>

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

    <ng-template #catNode let-node>
      @if (node.milestones.length > 0) {
        <div class="milestone-list">
          @for (milestone of node.milestones; track milestone.id) {
            <ng-container
              *ngTemplateOutlet="milestoneItem; context: { $implicit: milestone }"
            ></ng-container>
          }
        </div>
      }
      @for (child of node.children; track child.id) {
        <details class="category-subbranch" [open]="child.totalMilestones > 0">
          <summary class="category-subbranch-summary">
            <span class="code-badge code-badge-sm">{{ child.code || '—' }}</span>
            <span class="branch-name">{{ child.name }}</span>
            <span class="branch-count branch-count-muted">{{ child.totalMilestones }}</span>
          </summary>
          <div class="category-subbranch-body">
            <ng-container *ngTemplateOutlet="catNode; context: { $implicit: child }"></ng-container>
          </div>
        </details>
      }
      @if (node.milestones.length === 0 && node.children.length === 0) {
        <p class="branch-empty">{{ t('budget.projects.category-no-milestones') }}</p>
      }
    </ng-template>

    <ng-template #milestoneItem let-milestone>
      <article class="milestone-card">
        <div class="milestone-main">
          <div>
            <h4>{{ milestone.name_ar || emptyValue() }}</h4>
            <p>{{ milestone.name_en || emptyValue() }}</p>
          </div>
          <span class="status-badge" [ngClass]="statusClass(milestone.status)">
            {{ milestoneStatusLabel(milestone.status) }}
          </span>
        </div>

        <div class="milestone-meta">
          <span
            >{{ t('budget.milestones.responsible') }}:
            {{ milestone.responsible_name || emptyValue() }}</span
          >
          <span>{{ t('budget.milestones.order') }}: {{ milestone.order }}</span>
          <span
            >{{ t('budget.milestones.due-date') }}:
            {{ dateDisplayNullable(milestone.due_date) }}</span
          >
        </div>

        <div class="milestone-progress">
          <div class="progress-track">
            <div
              class="progress-fill"
              [style.width.%]="milestonePercent(milestone.percentage_completion)"
            ></div>
          </div>
          <strong>{{ percentDisplay(milestone.percentage_completion) }}</strong>
        </div>

        <div class="milestone-actions">
          <button type="button" class="milestone-open-btn" (click)="openMilestone(milestone.id)">
            {{ t('budget.milestones.view') }}
          </button>
        </div>
      </article>
    </ng-template>
  `,
  styleUrl: './project-view.component.scss',
})
export class ProjectViewComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private auth = inject(AuthService);
  private fb = inject(UntypedFormBuilder);

  t = (key: string) => this.translation.t(key);
  loading = signal(true);
  project = signal<Project | null>(null);
  milestones = signal<Milestone[]>([]);
  milestonesLoading = signal(false);
  categories = signal<CategorySelectOption[]>([]);
  changeLog = signal<ProjectChangeLogEntry[]>([]);
  changeLogLoading = signal(false);
  deviceLocationModalOpen = signal(false);
  descriptionExpanded = signal(false);
  showEmptyCategories = signal(false);
  skeletonItems = Array.from({ length: 7 }, (_, i) => i);

  mapForm = this.fb.group({
    latitude: [''],
    longitude: [''],
  });

  deviceLocationForm = this.fb.group({
    latitude: [''],
    longitude: [''],
  });

  backAction = {
    label: this.t('budget.projects.back-to-list'),
    icon: 'arrow_back',
    routerLink: '/budget/projects',
  };

  projectCode = computed(() => this.project()?.code || this.emptyValue());
  progressPercent = computed(() => {
    const item = this.project();
    if (!item) return 0;
    const parsed = Number(item.percentage_completion);
    if (!Number.isFinite(parsed)) return 0;
    return Math.min(100, Math.max(0, parsed));
  });

  expenditurePercent = computed(() => {
    const item = this.project();
    if (!item) return null;
    return budgetExpenditurePercent(item.approved_budget, item.budget_expenditure);
  });

  expenditurePercentDisplay = computed(() =>
    formatBudgetExpenditurePercent(this.expenditurePercent()),
  );

  expenditureProgressWidth = computed(() =>
    budgetExpenditureProgressWidth(this.expenditurePercent()),
  );

  expenditureOverBudget = computed(() => budgetExpenditureOverBudget(this.expenditurePercent()));

  remainingBudget = computed(() => {
    const item = this.project();
    if (!item) return 0;
    const approved = Number(item.approved_budget);
    const spent = Number(item.budget_expenditure);
    if (!Number.isFinite(approved) || !Number.isFinite(spent)) return 0;
    return approved - spent;
  });

  varianceClass = computed(() => (this.remainingBudget() >= 0 ? 'positive' : 'negative'));

  changeLogBatches = computed<ChangeLogBatch[]>(() => {
    const batches = new Map<string, ChangeLogBatch>();
    for (const entry of this.changeLog()) {
      let batch = batches.get(entry.batch_id);
      if (!batch) {
        batch = {
          batchId: entry.batch_id,
          action: entry.action,
          userLabel:
            entry.changed_by_name ||
            entry.changed_by_username ||
            this.t('budget.projects.value-empty'),
          changedAt: entry.changed_at,
          ipAddress: entry.ip_address,
          clientLatitude: this.parseClientCoord(entry.client_latitude),
          clientLongitude: this.parseClientCoord(entry.client_longitude),
          changes: [],
        };
        batches.set(entry.batch_id, batch);
      }
      batch.changes.push(entry);
    }
    return Array.from(batches.values());
  });

  quantitativeTargetDisplay = computed(() => {
    const item = this.project();
    if (!item) return this.emptyValue();
    const formatted = formatQuantitativeTarget(item);
    return formatted || this.emptyValue();
  });

  private milestonesByCategory = computed(() => {
    const map = new Map<number, Milestone[]>();
    for (const milestone of this.milestones()) {
      if (milestone.category == null) continue;
      const list = map.get(milestone.category) ?? [];
      list.push(milestone);
      map.set(milestone.category, list);
    }
    return map;
  });

  private categoryMetaById = computed(() => {
    const map = new Map<number, CategorySelectOption>();
    for (const category of this.categories()) {
      map.set(category.id, category);
    }
    return map;
  });

  categoryTree = computed<ProjectCategoryNode[]>(() => {
    const byParent = new Map<number | null, CategorySelectOption[]>();
    for (const category of this.categories()) {
      const key = category.parent ?? null;
      const list = byParent.get(key) ?? [];
      list.push(category);
      byParent.set(key, list);
    }
    const milestonesByCategory = this.milestonesByCategory();
    const metaById = this.categoryMetaById();

    const build = (parentId: number | null): ProjectCategoryNode[] =>
      (byParent.get(parentId) ?? []).map((category) => {
        const children = build(category.id);
        const milestones = milestonesByCategory.get(category.id) ?? [];
        const totalMilestones =
          milestones.length + children.reduce((sum, child) => sum + child.totalMilestones, 0);
        return {
          id: category.id,
          code: metaById.get(category.id)?.code ?? '',
          name: category.name || String(category.id),
          milestones,
          children,
          totalMilestones,
        };
      });

    return build(null);
  });

  categorySections = computed(() => {
    const showEmpty = this.showEmptyCategories();
    const typePrefix = projectTypeCategoryPrefix(this.project()?.project_type_name ?? '');
    const sections = typePrefix
      ? CATEGORY_SECTIONS.filter((section) => section.prefix === typePrefix)
      : CATEGORY_SECTIONS;
    const roots = this.categoryTree()
      .map((node) => this.filterCategoryNode(node, showEmpty))
      .filter((node): node is ProjectCategoryNode => node !== null);

    return sections
      .map((section) => ({
        prefix: section.prefix,
        label: this.t(section.labelKey),
        roots: roots.filter((root) => root.code.startsWith(section.prefix)),
      }))
      .filter((section) => showEmpty || section.roots.length > 0);
  });

  uncategorizedMilestones = computed(() =>
    this.milestones().filter((milestone) => milestone.category == null),
  );

  isDescriptionExpandable = computed(() => {
    const text = this.project()?.description?.trim() || '';
    return text.length > 220;
  });

  descriptionText = computed(() => {
    const text = this.project()?.description?.trim();
    if (!text) return this.t('budget.projects.value-empty');
    if (this.descriptionExpanded() || text.length <= 220) return text;
    return `${text.slice(0, 220)}...`;
  });

  canOpenMap = computed(() => {
    const item = this.project();
    if (!item) return false;
    return this.coordNumeric(item.latitude) != null && this.coordNumeric(item.longitude) != null;
  });

  mapExternalUrl = computed(() => {
    const item = this.project();
    if (!item) return '#';
    const lat = this.coordNumeric(item.latitude);
    const lng = this.coordNumeric(item.longitude);
    if (lat == null || lng == null) return '#';
    return `https://www.google.com/maps?q=${lat},${lng}`;
  });

  headerActions = computed<PageHeaderAction[]>(() => {
    const actions: PageHeaderAction[] = [
      {
        label: this.t('budget.projects.print'),
        icon: 'print',
        variant: 'ghost',
        click: () => this.printPage(),
      },
    ];
    const item = this.project();
    if (item && this.auth.canWriteBudget()) {
      actions.push({
        label: this.t('common.edit'),
        icon: 'edit',
        variant: 'secondary',
        routerLink: `/budget/projects/${item.id}/edit`,
      });
    }
    return actions;
  });

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const id = Number(idParam);
    if (!idParam || Number.isNaN(id)) {
      this.loading.set(false);
      this.router.navigate(['/budget/projects']);
      return;
    }

    this.budget.getProject(id).subscribe({
      next: (project) => {
        this.project.set(project);
        this.descriptionExpanded.set(false);
        this.mapForm.patchValue({
          latitude: project.latitude ?? '',
          longitude: project.longitude ?? '',
        });
        this.budget.listCategoryOptions({ project_type: project.project_type_id }).subscribe({
          next: (data) => this.categories.set(data),
        });
        this.loading.set(false);
        this.loadChangeLog(id);
      },
      error: () => {
        this.toast.error(this.t('budget.projects.load-error'));
        this.loading.set(false);
        this.router.navigate(['/budget/projects']);
      },
    });
    this.loadMilestones(id);
  }

  changeActionLabel(action: ProjectChangeLogEntry['action']): string {
    if (action === 'create') return this.t('budget.projects.change-log-action-create');
    if (action === 'delete') return this.t('budget.projects.change-log-action-delete');
    return this.t('budget.projects.change-log-action-update');
  }

  formatChangeDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date);
  }

  hasClientLocation(batch: ChangeLogBatch): boolean {
    return batch.clientLatitude != null && batch.clientLongitude != null;
  }

  openDeviceLocationDialog(batch: ChangeLogBatch): void {
    if (!this.hasClientLocation(batch)) return;
    this.deviceLocationForm.patchValue({
      latitude: batch.clientLatitude,
      longitude: batch.clientLongitude,
    });
    this.deviceLocationModalOpen.set(true);
  }

  closeDeviceLocationDialog(): void {
    this.deviceLocationModalOpen.set(false);
  }

  private parseClientCoord(value: string | number | null): number | null {
    if (value == null || value === '') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  private loadChangeLog(projectId: number): void {
    this.changeLogLoading.set(true);
    this.budget.listProjectChangeLog(projectId, { page_size: 200 }).subscribe({
      next: (data) => {
        this.changeLog.set(data.results);
        this.changeLogLoading.set(false);
      },
      error: () => {
        this.changeLog.set([]);
        this.changeLogLoading.set(false);
      },
    });
  }

  statusLabel(status: ProjectStatus): string {
    return this.t(`budget.projects.status.${status}`);
  }

  statusClass(status: ProjectStatus): string {
    return `status-${status}`;
  }

  milestoneStatusLabel(status: ProjectStatus): string {
    return this.t(`budget.milestones.status.${status}`);
  }

  emptyValue(): string {
    return this.t('budget.projects.value-empty');
  }

  numberDisplay(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return this.emptyValue();
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(parsed);
  }

  moneyDisplay(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return this.emptyValue();
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(parsed);
  }

  percentDisplay(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return this.emptyValue();
    return `${parsed.toFixed(0)}%`;
  }

  coordDisplay(value: string | number | null): string {
    if (value == null || value === '') return this.emptyValue();
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return this.emptyValue();
    return parsed.toFixed(8);
  }

  dateDisplay(value: string): string {
    if (!value) return this.emptyValue();
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return this.emptyValue();
    return parsed.toLocaleDateString();
  }

  dateDisplayNullable(value: string | null): string {
    if (!value) return this.emptyValue();
    return this.dateDisplay(value);
  }

  milestonePercent(value: string | number): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return 0;
    return Math.min(100, Math.max(0, parsed));
  }

  toggleDescription(): void {
    this.descriptionExpanded.update((value) => !value);
  }

  toggleEmptyCategories(): void {
    this.showEmptyCategories.update((value) => !value);
  }

  private filterCategoryNode(
    node: ProjectCategoryNode,
    showEmpty: boolean,
  ): ProjectCategoryNode | null {
    const children = node.children
      .map((child) => this.filterCategoryNode(child, showEmpty))
      .filter((child): child is ProjectCategoryNode => child !== null);
    const hasContent = node.milestones.length > 0 || children.length > 0;
    if (!showEmpty && !hasContent) {
      return null;
    }
    return { ...node, children };
  }

  private coordNumeric(value: string | number | null): number | null {
    if (value == null || value === '') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  private printPage(): void {
    window.print();
  }

  private loadMilestones(projectId: number): void {
    this.milestonesLoading.set(true);
    this.budget.listMilestones({ project: projectId, page_size: 500 }).subscribe({
      next: (data) => {
        this.milestones.set(data.results);
        this.milestonesLoading.set(false);
      },
      error: () => {
        this.milestones.set([]);
        this.milestonesLoading.set(false);
      },
    });
  }

  openMilestone(id: number): void {
    this.router.navigate(['/budget/milestones', id, 'view']);
  }
}
