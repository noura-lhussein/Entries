import { CommonModule } from '@angular/common';
import {
  Component,
  OnDestroy,
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
  FormsModule,
} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { CodeBannerComponent } from '../../shared/components/code-banner/code-banner.component';
import { FormActionsBarComponent } from '../../shared/components/form-actions-bar/form-actions-bar.component';
import { FormCheckboxComponent } from '../../shared/components/form-checkbox/form-checkbox.component';
import { FormDateComponent } from '../../shared/components/form-date/form-date.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import { FormReadonlyMetricComponent } from '../../shared/components/form-readonly-metric/form-readonly-metric.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { FormSectionTitleComponent } from '../../shared/components/form-section-title/form-section-title.component';
import { LocationPickerComponent } from '../../shared/components/location-picker/location-picker.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { LocationsService } from '../../shared/services/locations.service';
import { AuthService } from '../../core/services/auth.service';
import {
  PROJECT_STATUSES,
  type AnnualBudgetSelectOption,
  type BudgetSelectOption,
  type PreviousProjectOption,
  type Project,
  type ProjectAssignmentUser,
  type ProjectStatus,
} from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';
import {
  buildProjectForm,
  normalizeProjectPayload,
  syncPreviousProjectField,
} from './project-form.utils';
import { tryGetClientLocation } from './client-location.utils';
import {
  budgetExpenditurePercent,
  formatBudgetExpenditurePercent,
} from './budget-expenditure.utils';

