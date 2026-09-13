import { CommonModule } from '@angular/common';
import {
  Component,
  OnDestroy,
  OnInit,
  ViewChild,
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
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { FormActionsBarComponent } from '../../shared/components/form-actions-bar/form-actions-bar.component';
import { FormDateComponent } from '../../shared/components/form-date/form-date.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { FormSearchSelectComponent } from '../../shared/components/form-search-select/form-search-select.component';
import { FormCategoryPickerComponent } from '../../shared/components/form-category-picker/form-category-picker.component';
import { FormSectionTitleComponent } from '../../shared/components/form-section-title/form-section-title.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import {
  MILESTONE_STATUSES,
  type CategorySelectOption,
  type Milestone,
  type MilestonePayload,
  type MilestoneStatus,
} from './project-budget.models';
import { sortCategoryOptions } from './category-options.utils';
import { ProjectBudgetService } from './project-budget.service';

@Component({
  selector: 'app-milestone-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    PageHeaderComponent,
    FormSectionTitleComponent,
    FormInputComponent,
    FormSelectComponent,
    FormSearchSelectComponent,
    FormCategoryPickerComponent,
    FormDateComponent,
    FormMapPickerComponent,
    FormActionsBarComponent,
    ButtonComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="pageTitle()" [action]="backAction"></app-page-header>

      <form class="milestone-form" [formGroup]="form" (ngSubmit)="save()">
        <app-form-section-title [title]="t('budget.milestones.section-main')" />
        <app-form-search-select
          class="span-full"
          [label]="t('budget.milestones.project')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [searchPlaceholder]="t('budget.projects.search')"
          [noResultsLabel]="t('budget.reference.search-no-results')"
          [clearLabel]="t('budget.reference.clear-selection')"
          [required]="true"
          [options]="projectOptions()"
          [errorMessage]="projectErrorMessage()"
          formControlName="project"
        />
        <app-form-select
          class="span-full"
          [label]="t('budget.milestones.parent')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [options]="parentOptions()"
          formControlName="parent"
        />
        <app-form-select
          [label]="t('budget.milestones.responsible')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [options]="responsibleOptions()"
          formControlName="responsible"
        />
        <app-form-category-picker
          class="span-full"
          [label]="t('budget.milestones.category')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [searchPlaceholder]="t('budget.milestones.category-search')"
          [noResultsLabel]="t('budget.reference.search-no-results')"
          [clearLabel]="t('budget.reference.clear-selection')"
          [emptyHint]="categoryEmptyHint()"
          [disabled]="!hasProjectSelected()"
          [categories]="categories()"
          formControlName="category"
        />
        <app-form-select
          [label]="t('budget.milestones.status')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [required]="true"
          [options]="statusOptions()"
          [errorMessage]="statusErrorMessage()"
          formControlName="status"
        />
        <app-form-input
          [label]="t('budget.fields.name-ar')"
          type="text"
          [required]="true"
          [errorMessage]="nameArErrorMessage()"
          formControlName="name_ar"
        />
        <app-form-input
          [label]="t('budget.fields.name-en')"
          type="text"
          formControlName="name_en"
        />

        <app-form-section-title [title]="t('budget.milestones.section-progress')" />
        <app-form-input
          [label]="t('budget.milestones.percentage')"
          type="number"
          [min]="0"
          [max]="100"
          [step]="1"
          [hint]="t('budget.milestones.percentage-hint')"
          [errorMessage]="percentageErrorMessage()"
          formControlName="percentage_completion"
        />
        <app-form-input
          [label]="t('budget.milestones.order')"
          type="number"
          formControlName="order"
        />
        <app-form-date [label]="t('budget.projects.start-date')" formControlName="start_date" />
        <app-form-date [label]="t('budget.projects.end-date')" formControlName="end_date" />
        <app-form-date [label]="t('budget.milestones.due-date')" formControlName="due_date" />

        <app-form-section-title [title]="t('budget.projects.map-location')" />
        <app-form-map-picker
          #mapPicker
          class="span-full"
          [form]="form"
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
        />

        <app-form-actions-bar>
          <app-button variant="ghost" [label]="t('common.cancel')" (clicked)="goBack()" />
          <app-button
            variant="primary"
            icon="save"
            [label]="t('common.save')"
            [disabled]="saving() || loading()"
            [loading]="saving()"
            (clicked)="save()"
          />
        </app-form-actions-bar>
        @if (validationMessages().length > 0) {
          <div class="validation-summary" role="alert">
            <p>{{ t('budget.milestones.fix-errors') }}</p>
            <ul>
              @for (message of validationMessages(); track message) {
                <li>{{ message }}</li>
              }
            </ul>
          </div>
        }
      </form>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './milestone-form.component.scss',
})
export class MilestoneFormComponent implements OnInit, OnDestroy {
  @ViewChild('mapPicker') mapPicker?: FormMapPickerComponent;

