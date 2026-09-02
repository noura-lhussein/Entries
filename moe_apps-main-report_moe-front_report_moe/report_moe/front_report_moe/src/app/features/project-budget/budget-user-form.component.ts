import { Component, OnInit, ViewChild, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import {
  DynamicFormComponent,
  FormConfig,
  FormFieldConfig,
} from '../../shared/components/dynamic-form/dynamic-form.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { ProjectBudgetService } from './project-budget.service';
import type { BudgetSelectOption, BudgetUser } from './project-budget.models';

@Component({
  selector: 'app-budget-user-form',
  standalone: true,
  imports: [CommonModule, DynamicFormComponent, PageHeaderComponent],
  template: `
    <div class="page-container">
      <app-page-header
        [title]="isEdit() ? t('budget.users.form-title-edit') : t('budget.users.form-title-new')"
        [action]="backAction"
      ></app-page-header>
      <app-example-form
        #budgetUserForm
        [formConfig]="formConfig()"
        (fieldChange)="onFieldChange($event)"
        (submit)="onSubmit()"
      ></app-example-form>
    </div>
  `,
  styleUrl: './budget-user-form.component.scss',
})
export class BudgetUserFormComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private auth = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  @ViewChild('budgetUserForm') budgetUserForm!: DynamicFormComponent;

  isEdit = signal(false);
  userId: number | null = null;
  isLoading = signal(false);
  foundations = signal<BudgetSelectOption[]>([]);
  projects = signal<BudgetSelectOption[]>([]);

  formConfig = computed<FormConfig>(() => {
    const isSystemAdmin = this.auth.isAdmin();
    const lockedFoundationId = this.auth.currentUser()?.foundation_id ?? null;
    const foundationOptions = this.foundations().map((item) => ({
      value: item.id,
      label: item.name,
    }));

    const fields: FormFieldConfig[] = [
      ...(this.isEdit()
        ? []
        : [
            {
              key: 'username',
              type: 'input' as const,
              label: this.t('budget.users.username'),
              placeholder: this.t('budget.users.username-placeholder'),
              inputType: 'text' as const,
              required: true,
              validators: [],
            },
          ]),
      {
        key: 'password',
        type: 'input',
        label: this.isEdit()
          ? this.t('budget.users.password-edit')
          : this.t('budget.users.password'),
        placeholder: this.t('budget.users.password-placeholder'),
        inputType: 'password' as const,
        required: !this.isEdit(),
      },
      {
        key: 'first_name',
        type: 'input',
        label: this.t('budget.users.first-name'),
        inputType: 'text' as const,
      },
      {
        key: 'last_name',
        type: 'input',
        label: this.t('budget.users.last-name'),
        inputType: 'text' as const,
      },
      {
        key: 'email',
        type: 'input',
        label: this.t('budget.users.email'),
        inputType: 'email' as const,
      },
      {
        key: 'foundation',
        type: 'select',
        label: this.t('budget.fields.foundation'),
        placeholder: this.t('budget.reference.select-placeholder'),
        options: foundationOptions,
        required: true,
        validators: [],
        disabled: !isSystemAdmin && lockedFoundationId != null,
        defaultValue: !isSystemAdmin && lockedFoundationId != null ? lockedFoundationId : undefined,
      },
      {
        key: 'assigned_project_ids',
        type: 'multi-select',
        label: this.t('budget.users.assigned-projects'),
        placeholder: this.t('budget.reference.select-placeholder'),
        options: this.projectOptions(),
        defaultValue: [],
      },
      {
        key: 'is_active',
        type: 'checkbox',
        label: this.t('budget.users.active'),
        defaultValue: true,
      },
      {
        key: 'can_manage_budget',
        type: 'checkbox',
        label: this.t('budget.users.can-manage-budget'),
        defaultValue: false,
        disabled: !isSystemAdmin,
      },
      {
        key: 'can_manage_reference_data',
        type: 'checkbox',
        label: this.t('budget.users.can-manage-reference-data'),
        defaultValue: false,
        disabled: !isSystemAdmin,
      },
      {
        key: 'can_view_budget',
        type: 'checkbox',
        label: this.t('budget.users.can-view'),
        defaultValue: true,
        disabled: !isSystemAdmin && !this.auth.currentUser()?.can_view_budget,
      },
      {
        key: 'can_write_budget',
        type: 'checkbox',
        label: this.t('budget.users.can-write'),
        defaultValue: false,
        disabled: !isSystemAdmin && !this.auth.currentUser()?.can_write_budget,
      },
      {
        key: 'can_manage_budget_users',
        type: 'checkbox',
        label: this.t('budget.users.can-manage-users'),
        defaultValue: false,
        disabled: !isSystemAdmin && !this.auth.currentUser()?.can_manage_budget_users,
      },
    ];

    return {
      title: this.isEdit()
        ? this.t('budget.users.form-title-edit')
        : this.t('budget.users.form-title-new'),
      subtitle: this.isEdit()
        ? this.t('budget.users.form-subtitle-edit')
        : this.t('budget.users.form-subtitle-new'),
      fields,
      showDebug: false,
    };
  });

  projectOptions = computed(() =>
    this.projects().map((item) => ({
      value: item.id,
      label: item.name || String(item.id),
    })),
  );

  get backAction() {
    return {
      label: this.t('form.back'),
      icon: 'arrow_back',
      routerLink: '/budget/users',
      variant: 'ghost' as const,
    };
  }

  ngOnInit(): void {
    this.budget.listSelectOptions('foundations').subscribe({
      next: (data) => this.foundations.set(data),
      error: () => this.toast.error(this.t('budget.reference.load-error')),
    });

    const foundationId = this.auth.currentUser()?.foundation_id;
    if (foundationId != null) {
      this.loadProjects(foundationId);
    } else {
      this.budget.listProjects({ page_size: 500 }).subscribe({
        next: (data) => {
          this.projects.set(
            data.results.map((project) => ({
              id: project.id,
              name: project.name_ar || project.code,
            })),
          );
        },
      });
    }

    this.route.params.subscribe((params) => {
      if (params['id']) {
        this.userId = Number(params['id']);
        this.isEdit.set(true);
        this.loadUser();
      }
    });
  }

  onFieldChange(event: { key: string; value: unknown }): void {
    if (event.key !== 'foundation' || event.value == null || event.value === '') {
      return;
    }
    const foundationId = Number(event.value);
    if (Number.isNaN(foundationId)) return;
    this.loadProjects(foundationId);
  }

  private loadProjects(foundationId: number): void {
    this.budget.listProjects({ foundation: foundationId, page_size: 500 }).subscribe({
      next: (data) => {
        const projectIds = new Set(data.results.map((project) => project.id));
        this.projects.set(
          data.results.map((project) => ({
            id: project.id,
            name: project.name_ar || project.code,
          })),
        );
        const control = this.budgetUserForm?.userForm?.get('assigned_project_ids');
        if (control) {
          const current = (control.value as number[]) ?? [];
          control.setValue(
            current.filter((id) => projectIds.has(id)),
            { emitEvent: false },
          );
        }
      },
    });
  }

  private loadUser(): void {
    if (!this.userId) return;
    this.budget.getBudgetUser(this.userId).subscribe({
      next: (user: BudgetUser) => {
        if (user.foundation != null) {
          this.loadProjects(user.foundation);
        }
        setTimeout(() => {
          this.budgetUserForm?.userForm?.patchValue({
            first_name: user.first_name,
            last_name: user.last_name,
            email: user.email,
            foundation: user.foundation,
            assigned_project_ids: [...(user.assigned_project_ids ?? [])],
            is_active: user.is_active,
            can_manage_budget: user.can_manage_budget,
            can_manage_reference_data: user.can_manage_reference_data,
            can_view_budget: user.can_view_budget,
            can_write_budget: user.can_write_budget,
            can_manage_budget_users: user.can_manage_budget_users,
          });
        }, 50);
      },
      error: () => this.toast.error(this.t('budget.users.load-error')),
    });
  }

  private finishSave(messageKey: string): void {
    this.toast.success(this.t(messageKey));
    this.router.navigate(['/budget/users']);
  }

  private syncAssignmentsThenFinish(
    userId: number,
    projectIds: number[],
    messageKey: string,
  ): void {
    this.budget.syncUserAssignments(userId, projectIds).subscribe({
      next: () => this.finishSave(messageKey),
      error: () => {
        this.toast.error(this.t('budget.projects.assignment-error'));
        this.isLoading.set(false);
      },
    });
  }

  onSubmit(): void {
    if (!this.budgetUserForm || !this.budgetUserForm.isFormValid()) {
      this.toast.error(this.t('budget.users.fill-required'));
      return;
    }

    this.isLoading.set(true);
    const formData = { ...this.budgetUserForm.getFormData() };
    const projectIds = (formData.assigned_project_ids as number[]) ?? [];
    delete formData.assigned_project_ids;

    if (this.isEdit() && !formData.password) {
      delete formData.password;
    }

    if (this.isEdit() && this.userId) {
      this.budget.updateBudgetUser(this.userId, formData).subscribe({
        next: () =>
          this.syncAssignmentsThenFinish(this.userId!, projectIds, 'budget.users.update-success'),
        error: (err) => {
          const errors = err?.error;
          if (errors && typeof errors === 'object') {
            this.budgetUserForm.setServerErrors(errors);
          } else {
            this.toast.error(this.t('budget.users.update-error'));
          }
          this.isLoading.set(false);
        },
      });
    } else {
      this.budget.createBudgetUser(formData).subscribe({
        next: (user) => {
          if (projectIds.length > 0) {
            this.syncAssignmentsThenFinish(user.id, projectIds, 'budget.users.create-success');
          } else {
            this.finishSave('budget.users.create-success');
          }
        },
        error: (err) => {
          const errors = err?.error;
          if (errors && typeof errors === 'object') {
            this.budgetUserForm.setServerErrors(errors);
          } else {
            this.toast.error(this.t('budget.users.create-error'));
          }
          this.isLoading.set(false);
        },
      });
    }
  }
}