@Component({
  selector: 'app-project-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    LocationPickerComponent,
    PageHeaderComponent,
    CodeBannerComponent,
    FormSectionTitleComponent,
    FormReadonlyMetricComponent,
    FormActionsBarComponent,
    FormInputComponent,
    FormMapPickerComponent,
    FormSelectComponent,
    FormDateComponent,
    FormCheckboxComponent,
    ButtonComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="pageTitle()" [action]="backAction"></app-page-header>

      <app-code-banner
        [label]="t('budget.projects.code')"
        [code]="codeBannerText()"
        [hint]="codeBannerHint()"
        [preview]="!isEdit()"
      />

      <form class="project-form" [formGroup]="form" (ngSubmit)="save()">
        <app-form-section-title [title]="t('budget.projects.section-budget')" />
        <app-form-select
          class="span-full"
          [label]="t('budget.projects.annual-budget')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [required]="true"
          [options]="annualBudgetOptions()"
          formControlName="annual_budget"
        />

        <app-form-section-title [title]="t('budget.projects.section-identity')" />
        <app-form-input
          [label]="t('budget.fields.name-ar')"
          type="text"
          [required]="true"
          formControlName="name_ar"
        />
        <app-form-input
          [label]="t('budget.fields.name-en')"
          type="text"
          formControlName="name_en"
        />
        <app-form-select
          [label]="t('budget.projects.status')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [required]="true"
          [options]="statusOptions()"
          formControlName="status"
        />

        <app-form-section-title [title]="t('budget.projects.section-location')" />
        @if (isFoundationLocked()) {
          <app-form-readonly-metric
            [label]="t('budget.fields.foundation')"
            [value]="lockedFoundationLabel()"
          />
        } @else {
          <app-form-select
            [label]="t('budget.fields.foundation')"
            [placeholder]="t('budget.reference.select-placeholder')"
            [required]="true"
            [options]="foundationOptions()"
            formControlName="foundation"
          />
        }
        <app-location-picker class="span-full" [required]="true" formControlName="community" />

        <app-form-section-title [title]="t('budget.projects.section-progress')" />
        <app-form-input
          [label]="t('budget.projects.proposed-budget')"
          type="number"
          [required]="true"
          formControlName="proposed_budget"
        />
        <app-form-input
          [label]="t('budget.projects.approved-budget')"
          type="number"
          formControlName="approved_budget"
        />
        <app-form-input
          [label]="t('budget.projects.budget-expenditure')"
          type="number"
          formControlName="budget_expenditure"
        />
        <app-form-readonly-metric
          [label]="t('budget.projects.expenditure-percent')"
          [value]="expenditurePercentDisplay()"
          [hint]="t('budget.projects.expenditure-percent-hint')"
        />
        <app-form-checkbox
          [label]="t('budget.projects.completion-manual')"
          [hint]="t('budget.projects.completion-manual-hint')"
          formControlName="completion_is_manual"
        />
        <app-form-input
          *ngIf="form.get('completion_is_manual')?.value"
          [label]="t('budget.projects.percentage-completion')"
          type="number"
          [min]="0"
          [max]="100"
          [errorMessage]="completionErrorMessage()"
          formControlName="percentage_completion"
        />
        <app-form-readonly-metric
          *ngIf="!form.get('completion_is_manual')?.value"
          [label]="t('budget.projects.percentage-completion')"
          [value]="completionDisplay()"
          [hint]="t('budget.projects.completion-auto')"
        />
        <app-form-date
          [label]="t('budget.projects.start-date')"
          [required]="true"
          formControlName="start_date"
        />
        <app-form-date
          [label]="t('budget.projects.end-date')"
          [required]="true"
          formControlName="end_date"
        />

        <app-form-section-title [title]="t('budget.projects.section-extra')" />
        <app-form-checkbox
          class="span-full"
          [label]="t('budget.projects.is-round')"
          formControlName="is_round"
        />
        <app-form-select
          class="span-full"
          [label]="t('budget.projects.previous-project')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [hint]="previousProjectHint()"
          [required]="isRound()"
          [options]="previousProjectOptions()"
          formControlName="previous_project"
        />
        <app-form-input
          class="span-full"
          [label]="t('budget.projects.description')"
          [multiline]="true"
          [rows]="4"
          formControlName="description"
        />

        <app-form-section-title [title]="t('budget.projects.target-policy-section')" />
        <app-form-select
          [label]="t('budget.projects.target')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [options]="targetOptions()"
          formControlName="target"
        />
        <app-form-select
          [label]="t('budget.projects.policy')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [options]="policyOptions()"
          formControlName="policy"
        />

        <app-form-section-title [title]="t('budget.projects.quantitative-target-section')" />
        <p class="span-full field-hint">{{ t('budget.projects.quantitative-target-hint') }}</p>
        <app-form-input
          [label]="t('budget.projects.quantitative-target-value')"
          type="number"
          formControlName="quantitative_target_value"
        />
        <app-form-select
          [label]="t('budget.projects.quantitative-target-unit')"
          [placeholder]="t('budget.reference.select-placeholder')"
          [options]="measureUnitOptions()"
          formControlName="quantitative_target_unit"
        />

        @if (isEdit() && canManageAssignments() && !isViewMode()) {
          <app-form-section-title [title]="t('budget.projects.assigned-users')" />
          <div class="span-full project-assignments">
            <div class="assignment-add-row">
              <app-form-select
                class="assignment-user-select"
                [label]="t('budget.projects.select-user')"
                [placeholder]="t('budget.projects.select-user')"
                [options]="assignableUserOptions()"
                [ngModel]="selectedAssignUserId()"
                (ngModelChange)="onAssignUserSelected($event)"
                [ngModelOptions]="{ standalone: true }"
              />
              <app-button
                variant="secondary"
                icon="person_add"
                [label]="t('budget.projects.add-user')"
                [disabled]="!selectedAssignUserId() || assigningUser()"
                [loading]="assigningUser()"
                (clicked)="addProjectUser()"
              />
            </div>
            @if (assignedUsers().length === 0) {
              <p class="assignment-empty">{{ t('budget.users.empty') }}</p>
            } @else {
              <ul class="assignment-list">
                @for (user of assignedUsers(); track user.id) {
                  <li class="assignment-item">
                    <span>{{ user.full_name || user.username }}</span>
                    <app-button
                      variant="ghost"
                      [label]="t('budget.projects.remove-user')"
                      (clicked)="removeProjectUser(user.id)"
                    />
                  </li>
                }
              </ul>
            }
          </div>
        }

        <app-form-section-title [title]="t('budget.projects.map-location')" />
        <app-form-map-picker
          class="span-full"
          [form]="form"
          [readOnly]="isViewMode()"
          [zoomLockHintLabel]="t('budget.projects.map-enable-zoom')"
          [label]="t('budget.projects.map-location')"
          [hint]="t('budget.projects.map-hint')"
          [latitudeLabel]="t('budget.projects.latitude')"
          [longitudeLabel]="t('budget.projects.longitude')"
          [clearLabel]="t('budget.projects.map-clear')"
          [searchPlaceholder]="t('budget.projects.map-search-placeholder')"
          [searchNoResultsLabel]="t('budget.projects.map-search-no-results')"
          [searchLoadingLabel]="t('budget.projects.map-search-loading')"
          [resetViewLabel]="t('budget.projects.map-reset-view')"
          [fullscreenLabel]="t('budget.projects.map-fullscreen')"
          [exitFullscreenLabel]="t('budget.projects.map-exit-fullscreen')"
        />

        <app-form-actions-bar>
          <app-button variant="ghost" [label]="t('common.cancel')" (clicked)="goBack()" />
          @if (!isViewMode()) {
            <app-button
              variant="primary"
              icon="save"
              [label]="t('common.save')"
              [disabled]="form.invalid || saving() || loading()"
              [loading]="saving()"
              (clicked)="save()"
            />
          }
        </app-form-actions-bar>
      </form>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './project-form.component.scss',
})
export class ProjectFormComponent implements OnInit, OnDestroy {
  private budget = inject(ProjectBudgetService);
  private fb = inject(UntypedFormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private auth = inject(AuthService);
  private locations = inject(LocationsService);

  t = (key: string) => this.translation.t(key);

  projectId = signal<number | null>(null);
  isViewMode = signal(false);
  loading = signal(false);
  saving = signal(false);
  annualBudgets = signal<AnnualBudgetSelectOption[]>([]);
  foundations = signal<BudgetSelectOption[]>([]);
  eligiblePreviousProjects = signal<PreviousProjectOption[]>([]);
  assignedUsers = signal<ProjectAssignmentUser[]>([]);
  foundationBudgetUsers = signal<BudgetSelectOption[]>([]);
  selectedAssignUserId = signal<number | null>(null);
  assigningUser = signal(false);

  form: UntypedFormGroup = buildProjectForm(this.fb);
  targets = signal<BudgetSelectOption[]>([]);
  policies = signal<BudgetSelectOption[]>([]);
  measureUnits = signal<(BudgetSelectOption & { symbol?: string })[]>([]);
  isRound = signal(false);
  projectCode = signal('');
  selectedBudgetCode = signal<string | null>(null);
  selectedSubdistrictCode = signal<string | null>(null);
  selectedCommunityCode = signal<string | null>(null);
  selectedBudgetYear = signal<number | null>(null);
  completionPercent = signal<number | null>(null);
  private roundRulesSub?: Subscription;
  private budgetCodeSub?: Subscription;
  private communityCoordsSub?: Subscription;

  codeBannerText = computed(() => {
    if (this.isEdit()) {
      return this.projectCode() || '—';
    }
    const budgetCode = this.selectedBudgetCode();
    if (!budgetCode) return '—';
    const subdistrictCode = this.selectedSubdistrictCode();
    const communityCode = this.selectedCommunityCode();
    if (!subdistrictCode || !communityCode) {
      return `${budgetCode}-???-???-P???`;
    }
    return `${budgetCode}-${subdistrictCode}-${communityCode}-P???`;
  });

  codeBannerHint = computed(() => {
    if (this.isEdit()) {
      return this.t('budget.projects.code-assigned');
    }
    if (!this.selectedBudgetCode()) {
      return this.t('budget.projects.code-select-budget');
    }
    if (!this.selectedSubdistrictCode() || !this.selectedCommunityCode()) {
      return this.t('budget.projects.code-select-location');
    }
    return this.t('budget.projects.code-preview');
  });

  completionDisplay = computed(() => `${this.completionPercent() ?? 0}%`);

  expenditurePercentDisplay(): string {
    return formatBudgetExpenditurePercent(
      budgetExpenditurePercent(
        this.form.get('approved_budget')?.value,
        this.form.get('budget_expenditure')?.value,
      ),
    );
  }

  completionErrorMessage(): string {
    const control = this.form.get('percentage_completion');
    if (!control || !(control.dirty || control.touched)) return '';
    if (control.hasError('min') || control.hasError('max')) {
      return this.t('budget.projects.completion-range-error');
    }
    return '';
  }

  previousProjectHint = computed(() => {
    if (!this.isRound()) return '';
    const year = this.selectedBudgetYear();
    if (year == null) return this.t('budget.projects.previous-project-select-budget');
    return this.t('budget.projects.previous-project-prior-years').replace('{year}', String(year));
  });

  isEdit = computed(() => this.projectId() !== null);

  isFoundationLocked = computed(() => {
    const user = this.auth.currentUser();
    return !!user && !user.is_admin && user.foundation_id != null;
  });

  canManageAssignments = computed(() => {
    const user = this.auth.currentUser();
    return !!user && (user.is_admin || user.can_manage_budget || user.can_manage_budget_users);
  });

  assignableUserOptions = computed<SelectOption[]>(() => {
    const assignedIds = new Set(this.assignedUsers().map((item) => item.id));
    return this.foundationBudgetUsers()
      .filter((item) => !assignedIds.has(item.id))
      .map((item) => ({
        value: item.id,
        label: item.name || String(item.id),
      }));
  });

  lockedFoundationLabel = computed(() => {
    const user = this.auth.currentUser();
    const id = user?.foundation_id;
    if (id == null) return '—';
    const fromList = this.foundations().find((item) => item.id === id)?.name;
    return fromList || user?.foundation_name || String(id);
  });

  pageTitle = computed(() => {
    if (this.isViewMode()) return this.t('budget.projects.view-title');
    return this.isEdit()
      ? this.t('budget.projects.edit-title')
      : this.t('budget.projects.add-title');
  });

  backAction = {
    label: this.t('budget.projects.back-to-list'),
    icon: 'arrow_back',
    routerLink: '/budget/projects',
  };

  annualBudgetOptions = computed<SelectOption[]>(() =>
    this.annualBudgets().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  foundationOptions = computed<SelectOption[]>(() =>
    this.foundations().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  targetOptions = computed<SelectOption[]>(() =>
    this.targets().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  policyOptions = computed<SelectOption[]>(() =>
    this.policies().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  measureUnitOptions = computed<SelectOption[]>(() =>
    this.measureUnits().map((item) => ({
      value: item.id,
      label: item.symbol ? `${item.name} (${item.symbol})` : item.name || String(item.id),
    })),
  );

  previousProjectOptions = computed<SelectOption[]>(() => {
    if (!this.isRound()) return [];
    return this.eligiblePreviousProjects().map((item) => ({
      value: item.id,
      label: `${item.code || item.name_ar || item.id} — ${item.annual_budget_year}`,
    }));
  });

  statusOptions = computed<SelectOption[]>(() =>
    PROJECT_STATUSES.map((status) => ({
      value: status,
      label: this.statusLabel(status),
    })),
  );

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    void this.submitProject();
  }

  private async submitProject(): Promise<void> {
    const basePayload = normalizeProjectPayload(this.form.getRawValue() as Record<string, unknown>);
    const clientLocation = await tryGetClientLocation();
    const payload = clientLocation ? { ...basePayload, _change_meta: clientLocation } : basePayload;
    const id = this.projectId();
    this.saving.set(true);
    const request = id
      ? this.budget.updateProject(id, payload)
      : this.budget.createProject(payload);

    request.subscribe({
      next: () => {
        this.toast.success(this.t('budget.projects.save-success'));
        this.saving.set(false);
        this.router.navigate(['/budget/projects']);
      },
      error: () => {
        this.toast.error(this.t('budget.projects.save-error'));
        this.saving.set(false);
      },
    });
  }

  onAssignUserSelected(value: unknown): void {
    if (value == null || value === '') {
      this.selectedAssignUserId.set(null);
      return;
    }
    const id = Number(value);
    this.selectedAssignUserId.set(Number.isNaN(id) ? null : id);
  }

  statusLabel(status: ProjectStatus): string {
    return this.t(`budget.projects.status.${status}`);
  }

  goBack(): void {
    this.router.navigate(['/budget/projects']);
  }

  ngOnInit(): void {
    this.isViewMode.set(this.route.snapshot.url.some((segment) => segment.path === 'view'));
    this.loadDependencies();

    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      const id = Number(idParam);
      if (!Number.isNaN(id)) {
        this.projectId.set(id);
        this.loadProject(id);
        return;
      }
    }

    this.setupRoundProjectRules();
    this.setupCommunityCoordinateSync();
    this.applyLockedFoundation();
  }

  ngOnDestroy(): void {
    this.roundRulesSub?.unsubscribe();
    this.budgetCodeSub?.unsubscribe();
    this.communityCoordsSub?.unsubscribe();
  }

  private setupBudgetCodePreview(): void {
    this.budgetCodeSub?.unsubscribe();
    const control = this.form.get('annual_budget');
    if (!control) return;

    const sync = () => {
      const id = Number(control.value);
      const budget = this.annualBudgets().find((item) => item.id === id);
      this.selectedBudgetCode.set(budget?.code ?? null);
      this.selectedBudgetYear.set(budget?.year ?? null);
      this.loadEligiblePreviousProjects();
    };

    sync();
    this.budgetCodeSub = control.valueChanges.subscribe(() => sync());
  }

  private setupCommunityCoordinateSync(): void {
    this.communityCoordsSub?.unsubscribe();
    const control = this.form.get('community');
    if (!control) return;

    this.communityCoordsSub = control.valueChanges.subscribe((raw) => {
      if (this.isViewMode()) return;

      if (raw == null || raw === '') {
        this.form.patchValue({ latitude: '', longitude: '' });
        this.selectedSubdistrictCode.set(null);
        this.selectedCommunityCode.set(null);
        return;
      }

      const communityId = Number(raw);
      if (Number.isNaN(communityId)) return;

      this.locations.getCommunity(communityId).subscribe({
        next: (detail) => {
          this.selectedSubdistrictCode.set(detail.subdistrict_code?.trim() || null);
          this.selectedCommunityCode.set(detail.code?.trim() || null);
          const lat = this.parseCoordinate(detail.latitude);
          const lng = this.parseCoordinate(detail.longitude);
          if (lat == null || lng == null) return;
          this.form.patchValue({ latitude: lat, longitude: lng });
        },
      });
    });
  }

  private parseCoordinate(value: number | string | null | undefined): number | null {
    if (value == null || value === '') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  private setupRoundProjectRules(): void {
    this.roundRulesSub?.unsubscribe();
    syncPreviousProjectField(this.form);
    this.isRound.set(!!this.form.get('is_round')?.value);
    this.loadEligiblePreviousProjects();
    this.roundRulesSub = this.form.get('is_round')?.valueChanges.subscribe(() => {
      syncPreviousProjectField(this.form);
      this.isRound.set(!!this.form.get('is_round')?.value);
      this.loadEligiblePreviousProjects();
    });
    this.setupBudgetCodePreview();
  }

  private loadEligiblePreviousProjects(): void {
    if (!this.isRound()) {
      this.eligiblePreviousProjects.set([]);
      return;
    }

    const budgetId = Number(this.form.get('annual_budget')?.value);
    if (!budgetId || Number.isNaN(budgetId)) {
      this.eligiblePreviousProjects.set([]);
      this.clearInvalidPreviousProject();
      return;
    }

    this.budget.listEligiblePreviousProjects(budgetId, this.projectId() ?? undefined).subscribe({
      next: (data) => {
        this.eligiblePreviousProjects.set(data);
        this.clearInvalidPreviousProject();
      },
      error: () => this.eligiblePreviousProjects.set([]),
    });
  }

  private clearInvalidPreviousProject(): void {
    const control = this.form.get('previous_project');
    if (!control?.value) return;

    const id = Number(control.value);
    if (!this.eligiblePreviousProjects().some((item) => item.id === id)) {
      control.setValue(null, { emitEvent: false });
    }
  }

  private loadProject(id: number): void {
    this.loading.set(true);
    this.budget.getProject(id).subscribe({
      next: (project) => {
        this.form = buildProjectForm(this.fb, project);
        this.projectCode.set(project.code || '');
        this.completionPercent.set(Number(project.percentage_completion ?? 0));
        const budget = this.annualBudgets().find((item) => item.id === project.annual_budget);
        this.selectedBudgetCode.set(budget?.code ?? project.annual_budget_code ?? null);
        this.selectedBudgetYear.set(budget?.year ?? project.annual_budget_year ?? null);
        this.setupRoundProjectRules();
        this.setupCommunityCoordinateSync();
        this.applyLockedFoundation();
        this.loadProjectAssignments(id);
        this.applyViewMode();
        this.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.projects.load-error'));
        this.loading.set(false);
        this.router.navigate(['/budget/projects']);
      },
    });
  }

  private applyViewMode(): void {
    if (!this.isViewMode()) return;
    this.form.disable({ emitEvent: false });
  }

  private applyLockedFoundation(): void {
    if (!this.isFoundationLocked()) return;
    const foundationId = this.auth.currentUser()?.foundation_id;
    if (foundationId == null) return;
    const control = this.form.get('foundation');
    if (!control) return;
    control.setValue(foundationId, { emitEvent: false });
    control.disable({ emitEvent: false });
  }

  private loadDependencies(): void {
    this.budget.listAnnualBudgetOptions().subscribe({
      next: (data) => this.annualBudgets.set(data),
    });
    this.budget.listSelectOptions('foundations').subscribe({
      next: (data) => {
        this.foundations.set(data);
        this.applyLockedFoundation();
      },
    });
    if (this.canManageAssignments()) {
      this.budget.listBudgetUsers({ page_size: 500 }).subscribe({
        next: (data) => {
          this.foundationBudgetUsers.set(
            data.results.map((user) => ({
              id: user.id,
              name: user.full_name || user.username,
            })),
          );
        },
      });
    }
    this.budget.listSelectOptions('targets').subscribe({
      next: (data) => this.targets.set(data),
    });
    this.budget.listSelectOptions('policies').subscribe({
      next: (data) => this.policies.set(data),
    });
    this.budget.listSelectOptions('measure-units').subscribe({
      next: (data) => this.measureUnits.set(data as (BudgetSelectOption & { symbol?: string })[]),
    });
  }

  private loadProjectAssignments(projectId: number): void {
    if (!this.canManageAssignments()) return;
    this.budget.listProjectAssignments(projectId).subscribe({
      next: (users) => this.assignedUsers.set(users),
      error: () => this.toast.error(this.t('budget.projects.assignment-load-error')),
    });
  }

  addProjectUser(): void {
    const projectId = this.projectId();
    const userId = this.selectedAssignUserId();
    if (!projectId || userId == null) return;
    this.assigningUser.set(true);
    this.budget.addProjectAssignment(projectId, userId).subscribe({
      next: (user) => {
        this.assignedUsers.update((list) => [...list, user]);
        this.selectedAssignUserId.set(null);
        this.assigningUser.set(false);
        this.toast.success(this.t('budget.projects.assignment-success'));
      },
      error: () => {
        this.assigningUser.set(false);
        this.toast.error(this.t('budget.projects.assignment-error'));
      },
    });
  }

  removeProjectUser(userId: number): void {
    const projectId = this.projectId();
    if (!projectId) return;
    this.budget.removeProjectAssignment(projectId, userId).subscribe({
      next: () => {
        this.assignedUsers.update((list) => list.filter((item) => item.id !== userId));
        this.toast.success(this.t('budget.projects.assignment-remove-success'));
      },
      error: () => this.toast.error(this.t('budget.projects.assignment-remove-error')),
    });
  }
}
