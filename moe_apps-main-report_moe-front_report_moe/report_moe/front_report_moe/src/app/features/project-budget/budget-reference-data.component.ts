import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import {
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { type Observable } from 'rxjs';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormReadonlyMetricComponent } from '../../shared/components/form-readonly-metric/form-readonly-metric.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import type { TableColumn } from '../../shared/components/data-table/data-table.component';
import { ToastService } from '../../shared/services/toast.service';
import { DialogService } from '../../shared/services/dialog.service';
import { TranslationService } from '../../shared/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import { FilterState } from '../../shared/utils/filter-state';
import type {
  BudgetReferencePayload,
  BudgetReferenceType,
  BudgetSelectOption,
} from './project-budget.models';
import { ProjectBudgetService, type BudgetReferenceEntity } from './project-budget.service';
import { BUDGET_REFERENCE_TABS } from './budget-reference-tabs';

type FieldType = 'text' | 'email' | 'number' | 'select';
type ReferenceFieldKey = keyof BudgetReferencePayload | 'name';

interface ReferenceField {
  key: ReferenceFieldKey;
  labelKey: string;
  type: FieldType;
  required?: boolean;
  optionsKey?: 'categories' | 'foundations';
}

type ReferenceRow = { id: number; [key: string]: unknown };

interface CategoryNode {
  id: number;
  code: string;
  name_ar: string;
  name_en: string;
  parent: number | null;
  children: CategoryNode[];
}

interface ReferenceConfig {
  type: BudgetReferenceType;
  titleKey: string;
  descriptionKey: string;
  endpointLabelKey: string;
  columns: TableColumn[];
  fields: ReferenceField[];
}

