import {
  Component,
  OnInit,
  ViewChild,
  inject,
  signal,
  computed,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Validators } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import {
  BuilderService,
  SubMainSection,
  Title,
  TitleCategory,
  MainSection,
} from '../../core/services/builder.service';
import { User } from '../../core/models';
import {
  DynamicFormComponent,
  FormConfig,
  FormFieldConfig,
} from '../../shared/components/dynamic-form/dynamic-form.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [CommonModule, DynamicFormComponent, PageHeaderComponent],
  template: `
    <div class="page-container">
      <app-page-header
        [title]="isEdit() ? t('user-form.title-edit') : t('user-form.title-new')"
        [description]="isEdit() ? t('user-form.subtitle-edit') : t('user-form.subtitle-new')"
        [action]="backAction"
      ></app-page-header>
      <app-example-form
        #userForm
        [formConfig]="formConfig()"
        (fieldChange)="onFieldChange($event)"
        (submit)="onSubmit()"
      ></app-example-form>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './user-form.component.scss',
})
export class UserFormComponent implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private builder = inject(BuilderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  @ViewChild('userForm') userForm!: DynamicFormComponent;

  // moeds portal (Ministry of Energy) sectors. One static multi-select; the
  // per-sector view/write access follows the «view/edit data» checkboxes.
  // Mirrors the backend User.PORTAL_SECTORS.
  private readonly portalSectorOptions = [
    { value: 'water', labelKey: 'user-form.sector-water' },
    { value: 'electricity', labelKey: 'user-form.sector-electricity' },
    { value: 'oil_gas', labelKey: 'user-form.sector-oil-gas' },
    { value: 'mineral', labelKey: 'user-form.sector-mineral' },
    { value: 'projects', labelKey: 'user-form.sector-projects' },
  ];

  isEdit = signal(false);
  userId: number | null = null;
  isLoading = signal(false);
  mainSections = signal<MainSection[]>([]);
  subSections = signal<SubMainSection[]>([]);
  titles = signal<Title[]>([]);
  titleCategories = signal<TitleCategory[]>([]);
  filteredSubSections = signal<SubMainSection[]>([]);
  filteredTitles = signal<Title[]>([]);

  // computed rebuilds when language or data signals change; trackBy on field.key
  // keeps DOM stable so option updates do not scroll the page to the top.
  formConfig = computed<FormConfig>(() => {
    const mainSectionOptions = this.mainSections().map((m) => ({ value: m.id, label: m.name }));
    const subSectionOptions = this.filteredSubSections().map((s) => ({
      value: s.id,
      label: s.name,
    }));
    const titleCategoryOptions = this.titleCategories().map((c) => ({
      value: c.id,
      label: c.name,
    }));
    const titleOptions = this.filteredTitles().map((t) => ({
      value: t.id,
      label: t.name,
    }));

    const allFields: FormFieldConfig[] = [
      {
        key: 'section_account',
        type: 'section',
        label: this.t('user-form.section-account'),
      },
      {
        key: 'username',
        type: 'input',
        label: this.t('user-form.username'),
        placeholder: this.t('user-form.username-placeholder'),
        inputType: 'text',
        required: true,
        validators: [Validators.required],
        disabled: this.isEdit(),
      },
      ...(!this.isEdit()
        ? [
            {
              key: 'password',
              type: 'input' as const,
              label: this.t('user-form.password'),
              placeholder: this.t('user-form.password-placeholder'),
              inputType: 'password' as const,
              required: true,
              validators: [Validators.required, Validators.minLength(6)],
            },
          ]
        : []),
      {
        key: 'first_name',
        type: 'input',
        label: this.t('user-form.first-name'),
        placeholder: this.t('user-form.first-name-placeholder'),
        inputType: 'text',
      },
      {
        key: 'last_name',
        type: 'input',
        label: this.t('user-form.last-name'),
        placeholder: this.t('user-form.last-name-placeholder'),
        inputType: 'text',
      },
      {
        key: 'email',
        type: 'input',
        label: this.t('user-form.email'),
        placeholder: this.t('user-form.email-placeholder'),
        inputType: 'email',
        validators: [Validators.email],
      },
      {
        key: 'is_active',
        type: 'checkbox',
        label: this.t('user-form.is-active'),
        defaultValue: true,
      },

      {
        key: 'section_report_perms',
        type: 'section',
        label: this.t('user-form.section-report-perms'),
      },
      {
        key: 'can_view_info',
        type: 'checkbox',
        label: this.t('user-form.can-view'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_view_info && !this.auth.isAdmin(),
      },
      {
        key: 'can_write_info',
        type: 'checkbox',
        label: this.t('user-form.can-write'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_write_info && !this.auth.isAdmin(),
      },
      {
        key: 'can_confirm_info',
        type: 'checkbox',
        label: this.t('user-form.can-confirm'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_confirm_info && !this.auth.isAdmin(),
      },
      {
        key: 'can_export_reports',
        type: 'checkbox',
        label: this.t('user-form.can-export'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_export_reports && !this.auth.isAdmin(),
      },
      {
        key: 'can_add_user',
        type: 'checkbox' as const,
        label: this.t('user-form.can-add-user'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_add_user && !this.auth.isAdmin(),
      },

      {
        key: 'section_portal',
        type: 'section',
        label: this.t('user-form.section-portal'),
      },
      {
        key: 'portal_sectors',
        type: 'multi-select',
        label: this.t('user-form.portal-sectors'),
        placeholder: this.t('user-form.portal-sectors-placeholder'),
        hint: this.t('user-form.portal-sectors-hint'),
        defaultValue: [],
        fullWidth: true,
        options: this.portalSectorOptions.map((o) => ({
          value: o.value,
          label: this.t(o.labelKey),
        })),
      },
      {
        key: 'can_manage_datasets',
        type: 'checkbox',
        label: this.t('user-form.portal-manage-datasets'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_manage_datasets && !this.auth.isAdmin(),
      },
      {
        key: 'can_manage_control_panel',
        type: 'checkbox',
        label: this.t('user-form.portal-manage-control-panel'),
        defaultValue: false,
        disabled: !this.auth.currentUser()?.can_manage_control_panel && !this.auth.isAdmin(),
      },

      {
        key: 'section_scope',
        type: 'section',
        label: this.t('user-form.section-scope'),
      },
      {
        key: 'main_section_ids',
        type: 'multi-select',
        label: this.t('user-form.main-sections'),
        placeholder: this.t('user-form.main-sections-placeholder'),
        hint: this.t('user-form.main-sections-hint'),
        fullWidth: true,
        options: mainSectionOptions,
      },
      {
        key: 'sub_main_ids',
        type: 'multi-select',
        label: this.t('user-form.sub-sections'),
        placeholder: this.t('user-form.sub-sections-placeholder'),
        hint: this.t('user-form.sub-sections-hint'),
        fullWidth: true,
        options: subSectionOptions,
      },
      {
        key: 'title_category_ids',
        type: 'multi-select',
        label: this.t('user-form.title-categories'),
        placeholder: this.t('user-form.title-categories-placeholder'),
        hint: this.t('user-form.title-categories-hint'),
        fullWidth: true,
        options: titleCategoryOptions,
      },
      {
        key: 'title_ids',
        type: 'multi-select',
        label: this.t('user-form.titles'),
        placeholder: this.t('user-form.titles-placeholder'),
        hint: this.t('user-form.titles-hint'),
        fullWidth: true,
        options: titleOptions,
      },
    ];

    return {
      title: this.isEdit() ? this.t('user-form.title-edit') : this.t('user-form.title-new'),
      subtitle: this.isEdit()
        ? this.t('user-form.subtitle-edit')
        : this.t('user-form.subtitle-new'),
      hideTitle: true,
      compact: true,
      fields: allFields,
      showDebug: false,
    };
  });

  get backAction() {
    return {
      label: this.t('form.back'),
      icon: 'arrow_back',
      routerLink: '/users',
      variant: 'ghost' as const,
    };
  }

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params['id']) {
        this.userId = params['id'];
        this.isEdit.set(true);
      }
      this.loadAllThenUser();
    });
  }

  onFieldChange(event: { key: string; value: any }): void {
    if (event.key === 'main_section_ids') {
      this.onMainSectionChange(event.value);
    }
    if (event.key === 'title_category_ids') {
      this.onTitleCategoryChange(event.value);
    }
  }

  private onMainSectionChange(selectedMainIds: number[], skipReset = false): void {
    let filtered: SubMainSection[] = [];
    if (selectedMainIds && selectedMainIds.length > 0) {
      filtered = this.subSections().filter((s: any) =>
        selectedMainIds.includes(s.main_section ?? s.main_section_id),
      );
    }
    this.filteredSubSections.set(filtered);

    if (!skipReset) {
      // Main is a filter + shortcut: selecting mains fills every leaf under them
      // (including «تحديد الكل» on main). Clearing mains clears sub assignments.
      const leafIds = filtered.map((s) => s.id);
      this.userForm?.userForm?.get('sub_main_ids')?.setValue(leafIds, { emitEvent: false });
    }
  }

  private onTitleCategoryChange(selectedCategoryIds: number[], skipReset = false): void {
    let filtered: Title[] = [];
    if (selectedCategoryIds && selectedCategoryIds.length > 0) {
      filtered = this.titles().filter((t) => selectedCategoryIds.includes(t.category as number));
    }
    this.filteredTitles.set(filtered);

    if (!skipReset) {
      // Category filters + auto-fills all titles under the selection (same as main→sub).
      const titleIds = filtered.map((t) => t.id);
      this.userForm?.userForm?.get('title_ids')?.setValue(titleIds, { emitEvent: false });
    }
  }

  private loadAllThenUser(): void {
    forkJoin({
      mainSections: this.builder.getMainSections(),
      // Assignable sections only — parents reject UserSubMain on the backend.
      subSections: this.builder.getSubMainSections({ leaves: true }),
      titleCategories: this.builder.getTitleCategories(),
      titles: this.builder.getTitles(),
    }).subscribe({
      next: ({ mainSections, subSections, titleCategories, titles }) => {
        const subs = (subSections.results || []).filter((s) => s.is_leaf !== false);
        this.subSections.set(subs);
        this.titleCategories.set(titleCategories.results || []);
        this.titles.set(titles.results || []);

        // Only show main sections that are parents of leaf sub-sections
        const visibleMainIds = new Set(subs.map((s: any) => s.main_section ?? s.main_section_id));
        this.mainSections.set(
          (mainSections.results || []).filter((m: any) => visibleMainIds.has(m.id)),
        );

        if (this.userId) {
          this.loadUser();
        }
      },
      error: () => this.toast.error(this.t('users.load-data-error')),
    });
  }

  private loadUser(): void {
    if (!this.userId) return;
    this.api.get<User>(`/users/${this.userId}/`).subscribe({
      next: (user) => {
        const userSubIds = user.sub_main_ids ?? [];
        const derivedMainIds = [
          ...new Set(
            this.subSections()
              .filter((s: any) => userSubIds.includes(s.id))
              .map((s: any) => s.main_section ?? s.main_section_id)
              .filter(Boolean),
          ),
        ] as number[];

        const categoryIds = user.title_category_ids ?? [];
        this.onMainSectionChange(derivedMainIds, true);
        this.onTitleCategoryChange(categoryIds, true);

        setTimeout(() => {
          this.userForm?.userForm?.patchValue({
            username: user.username,
            first_name: user.first_name,
            last_name: user.last_name,
            email: user.email,
            is_active: user.is_active,
            can_write_info: user.can_write_info,
            can_view_info: user.can_view_info,
            can_confirm_info: user.can_confirm_info,
            can_export_reports: user.can_export_reports,
            can_add_user: user.can_add_user,
            portal_sectors: user.portal_sectors ?? [],
            can_manage_datasets: user.can_manage_datasets,
            can_manage_control_panel: user.can_manage_control_panel,
            main_section_ids: derivedMainIds,
            sub_main_ids: userSubIds,
            title_category_ids: categoryIds,
            title_ids: user.title_ids ?? [],
          });
        }, 50);
      },
      error: () => this.toast.error(this.t('users.load-user-error')),
    });
  }

  onSubmit(): void {
    if (!this.userForm || !this.userForm.isFormValid()) {
      this.toast.error(this.t('users.fill-required'));
      return;
    }

    const formData = this.userForm.getFormData();
    const mainIds = Array.isArray(formData.main_section_ids)
      ? formData.main_section_ids
      : formData.main_section_ids
        ? [formData.main_section_ids]
        : [];
    const subIds = Array.isArray(formData.sub_main_ids)
      ? formData.sub_main_ids
      : formData.sub_main_ids
        ? [formData.sub_main_ids]
        : [];

    const categoryIds = Array.isArray(formData.title_category_ids)
      ? formData.title_category_ids
      : formData.title_category_ids
        ? [formData.title_category_ids]
        : [];
    const titleIds = Array.isArray(formData.title_ids)
      ? formData.title_ids
      : formData.title_ids
        ? [formData.title_ids]
        : [];

    if (mainIds.length > 0 && subIds.length === 0) {
      this.toast.error(this.t('user-form.sub-sections-required-when-main'));
      return;
    }
    if (categoryIds.length > 0 && titleIds.length === 0) {
      this.toast.error(this.t('user-form.titles-required-when-category'));
      return;
    }

    this.isLoading.set(true);

    delete formData.main_section_ids;
    delete formData.is_admin;

    if (!Array.isArray(formData.portal_sectors)) {
      formData.portal_sectors = formData.portal_sectors ? [formData.portal_sectors] : [];
    }
    formData.sub_main_ids = subIds;
    formData.title_category_ids = categoryIds;
    formData.title_ids = titleIds;

    if (this.isEdit() && this.userId) {
      this.api.patch(`/users/${this.userId}/`, formData).subscribe({
        next: () => {
          this.toast.success(this.t('users.update-success'));
          this.router.navigate(['/users']);
        },
        error: (err) => {
          const errors = err?.error;
          if (errors && typeof errors === 'object') {
            this.userForm.setServerErrors(errors);
          } else {
            this.toast.error(this.t('users.update-error'));
          }
          this.isLoading.set(false);
        },
      });
    } else {
      this.api.post('/users/', formData).subscribe({
        next: () => {
          this.toast.success(this.t('users.create-success'));
          this.router.navigate(['/users']);
        },
        error: (err) => {
          const errors = err?.error;
          if (errors && typeof errors === 'object') {
            this.userForm.setServerErrors(errors);
          } else {
            this.toast.error(this.t('users.create-error'));
          }
          this.isLoading.set(false);
        },
      });
    }
  }
}