  private budget = inject(ProjectBudgetService);
  private fb = inject(UntypedFormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);
  loading = signal(false);
  saving = signal(false);
  submitAttempted = signal(false);
  milestoneId = signal<number | null>(null);
  projects = signal<SelectOption[]>([]);
  responsibles = signal<SelectOption[]>([]);
  parents = signal<SelectOption[]>([]);
  categories = signal<CategorySelectOption[]>([]);
  private projectTypeByProjectId = signal<Map<number, number>>(new Map());
  private projectCoordsByProjectId = signal<Map<number, { latitude: number; longitude: number }>>(
    new Map(),
  );
  selectedProjectId = signal<number | null>(null);

  private projectChangeSub?: Subscription;

  form: UntypedFormGroup = this.fb.group({
    project: [null, Validators.required],
    parent: [null],
    responsible: [null],
    category: [null],
    name_ar: ['', Validators.required],
    name_en: [''],
    latitude: [null],
    longitude: [null],
    percentage_completion: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
    start_date: [null],
    end_date: [null],
    order: [1],
    due_date: [null],
    status: ['draft', Validators.required],
  });

  isEdit = computed(() => this.milestoneId() !== null);
  pageTitle = computed(() =>
    this.isEdit() ? this.t('budget.milestones.edit-title') : this.t('budget.milestones.add-title'),
  );
  projectOptions = computed(() => this.projects());
  responsibleOptions = computed(() => this.responsibles());
  parentOptions = computed(() => this.parents());
  hasProjectSelected = computed(() => this.selectedProjectId() != null);
  categoryEmptyHint = computed(() =>
    this.hasProjectSelected() ? '' : this.t('budget.milestones.category-select-project-first'),
  );
  statusOptions = computed<SelectOption[]>(() =>
    MILESTONE_STATUSES.map((status) => ({
      value: status,
      label: this.statusLabel(status),
    })),
  );
  percentageErrorMessage = computed(() => {
    const control = this.form.get('percentage_completion');
    if (!control || !this.shouldShowErrors()) return '';
    if (control.hasError('required')) return this.t('budget.milestones.percentage-required');
    if (control.hasError('min') || control.hasError('max')) {
      return this.t('budget.milestones.percentage-error');
    }
    return '';
  });
  projectErrorMessage = computed(() => {
    const control = this.form.get('project');
    if (!control || !this.shouldShowErrors()) return '';
    if (control.hasError('required')) return this.t('budget.milestones.project-required');
    return '';
  });
  statusErrorMessage = computed(() => {
    const control = this.form.get('status');
    if (!control || !this.shouldShowErrors()) return '';
    if (control.hasError('required')) return this.t('budget.milestones.status-required');
    return '';
  });
  nameArErrorMessage = computed(() => {
    const control = this.form.get('name_ar');
    if (!control || !this.shouldShowErrors()) return '';
    if (control.hasError('required')) return this.t('budget.milestones.name-ar-required');
    return '';
  });
  validationMessages = computed(() => {
    if (!this.shouldShowErrors() || this.form.valid) return [];
    const messages: string[] = [];
    if (this.projectErrorMessage()) messages.push(this.projectErrorMessage());
    if (this.statusErrorMessage()) messages.push(this.statusErrorMessage());
    if (this.nameArErrorMessage()) messages.push(this.nameArErrorMessage());
    if (this.percentageErrorMessage()) messages.push(this.percentageErrorMessage());
    return messages;
  });

