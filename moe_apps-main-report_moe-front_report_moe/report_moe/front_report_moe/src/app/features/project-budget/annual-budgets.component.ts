import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit,
  computed,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import {
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormGroup,
  Validators,
} from '@angular/forms';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { CodeBannerComponent } from '../../shared/components/code-banner/code-banner.component';
import { FormDateComponent } from '../../shared/components/form-date/form-date.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { ListPageComponent } from '../../shared/components/list-page/list-page.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import type { TableColumn } from '../../shared/components/data-table/data-table.component';
import type { FilterGroup } from '../../shared/components/filter-panel/filter-panel.component';
import { ToastService } from '../../shared/services/toast.service';
import { DialogService } from '../../shared/services/dialog.service';
import { TranslationService } from '../../shared/services/translation.service';
import { FilterState } from '../../shared/utils/filter-state';
import type {
  AnnualBudget,
  AnnualBudgetPayload,
  BudgetSelectOption,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';

@Component({
  selector: 'app-annual-budgets',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ListPageComponent,
    ModalComponent,
    FormInputComponent,
    FormSelectComponent,
    FormDateComponent,
    ButtonComponent,
    CodeBannerComponent,
  ],
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

    <app-modal [visible]="modalOpen()" [title]="modalTitle()" size="medium" (close)="closeModal()">
      <app-code-banner
        *ngIf="editing()?.code"
        size="compact"
        [label]="t('budget.fields.code')"
        [code]="editing()!.code"
      />

      <form class="annual-budget-form" [formGroup]="form" (ngSubmit)="save()">
        <app-form-input
          [label]="t('budget.annual-budget.year')"
          type="number"
          [required]="true"
          formControlName="year"
        />
        <app-form-select
          [label]="t('budget.annual-budget.project-type')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [required]="true"
          [options]="projectTypeOptions()"
          formControlName="project_type"
        />
        <app-form-select
          [label]="t('budget.annual-budget.currency')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [required]="true"
          [options]="currencyOptions()"
          formControlName="currency"
        />
        <app-form-input
          [label]="t('budget.annual-budget.amount')"
          type="number"
          [required]="true"
          formControlName="amount"
        />
        <app-form-date
          [label]="t('budget.annual-budget.approved-at')"
          formControlName="approved_at"
        />
        <app-form-input
          [label]="t('budget.annual-budget.notes')"
          type="text"
          formControlName="notes"
        />
      </form>

      <div footer class="annual-budget-actions">
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
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styles: [
    `
      .annual-budget-form {
        display: grid;
        gap: 14px;
      }

      .annual-budget-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
      }
    `,
  ],
})
export class AnnualBudgetsComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private fb = inject(UntypedFormBuilder);
  private toast = inject(ToastService);
  private confirmDialog = inject(DialogService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);
  fs = new FilterState(() => this.load(), '');

  rows = signal<AnnualBudget[]>([]);
  projectTypes = signal<BudgetSelectOption[]>([]);
  currencies = signal<BudgetSelectOption[]>([]);
  modalOpen = signal(false);
  saving = signal(false);
  editing = signal<AnnualBudget | null>(null);

  form: UntypedFormGroup = this.buildForm();

  filterGroups = computed<FilterGroup[]>(() => [
    {
      label: this.t('budget.annual-budget.year'),
      key: 'year',
      type: 'select',
      options: this.yearFilterOptions(),
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
  ]);

  columns = computed<TableColumn[]>(() => [
    {
      key: 'code',
      label: this.t('budget.fields.code'),
      sortable: true,
      type: 'code',
      minWidth: '100px',
    },
    { key: 'year', label: this.t('budget.annual-budget.year'), sortable: true },
    {
      key: 'project_type_name',
      label: this.t('budget.annual-budget.project-type'),
      sortable: true,
    },
    { key: 'currency_code', label: this.t('budget.annual-budget.currency') },
    { key: 'amount', label: this.t('budget.annual-budget.amount'), sortable: true },
    { key: 'approved_at', label: this.t('budget.annual-budget.approved-at') },
    { key: 'notes', label: this.t('budget.annual-budget.notes') },
  ]);

  actions = computed(() => [
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
  ]);

  modalTitle = computed(() =>
    this.editing()
      ? this.t('budget.annual-budget.edit-title')
      : this.t('budget.annual-budget.add-title'),
  );

  pageConfig = computed(() => ({
    title: this.t('budget.annual-budget.title'),
    description: this.t('budget.annual-budget.description'),
    headerAction: {
      label: this.t('budget.annual-budget.add-title'),
      icon: 'add',
      click: () => this.openCreate(),
    },
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
    emptyMessage: this.t('budget.annual-budget.empty'),
  }));

  projectTypeOptions = computed<SelectOption[]>(() =>
    this.projectTypes().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  currencyOptions = computed<SelectOption[]>(() =>
    this.currencies().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  ngOnInit(): void {
    this.loadDependencies();
    this.load();
  }

  clearFilter(key: string): void {
    this.fs.onFilterChange({ key, value: '' });
  }

  load(): void {
    this.fs.loading.set(true);
    this.budget.listAnnualBudgets(this.fs.params).subscribe({
      next: (data) => {
        this.rows.set(data.results);
        this.fs.setTotal(data.count);
        this.fs.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.annual-budget.load-error'));
        this.fs.loading.set(false);
      },
    });
  }

  openCreate(): void {
    this.editing.set(null);
    this.form = this.buildForm();
    this.modalOpen.set(true);
  }

  openEdit(id: number): void {
    const row = this.rows().find((item) => item.id === id);
    if (!row) return;
    this.editing.set(row);
    this.form = this.buildForm(row);
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
    const payload = this.normalizePayload(this.form.getRawValue() as Record<string, unknown>);
    const current = this.editing();
    this.saving.set(true);
    const request = current
      ? this.budget.updateAnnualBudget(current.id, payload)
      : this.budget.createAnnualBudget(payload);

    request.subscribe({
      next: () => {
        this.toast.success(this.t('budget.annual-budget.save-success'));
        this.saving.set(false);
        this.closeModal();
        this.load();
      },
      error: () => {
        this.toast.error(this.t('budget.annual-budget.save-error'));
        this.saving.set(false);
      },
    });
  }

  async delete(id: number): Promise<void> {
    const confirmed = await this.confirmDialog.confirm({
      title: this.t('user-data.delete-confirm-title'),
      message: this.t('budget.annual-budget.confirm-delete'),
      type: 'error',
      icon: 'delete',
      confirmLabel: this.t('common.delete'),
      cancelLabel: this.t('common.cancel'),
    });
    if (!confirmed) return;
    this.budget.deleteAnnualBudget(id).subscribe({
      next: () => {
        this.toast.success(this.t('budget.annual-budget.delete-success'));
        this.load();
      },
      error: () => this.toast.error(this.t('budget.annual-budget.delete-error')),
    });
  }

  private loadDependencies(): void {
    this.budget.listSelectOptions('project-types').subscribe({
      next: (data) => this.projectTypes.set(data),
    });
    this.budget.listSelectOptions('currencies').subscribe({
      next: (data) => this.currencies.set(data),
    });
  }

  private buildForm(row?: AnnualBudget): UntypedFormGroup {
    return this.fb.group({
      year: [row?.year ?? new Date().getFullYear(), Validators.required],
      project_type: [row?.project_type ?? null, Validators.required],
      currency: [row?.currency ?? null, Validators.required],
      amount: [row?.amount ?? null, Validators.required],
      approved_at: [row?.approved_at ?? ''],
      notes: [row?.notes ?? ''],
    });
  }

  private normalizePayload(value: Record<string, unknown>): AnnualBudgetPayload {
    const payload: AnnualBudgetPayload = {};
    for (const [key, raw] of Object.entries(value)) {
      if (raw === '' || raw === undefined) {
        (payload as Record<string, unknown>)[key] = key === 'notes' ? '' : null;
        continue;
      }
      if (key === 'year' || key === 'project_type' || key === 'currency') {
        (payload as Record<string, unknown>)[key] = raw === null ? null : Number(raw);
        continue;
      }
      if (key === 'approved_at') {
        (payload as Record<string, unknown>)[key] =
          typeof raw === 'string' && raw ? raw.slice(0, 10) : null;
        continue;
      }
      if (key === 'amount') {
        (payload as Record<string, unknown>)[key] = raw === null ? null : Number(raw);
        continue;
      }
      (payload as Record<string, unknown>)[key] = raw;
    }
    return payload;
  }

  private yearFilterOptions(): { value: string; label: string }[] {
    const current = new Date().getFullYear();
    const years: { value: string; label: string }[] = [];
    for (let year = current + 2; year >= current - 8; year -= 1) {
      years.push({ value: String(year), label: String(year) });
    }
    return years;
  }
}