@Component({
  selector: 'app-budget-reference-data',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    RouterLinkActive,
    ListPageComponent,
    ModalComponent,
    FormInputComponent,
    FormReadonlyMetricComponent,
    FormSelectComponent,
    ButtonComponent,
  ],
  template: `
    <div class="page-shell">
      <nav
        class="reference-tabs"
        aria-label="Budget reference data"
        *ngIf="referenceTabs().length > 1"
      >
        <a
          *ngFor="let tab of referenceTabs()"
          class="reference-tab"
          [routerLink]="['/budget/reference-data', tab.type]"
          routerLinkActive="active"
          [routerLinkActiveOptions]="{ exact: true }"
        >
          {{ t(tab.labelKey) }}
        </a>
      </nav>

      <ng-container *ngIf="currentType() === 'categories'; else listView">
        <div class="cat-panel">
          <div class="cat-chrome">
            <div class="cat-head">
              <div class="cat-head-text">
                <h2 class="cat-head-title">{{ t(activeConfig().titleKey) }}</h2>
                <p class="cat-head-desc">{{ t(activeConfig().descriptionKey) }}</p>
              </div>
              <div class="cat-head-actions">
                <button type="button" class="cat-tool" (click)="expandAllCategories()">
                  {{ t('budget.reference.expand-all') }}
                </button>
                <button type="button" class="cat-tool" (click)="collapseAllCategories()">
                  {{ t('budget.reference.collapse-all') }}
                </button>
                <app-button
                  *ngIf="canWriteCurrentTab()"
                  variant="primary"
                  icon="add"
                  [label]="t('budget.reference.add') + ' ' + t('budget.reference.category')"
                  (clicked)="openCreateCategory(null)"
                />
              </div>
            </div>

            <div class="cat-search">
              <input
                type="text"
                class="cat-search-input"
                [placeholder]="t('budget.reference.search')"
                [value]="categorySearch()"
                (input)="onCategorySearch($any($event.target).value)"
              />
            </div>
          </div>

          <div class="cat-tree" *ngIf="!fs.loading(); else catLoading">
            <ng-container *ngIf="categorySections().length; else catEmpty">
              <div class="cat-section" *ngFor="let section of categorySections()">
                <div class="cat-section-head">
                  <span class="cat-section-code">{{ section.prefix }}</span>
                  <span class="cat-section-title">{{ section.label }}</span>
                  <span class="cat-section-count">{{ section.roots.length }}</span>
                </div>
                <ng-container *ngFor="let node of section.roots">
                  <ng-container
                    *ngTemplateOutlet="catNode; context: { $implicit: node, level: 0 }"
                  ></ng-container>
                </ng-container>
              </div>
            </ng-container>
          </div>

          <ng-template #catLoading>
            <div class="cat-state">{{ t('dashboard.loading') }}</div>
          </ng-template>
          <ng-template #catEmpty>
            <div class="cat-state">{{ t('budget.reference.empty') }}</div>
          </ng-template>
        </div>

        <ng-template #catNode let-node let-level="level">
          <div class="cat-row" [style.padding-inline-start.px]="10 + level * 24">
            <button
              *ngIf="node.children.length"
              type="button"
              class="cat-chevron"
              [class.is-open]="isCategoryExpanded(node.id)"
              (click)="toggleCategory(node.id)"
              [attr.aria-label]="isCategoryExpanded(node.id) ? 'collapse' : 'expand'"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                <path
                  d="M9 6l6 6-6 6"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>
            <span *ngIf="!node.children.length" class="cat-chevron-spacer"></span>

            <span *ngIf="node.code" class="cat-code">{{ node.code }}</span>
            <span class="cat-name">{{ node.name_ar }}</span>
            <span *ngIf="node.name_en" class="cat-name-en">{{ node.name_en }}</span>
            <span *ngIf="node.children.length" class="cat-badge">{{ node.children.length }}</span>

            <span class="cat-row-actions" *ngIf="canWriteCurrentTab()">
              <button
                type="button"
                class="cat-act"
                [title]="t('budget.reference.add-child')"
                (click)="openCreateCategory(node.id)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                  <path
                    d="M12 5v14M5 12h14"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
              <button
                type="button"
                class="cat-act"
                [title]="t('common.edit')"
                (click)="openEditCategory(node)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                  <path
                    d="M4 20h4L18 10l-4-4L4 16v4zM14 6l4 4"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
              <button
                type="button"
                class="cat-act cat-act--danger"
                [title]="t('common.delete')"
                (click)="deleteCategory(node)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                  <path
                    d="M5 7h14M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </button>
            </span>
          </div>

          <ng-container *ngIf="isCategoryExpanded(node.id)">
            <ng-container *ngFor="let child of node.children">
              <ng-container
                *ngTemplateOutlet="catNode; context: { $implicit: child, level: level + 1 }"
              ></ng-container>
            </ng-container>
          </ng-container>
        </ng-template>
      </ng-container>

      <ng-template #listView>
        <app-list-page
          [config]="pageConfig()"
          (onSearch)="fs.onSearch($event)"
          (onPrevious)="fs.previousPage()"
          (onNext)="fs.nextPage()"
          (onGoToPage)="fs.goToPage($event)"
          (onClearFilters)="fs.clearFilters()"
        ></app-list-page>
      </ng-template>

      <app-modal
        [visible]="modalOpen()"
        [title]="modalTitle()"
        size="medium"
        (close)="closeModal()"
      >
        <form class="reference-form" [formGroup]="form" (ngSubmit)="save()">
          <ng-container *ngFor="let field of activeConfig().fields">
            <app-form-readonly-metric
              *ngIf="field.key === 'foundation' && isResponsibleFoundationLocked()"
              [label]="t(field.labelKey)"
              [value]="lockedFoundationLabel()"
            />
            <app-form-select
              *ngIf="
                field.type === 'select' &&
                !(field.key === 'foundation' && isResponsibleFoundationLocked())
              "
              [label]="t(field.labelKey)"
              [placeholder]="t('budget.reference.select-placeholder')"
              [required]="!!field.required"
              [options]="optionsFor(field)"
              [formControlName]="field.key"
            />

            <app-form-input
              *ngIf="field.type !== 'select'"
              [label]="t(field.labelKey)"
              [type]="inputType(field)"
              [required]="!!field.required"
              [formControlName]="field.key"
            />
          </ng-container>
        </form>

        <div footer class="reference-actions">
          <app-button variant="ghost" [label]="t('common.cancel')" (clicked)="closeModal()" />
          <app-button
            variant="primary"
            icon="save"
            [label]="t('common.save')"
            [disabled]="form.invalid || saving()"
            [loading]="saving()"
            (clicked)="save()"
          />
        </div>
      </app-modal>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        height: 100%;
        min-height: 0;
      }

      .page-shell {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
        overflow: hidden;
      }

      .reference-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e5e7eb;
        flex-shrink: 0;
        position: sticky;
        top: 0;
        z-index: 4;
        background: #f9fafb;
      }

      .reference-tab {
        display: inline-flex;
        align-items: center;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.875rem;
        font-weight: 500;
        color: #4b5563;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        transition:
          background-color 0.15s ease,
          color 0.15s ease,
          border-color 0.15s ease;
      }

      .reference-tab:hover {
        background: #f5f0e8;
        color: #1f2937;
      }

      .reference-tab.active {
        background: #f5f0e8;
        color: #054239;
        border-color: #b9a779;
        font-weight: 600;
      }

      .reference-form {
        display: grid;
        gap: 14px;
      }

      .reference-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
      }

      .cat-panel {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        flex: 1 1 auto;
        min-height: 0;
        display: flex;
        flex-direction: column;
      }

      .cat-chrome {
        flex-shrink: 0;
        position: sticky;
        top: 0;
        z-index: 3;
        background: #fff;
      }

      .cat-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        padding: 16px 18px;
        border-bottom: 1px solid #eef0f2;
      }

      .cat-head-title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: #1f2937;
      }

      .cat-head-desc {
        margin: 4px 0 0;
        font-size: 0.85rem;
        color: #6b7280;
      }

      .cat-head-actions {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
      }

      .cat-tool {
        padding: 7px 12px;
        font-size: 0.8125rem;
        font-weight: 500;
        color: #4b5563;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s ease;
      }

      .cat-tool:hover {
        background: #f5f0e8;
        color: #054239;
        border-color: #b9a779;
      }

      .cat-search {
        padding: 12px 18px;
        border-bottom: 1px solid #eef0f2;
      }

      .cat-search-input {
        width: 100%;
        padding: 9px 12px;
        font-size: 0.875rem;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        outline: none;
        transition:
          border-color 0.15s ease,
          box-shadow 0.15s ease;
      }

      .cat-search-input:focus {
        border-color: #b9a779;
        box-shadow: 0 0 0 3px rgba(185, 167, 121, 0.2);
      }

      .cat-tree {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        padding: 6px 0;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior: contain;
      }

      .page-shell > app-list-page {
        flex: 1 1 auto;
        min-height: 0;
      }

      .cat-state {
        padding: 28px;
        text-align: center;
        color: #9ca3af;
        font-size: 0.9rem;
      }

      .cat-section + .cat-section {
        margin-top: 6px;
      }

      .cat-section-head {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 16px;
        background: #f5f0e8;
        border-top: 1px solid #ece3d3;
        border-bottom: 1px solid #ece3d3;
        position: sticky;
        top: 0;
        z-index: 1;
      }

      .cat-section:first-child .cat-section-head {
        border-top: none;
      }

      .cat-section-code {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 34px;
        padding: 3px 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.75rem;
        font-weight: 700;
        color: #fff;
        background: linear-gradient(135deg, #054239 0%, #0a5c4f 100%);
        border-radius: 6px;
      }

      .cat-section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #353233;
      }

      .cat-section-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        height: 20px;
        padding: 0 6px;
        margin-inline-start: auto;
        font-size: 0.7rem;
        font-weight: 700;
        color: #054239;
        background: #fff;
        border: 1px solid #e3d6bf;
        border-radius: 999px;
      }

      .cat-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 7px 14px;
        border-bottom: 1px solid #f5f6f7;
        transition: background 0.12s ease;
      }

      .cat-row:hover {
        background: #faf8f3;
      }

      .cat-chevron {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border: none;
        background: transparent;
        color: #9ca3af;
        cursor: pointer;
        border-radius: 6px;
        transition:
          transform 0.15s ease,
          color 0.15s ease,
          background 0.15s ease;
      }

      .cat-chevron:hover {
        background: #f1ece2;
        color: #054239;
      }

      .cat-chevron.is-open {
        transform: rotate(90deg);
        color: #054239;
      }

      [dir='rtl'] .cat-chevron svg {
        transform: scaleX(-1);
      }

      [dir='rtl'] .cat-chevron.is-open {
        transform: rotate(90deg);
      }

      .cat-chevron-spacer {
        display: inline-block;
        width: 22px;
        height: 22px;
      }

      .cat-code {
        display: inline-flex;
        align-items: center;
        min-width: 52px;
        justify-content: center;
        padding: 3px 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.75rem;
        font-weight: 700;
        color: #4a5530;
        background: linear-gradient(135deg, #eef1e8 0%, #dde4d0 100%);
        border: 1px solid #7d8f52;
        border-radius: 6px;
      }

      .cat-name {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1f2937;
      }

      .cat-name-en {
        font-size: 0.8rem;
        color: #9ca3af;
        direction: ltr;
      }

      .cat-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        height: 20px;
        padding: 0 6px;
        font-size: 0.7rem;
        font-weight: 700;
        color: #6b7280;
        background: #f3f4f6;
        border-radius: 999px;
      }

      .cat-row-actions {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        margin-inline-start: auto;
        opacity: 0;
        transition: opacity 0.12s ease;
      }

      .cat-row:hover .cat-row-actions {
        opacity: 1;
      }

      .cat-act {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border: none;
        background: transparent;
        color: #6b7280;
        border-radius: 7px;
        cursor: pointer;
        transition: all 0.12s ease;
      }

      .cat-act:hover {
        background: #f1ece2;
        color: #054239;
      }

      .cat-act--danger:hover {
        background: #fee2e2;
        color: #b91c1c;
      }
    `,
  ],
})
export class BudgetReferenceDataComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(UntypedFormBuilder);
  private toast = inject(ToastService);
  private confirmDialog = inject(DialogService);
  private translation = inject(TranslationService);
  private auth = inject(AuthService);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), 'search');

  referenceTabs = computed(() => {
    const user = this.auth.currentUser();
    if (user?.is_admin || user?.can_manage_reference_data) {
      return BUDGET_REFERENCE_TABS;
    }
    if (user?.can_manage_budget) {
      return BUDGET_REFERENCE_TABS.filter((tab) => tab.type === 'responsibles');
    }
    return [];
  });

  canWriteCurrentTab = computed(() => {
    const user = this.auth.currentUser();
    if (!user) return false;
    if (user.is_admin || user.can_manage_reference_data) return true;
    return user.can_manage_budget && this.currentType() === 'responsibles';
  });

  isResponsibleFoundationLocked = computed(() => {
    const user = this.auth.currentUser();
    return (
      this.currentType() === 'responsibles' &&
      !!user &&
      !user.is_admin &&
      user.foundation_id != null
    );
  });

  lockedFoundationLabel = computed(() => {
    const user = this.auth.currentUser();
    const id = user?.foundation_id;
    if (id == null) return '—';
    const fromList = this.foundations().find((item) => item.id === id)?.name;
    return fromList || user?.foundation_name || String(id);
  });

  rows = signal<ReferenceRow[]>([]);

  categoriesRaw = signal<ReferenceRow[]>([]);
  categorySearch = signal('');
  expandedCategoryIds = signal<Set<number>>(new Set<number>());

  categoryTree = computed<CategoryNode[]>(() => this.buildCategoryTree(this.categoriesRaw()));

  visibleCategoryTree = computed<CategoryNode[]>(() => {
    const query = this.categorySearch().trim().toLowerCase();
    if (!query) return this.categoryTree();

    const matches = (node: CategoryNode): boolean =>
      node.name_ar.toLowerCase().includes(query) ||
      node.name_en.toLowerCase().includes(query) ||
      node.code.toLowerCase().includes(query);

    const prune = (nodes: CategoryNode[]): CategoryNode[] => {
      const out: CategoryNode[] = [];
      for (const node of nodes) {
        const children = prune(node.children);
        if (matches(node) || children.length) {
          out.push({ ...node, children });
        }
      }
      return out;
    };
    return prune(this.categoryTree());
  });

  private readonly categorySectionDefs = [
    { prefix: '31', labelKey: 'budget.projects.category-section-new' },
    { prefix: '32', labelKey: 'budget.projects.category-section-ongoing' },
    { prefix: '33', labelKey: 'budget.projects.category-section-renewal' },
  ];

  categorySections = computed(() => {
    const tree = this.visibleCategoryTree();
    const known = new Set<number>();
    const sections = this.categorySectionDefs
      .map((def) => {
        const roots = tree.filter((node) => node.code.startsWith(def.prefix));
        roots.forEach((root) => known.add(root.id));
        return { prefix: def.prefix, label: this.t(def.labelKey), roots };
      })
      .filter((section) => section.roots.length > 0);

    const other = tree.filter((node) => !known.has(node.id));
    if (other.length) {
      sections.push({
        prefix: 'other',
        label: this.t('budget.projects.uncategorized'),
        roots: other,
      });
    }
    return sections;
  });
  modalOpen = signal(false);
  saving = signal(false);
  editing = signal<ReferenceRow | null>(null);
  currentType = signal<BudgetReferenceType>('categories');
  categories = signal<BudgetSelectOption[]>([]);
  foundations = signal<BudgetSelectOption[]>([]);

  form: UntypedFormGroup = this.fb.group({});

  readonly configs: Record<BudgetReferenceType, ReferenceConfig> = {
    categories: {
      type: 'categories',
      titleKey: 'budget.reference.categories',
      descriptionKey: 'budget.reference.categories-desc',
      endpointLabelKey: 'budget.reference.category',
      columns: [
        { key: 'tree_name', label: this.t('budget.fields.name-ar'), sortable: false },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
        { key: 'parent_name', label: this.t('budget.fields.parent') },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        {
          key: 'parent',
          labelKey: 'budget.fields.parent',
          type: 'select',
          optionsKey: 'categories',
        },
      ],
    },
    foundations: {
      type: 'foundations',
      titleKey: 'budget.reference.foundations',
      descriptionKey: 'budget.reference.foundations-desc',
      endpointLabelKey: 'budget.reference.foundation',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
      ],
    },
    responsibles: {
      type: 'responsibles',
      titleKey: 'budget.reference.responsibles',
      descriptionKey: 'budget.reference.responsibles-desc',
      endpointLabelKey: 'budget.reference.responsible',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'foundation_name', label: this.t('budget.fields.foundation') },
        { key: 'phone', label: this.t('budget.fields.phone') },
        { key: 'email', label: this.t('budget.fields.email') },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        {
          key: 'foundation',
          labelKey: 'budget.fields.foundation',
          type: 'select',
          required: true,
          optionsKey: 'foundations',
        },
        { key: 'phone', labelKey: 'budget.fields.phone', type: 'text' },
        { key: 'email', labelKey: 'budget.fields.email', type: 'email' },
      ],
    },
    'project-types': {
      type: 'project-types',
      titleKey: 'budget.reference.project-types',
      descriptionKey: 'budget.reference.project-types-desc',
      endpointLabelKey: 'budget.reference.project-type',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
      ],
    },
    targets: {
      type: 'targets',
      titleKey: 'budget.reference.targets',
      descriptionKey: 'budget.reference.targets-desc',
      endpointLabelKey: 'budget.reference.target',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
        { key: 'description', label: this.t('budget.fields.description') },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        { key: 'description', labelKey: 'budget.fields.description', type: 'text' },
      ],
    },
    policies: {
      type: 'policies',
      titleKey: 'budget.reference.policies',
      descriptionKey: 'budget.reference.policies-desc',
      endpointLabelKey: 'budget.reference.policy',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
        { key: 'description', label: this.t('budget.fields.description') },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        { key: 'description', labelKey: 'budget.fields.description', type: 'text' },
      ],
    },
    'measure-units': {
      type: 'measure-units',
      titleKey: 'budget.reference.measure-units',
      descriptionKey: 'budget.reference.measure-units-desc',
      endpointLabelKey: 'budget.reference.measure-unit',
      columns: [
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'name_en', label: this.t('budget.fields.name-en'), sortable: true },
        { key: 'symbol', label: this.t('budget.fields.symbol') },
      ],
      fields: [
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        { key: 'symbol', labelKey: 'budget.fields.symbol', type: 'text' },
      ],
    },
    currencies: {
      type: 'currencies',
      titleKey: 'budget.reference.currencies',
      descriptionKey: 'budget.reference.currencies-desc',
      endpointLabelKey: 'budget.reference.currency',
      columns: [
        { key: 'code', label: this.t('budget.fields.code'), sortable: true },
        { key: 'name_ar', label: this.t('budget.fields.name-ar'), sortable: true },
        { key: 'symbol', label: this.t('budget.fields.symbol') },
        { key: 'exchange_rate', label: this.t('budget.fields.exchange-rate') },
      ],
      fields: [
        { key: 'code', labelKey: 'budget.fields.code', type: 'text', required: true },
        { key: 'name_ar', labelKey: 'budget.fields.name-ar', type: 'text', required: true },
        { key: 'name_en', labelKey: 'budget.fields.name-en', type: 'text' },
        { key: 'symbol', labelKey: 'budget.fields.symbol', type: 'text' },
        {
          key: 'exchange_rate',
          labelKey: 'budget.fields.exchange-rate',
          type: 'number',
          required: true,
        },
      ],
    },
  };

  activeConfig = computed(() => this.configs[this.currentType()]);

  modalTitle = computed(() => {
    const mode = this.editing() ? 'budget.reference.edit' : 'budget.reference.add';
    return `${this.t(mode)} ${this.t(this.activeConfig().endpointLabelKey)}`;
  });

  actions = computed(() =>
    this.canWriteCurrentTab()
      ? [
          {
            icon: 'edit',
            label: this.t('common.edit'),
            action: (id: number) => this.openEdit(id),
          },
          {
            icon: 'delete',
            label: this.t('common.delete'),
            action: (id: number) => this.delete(id),
          },
        ]
      : [],
  );

  pageConfig = computed(() => ({
    title: this.t(this.activeConfig().titleKey),
    description: this.t(this.activeConfig().descriptionKey),
    headerAction: this.canWriteCurrentTab()
      ? {
          label: `${this.t('budget.reference.add')} ${this.t(this.activeConfig().endpointLabelKey)}`,
          icon: 'add',
          click: () => this.openCreate(),
        }
      : undefined,
    searchPlaceholder: this.t('budget.reference.search'),
    filterGroups: [],
    columns: this.activeConfig().columns,
    data: this.rows(),
    actions: this.actions(),
    loading: this.fs.loading(),
    currentPage: this.fs.currentPage(),
    totalPages: this.fs.totalPages(),
    totalItems: this.fs.totalCount(),
    pageSize: this.fs.pageSize(),
    emptyMessage: this.t('budget.reference.empty'),
  }));

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const type = (params.get('type') || 'categories') as BudgetReferenceType;
      const user = this.auth.currentUser();
      if (
        !user?.is_admin &&
        !user?.can_manage_reference_data &&
        user?.can_manage_budget &&
        type !== 'responsibles'
      ) {
        this.router.navigate(['/budget/reference-data', 'responsibles']);
        return;
      }
      if (!this.configs[type]) {
        this.router.navigate(['/budget/reference-data', 'categories']);
        return;
      }
      this.currentType.set(type);
      this.categorySearch.set('');
      this.fs.currentPage.set(1);
      this.rebuildForm();
      this.loadDependencies();
      this.load();
    });
  }

  load(): void {
    this.fs.loading.set(true);
    const type = this.currentType();

    if (type === 'categories') {
      this.budget.list<BudgetReferenceEntity>('categories', { page_size: 1000 }).subscribe({
        next: (data) => {
          const results = data.results as unknown as ReferenceRow[];
          this.categoriesRaw.set(results);
          if (this.expandedCategoryIds().size === 0) {
            this.expandedCategoryIds.set(new Set(this.categoryTree().map((node) => node.id)));
          }
          this.fs.loading.set(false);
        },
        error: () => {
          this.toast.error(this.t('budget.reference.load-error'));
          this.fs.loading.set(false);
        },
      });
      return;
    }

    this.budget.list<BudgetReferenceEntity>(type, this.fs.params).subscribe({
      next: (data) => {
        this.rows.set(data.results as unknown as ReferenceRow[]);
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.reference.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  openCreate(): void {
    this.editing.set(null);
    this.rebuildForm();
    this.loadCategoryOptions();
    this.modalOpen.set(true);
  }

  openEdit(id: number): void {
    const row = this.rows().find((item) => item.id === id);
    if (!row) return;
    this.editing.set(row);
    this.rebuildForm(row);
    this.loadCategoryOptions(id);
    this.modalOpen.set(true);
  }

  closeModal(): void {
    this.modalOpen.set(false);
    this.editing.set(null);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const type = this.currentType();
    const current = this.editing();
    this.saving.set(true);

    const payload = this.normalizePayload(this.form.getRawValue() as Record<string, unknown>);
    const request = current
      ? this.budget.update(type, current.id, payload)
      : this.budget.create(type, payload);
    this.persist(request);
  }

  async delete(id: number): Promise<void> {
    const confirmed = await this.confirmDialog.confirm({
      title: this.t('user-data.delete-confirm-title'),
      message: this.t('budget.reference.confirm-delete'),
      type: 'error',
      icon: 'delete',
      confirmLabel: this.t('common.delete'),
      cancelLabel: this.t('common.cancel'),
    });
    if (!confirmed) return;
    const type = this.currentType();

    this.budget.delete(type, id).subscribe({
      next: () => this.afterDelete(),
      error: () => this.toast.error(this.t('budget.reference.delete-error')),
    });
  }

  private persist(request: Observable<unknown>): void {
    request.subscribe({
      next: () => {
        this.toast.success(this.t('budget.reference.save-success'));
        this.saving.set(false);
        this.closeModal();
        this.load();
        this.loadDependencies();
      },
      error: () => {
        this.toast.error(this.t('budget.reference.save-error'));
        this.saving.set(false);
      },
    });
  }

  private afterDelete(): void {
    this.toast.success(this.t('budget.reference.delete-success'));
    this.load();
    this.loadDependencies();
  }

  private buildCategoryTree(rows: ReferenceRow[]): CategoryNode[] {
    const nodes = new Map<number, CategoryNode>();
    for (const row of rows) {
      const id = row['id'] as number;
      nodes.set(id, {
        id,
        code: String(row['code'] ?? ''),
        name_ar: String(row['name_ar'] ?? ''),
        name_en: String(row['name_en'] ?? ''),
        parent: (row['parent'] as number | null) ?? null,
        children: [],
      });
    }

    const roots: CategoryNode[] = [];
    for (const node of nodes.values()) {
      if (node.parent != null && nodes.has(node.parent)) {
        nodes.get(node.parent)!.children.push(node);
      } else {
        roots.push(node);
      }
    }

    const sortRecursive = (list: CategoryNode[]): void => {
      list.sort((left, right) =>
        (left.code || left.name_ar).localeCompare(right.code || right.name_ar, 'ar', {
          numeric: true,
        }),
      );
      list.forEach((node) => sortRecursive(node.children));
    };
    sortRecursive(roots);
    return roots;
  }

  isCategoryExpanded(id: number): boolean {
    if (this.categorySearch().trim()) return true;
    return this.expandedCategoryIds().has(id);
  }

  toggleCategory(id: number): void {
    const next = new Set(this.expandedCategoryIds());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.expandedCategoryIds.set(next);
  }

  expandAllCategories(): void {
    const ids = new Set<number>();
    const walk = (nodes: CategoryNode[]): void => {
      for (const node of nodes) {
        if (node.children.length) ids.add(node.id);
        walk(node.children);
      }
    };
    walk(this.categoryTree());
    this.expandedCategoryIds.set(ids);
  }

  collapseAllCategories(): void {
    this.expandedCategoryIds.set(new Set<number>());
  }

  onCategorySearch(query: string): void {
    this.categorySearch.set(query);
  }

  openCreateCategory(parentId: number | null): void {
    this.editing.set(null);
    this.rebuildForm();
    this.loadCategoryOptions();
    if (parentId != null) {
      this.form.patchValue({ parent: parentId });
    }
    this.modalOpen.set(true);
  }

  openEditCategory(node: CategoryNode): void {
    const row: ReferenceRow = {
      id: node.id,
      name_ar: node.name_ar,
      name_en: node.name_en,
      parent: node.parent,
      code: node.code,
    };
    this.editing.set(row);
    this.rebuildForm(row);
    this.loadCategoryOptions(node.id);
    this.modalOpen.set(true);
  }

  deleteCategory(node: CategoryNode): void {
    this.delete(node.id);
  }

  optionsFor(field: ReferenceField): SelectOption[] {
    if (field.optionsKey === 'categories') {
      return this.categories().map((item) => ({
        value: item.id,
        label: item.name || String(item.id),
      }));
    }
    if (field.optionsKey === 'foundations') {
      return this.foundations().map((item) => ({
        value: item.id,
        label: item.name || String(item.id),
      }));
    }
    return [];
  }

  inputType(field: ReferenceField): 'text' | 'email' | 'number' {
    return field.type === 'email' || field.type === 'number' ? field.type : 'text';
  }

  private rebuildForm(row?: ReferenceRow): void {
    const controls: Record<string, unknown[]> = {};
    for (const field of this.activeConfig().fields) {
      let value = row ? (row[field.key] ?? null) : null;
      if (field.key === 'foundation' && this.isResponsibleFoundationLocked() && value == null) {
        value = this.auth.currentUser()?.foundation_id ?? null;
      }
      controls[field.key] = [value ?? '', field.required ? Validators.required : []];
    }
    this.form = this.fb.group(controls);
    this.applyLockedResponsibleFoundation();
  }

  private applyLockedResponsibleFoundation(): void {
    if (!this.isResponsibleFoundationLocked()) return;
    const foundationId = this.auth.currentUser()?.foundation_id;
    if (foundationId == null) return;
    const control = this.form.get('foundation');
    if (!control) return;
    control.setValue(foundationId, { emitEvent: false });
    control.disable({ emitEvent: false });
  }

  private loadCategoryOptions(excludeId?: number): void {
    const params = excludeId != null ? { exclude: excludeId } : undefined;
    this.budget.listSelectOptions('categories', params).subscribe({
      next: (data) => this.categories.set(data),
    });
  }

  private loadDependencies(): void {
    const type = this.currentType();
    const optionKeys = new Set(
      this.activeConfig()
        .fields.map((field) => field.optionsKey)
        .filter(Boolean),
    );
    if (optionKeys.has('categories') || type === 'categories') {
      this.loadCategoryOptions(this.editing()?.id);
    }
    if (optionKeys.has('foundations')) {
      this.budget.listSelectOptions('foundations').subscribe({
        next: (data) => this.foundations.set(data),
      });
    }
  }

  private normalizePayload(value: Record<string, unknown>): BudgetReferencePayload {
    const payload: BudgetReferencePayload = {};
    for (const [key, raw] of Object.entries(value)) {
      if (raw === '' || raw === undefined) {
        (payload as Record<string, unknown>)[key] = null;
        continue;
      }
      (payload as Record<string, unknown>)[key] = raw;
    }
    return payload;
  }
}