  backAction = {
    label: this.t('budget.milestones.back-to-list'),
    icon: 'arrow_back',
    routerLink: '/budget/milestones',
  };

  ngOnInit(): void {
    this.loadDependencies();

    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      const id = Number(idParam);
      if (!Number.isNaN(id)) {
        this.milestoneId.set(id);
        this.loadMilestone(id);
      }
    }

    this.projectChangeSub = this.form.get('project')?.valueChanges.subscribe((projectId) => {
      this.syncSelectedProjectId(projectId);
      this.loadParentMilestones();
      this.loadCategoriesForProject(projectId);
      this.applyProjectLocation(projectId);
    });

    this.syncSelectedProjectId(this.form.get('project')?.value);
  }

  ngOnDestroy(): void {
    this.projectChangeSub?.unsubscribe();
  }

  private syncSelectedProjectId(projectId: unknown): void {
    if (projectId == null || projectId === '') {
      this.selectedProjectId.set(null);
      return;
    }
    const parsed = Number(projectId);
    this.selectedProjectId.set(Number.isFinite(parsed) ? parsed : null);
  }

  save(): void {
    this.submitAttempted.set(true);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.toast.error(this.t('budget.milestones.fix-errors-short'));
      return;
    }
    const payload = this.normalizePayload();
    const id = this.milestoneId();
    this.saving.set(true);
    const request = id
      ? this.budget.updateMilestone(id, payload)
      : this.budget.createMilestone(payload);

    request.subscribe({
      next: () => {
        this.toast.success(this.t('budget.milestones.save-success'));
        this.saving.set(false);
        this.submitAttempted.set(false);
        this.router.navigate(['/budget/milestones']);
      },
      error: () => {
        this.toast.error(this.t('budget.milestones.save-error'));
        this.saving.set(false);
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/budget/milestones']);
  }

  statusLabel(status: MilestoneStatus): string {
    return this.t(`budget.milestones.status.${status}`);
  }

  private projectOptionLabel(item: {
    id: number;
    code?: string;
    name_ar?: string;
    name_en?: string;
    annual_budget_year?: number;
  }): string {
    const name = item.name_ar || item.name_en || '';
    const code = item.code || '';
    const year = item.annual_budget_year != null ? String(item.annual_budget_year) : '';
    const parts = [code, name, year].filter((part) => part.trim().length > 0);
    return parts.join(' — ') || String(item.id);
  }

  private loadDependencies(): void {
    this.budget.listProjects({ page_size: 500 }).subscribe({
      next: (data) => {
        const typeMap = new Map<number, number>();
        const coordMap = new Map<number, { latitude: number; longitude: number }>();
        for (const item of data.results) {
          typeMap.set(item.id, item.project_type_id);
          const latitude = this.parseCoord(item.latitude);
          const longitude = this.parseCoord(item.longitude);
          if (latitude != null && longitude != null) {
            coordMap.set(item.id, { latitude, longitude });
          }
        }
        this.projectTypeByProjectId.set(typeMap);
        this.projectCoordsByProjectId.set(coordMap);
        this.projects.set(
          data.results.map((item) => ({
            value: item.id,
            label: this.projectOptionLabel(item),
          })),
        );
        const projectId = this.form.get('project')?.value;
        if (projectId != null) {
          this.loadCategoriesForProject(projectId);
          this.applyProjectLocation(projectId);
        }
      },
    });
    this.budget.list('responsibles', { page_size: 500 }).subscribe({
      next: (data) =>
        this.responsibles.set(
          data.results.map((item) => ({
            value: item.id,
            label: item.name_ar || item.name_en || String(item.id),
          })),
        ),
    });
  }

  private loadCategoriesForProject(projectId: number | string | null): void {
    const parsedId = projectId != null ? Number(projectId) : NaN;
    if (!Number.isFinite(parsedId)) {
      this.categories.set([]);
      this.form.patchValue({ category: null }, { emitEvent: false });
      return;
    }

    const projectTypeId = this.projectTypeByProjectId().get(parsedId);
    const params = projectTypeId != null ? { project_type: projectTypeId } : undefined;
    this.budget.listCategoryOptions(params).subscribe({
      next: (data) => {
        const options = sortCategoryOptions(data);
        this.categories.set(options);
        const currentCategory = this.form.get('category')?.value;
        if (
          currentCategory != null &&
          !options.some((option) => Number(option.id) === Number(currentCategory))
        ) {
          this.form.patchValue({ category: null }, { emitEvent: false });
        }
      },
    });
  }

  private loadMilestone(id: number): void {
    this.loading.set(true);
    this.budget.getMilestone(id).subscribe({
      next: (item) => {
        this.patchForm(item);
        this.loadParentMilestones();
        this.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.milestones.load-error'));
        this.loading.set(false);
        this.router.navigate(['/budget/milestones']);
      },
    });
  }

  private patchForm(item: Milestone): void {
    this.syncSelectedProjectId(item.project);
    this.form.patchValue({
      project: item.project,
      parent: item.parent,
      responsible: item.responsible,
      category: item.category,
      name_ar: item.name_ar,
      name_en: item.name_en,
      latitude: item.latitude,
      longitude: item.longitude,
      percentage_completion: Number(item.percentage_completion ?? 0),
      start_date: item.start_date,
      end_date: item.end_date,
      order: item.order,
      due_date: item.due_date,
      status: item.status,
    });
    this.loadCategoriesForProject(item.project);
    this.applyProjectLocation(item.project);
  }

  private applyProjectLocation(projectId: number | string | null | undefined): void {
    const parsedId = projectId != null ? Number(projectId) : NaN;
    if (!Number.isFinite(parsedId)) return;

    const coords = this.projectCoordsByProjectId().get(parsedId);
    if (!coords) return;

    const latCtrl = this.form.get('latitude');
    const lngCtrl = this.form.get('longitude');
    const currentLat = this.parseCoord(latCtrl?.value);
    const currentLng = this.parseCoord(lngCtrl?.value);
    const hasMilestoneCoords = currentLat != null && currentLng != null;

    if (this.isEdit() && hasMilestoneCoords) {
      return;
    }

    this.form.patchValue({
      latitude: coords.latitude,
      longitude: coords.longitude,
    });
    requestAnimationFrame(() => this.mapPicker?.focusMarker());
  }

  private parseCoord(value: unknown): number | null {
    if (value == null || value === '') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  private loadParentMilestones(): void {
    const projectId = Number(this.form.get('project')?.value);
    if (!projectId || Number.isNaN(projectId)) {
      this.parents.set([]);
      this.form.get('parent')?.setValue(null, { emitEvent: false });
      return;
    }
    this.budget.listMilestones({ project: projectId, page_size: 500 }).subscribe({
      next: (data) => {
        const selfId = this.milestoneId();
        const options = data.results
          .filter((item) => item.id !== selfId)
          .map((item) => ({
            value: item.id,
            label: item.name_ar || String(item.id),
          }));
        this.parents.set(options);
      },
      error: () => this.parents.set([]),
    });
  }

  private normalizePayload(): MilestonePayload {
    const raw = this.form.getRawValue() as Record<string, unknown>;
    const toNullableNumber = (value: unknown): number | null => {
      if (value == null || value === '') return null;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    };

    return {
      project: toNullableNumber(raw['project']),
      parent: toNullableNumber(raw['parent']),
      responsible: toNullableNumber(raw['responsible']),
      category: toNullableNumber(raw['category']),
      name_ar: String(raw['name_ar'] || ''),
      name_en: String(raw['name_en'] || ''),
      latitude: toNullableNumber(raw['latitude']),
      longitude: toNullableNumber(raw['longitude']),
      percentage_completion: toNullableNumber(raw['percentage_completion']),
      start_date: (raw['start_date'] as string) || null,
      end_date: (raw['end_date'] as string) || null,
      order: toNullableNumber(raw['order']),
      due_date: (raw['due_date'] as string) || null,
      status: (raw['status'] as MilestoneStatus) || null,
    };
  }

  private shouldShowErrors(): boolean {
    return this.submitAttempted() || this.form.touched || this.form.dirty;
  }
}
