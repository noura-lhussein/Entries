import { Component, OnInit, inject, signal, computed, effect, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { catchError, forkJoin, map, of, switchMap, Observable } from 'rxjs';
import {
  BuilderService,
  Attribute,
  City,
  District,
  SubDistrictOption,
  CommunityOption,
  MainSection,
  Option,
  SubMainSection,
  Title,
  TitleCategory,
  sortTitlesByOrder,
} from '../../core/services/builder.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import {
  DynamicFormComponent,
  FormConfig,
} from '../../shared/components/dynamic-form/dynamic-form.component';
import { TableComponent, TableColumn } from '../../shared/components/table/table.component';
import {
  buildFormFieldsFromAttributes,
  getCommunityAttributeKey,
  getDistrictAttributeKey,
  getEffectiveCityFieldKey,
  getSubDistrictAttributeKey,
  isLocationAttributeType,
} from './builder-attribute-fields';
import { ENTITY_ATTRIBUTE_TYPES } from './entity-attribute-types';
import { collectNonEmptyAttributeValues } from './builder-submit.utils';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { FormCheckboxComponent } from '../../shared/components/form-checkbox/form-checkbox.component';
import { TitleExcelActionsComponent } from '../../shared/components/title-excel-actions/title-excel-actions.component';
import { AssignedUsersDialogComponent } from '../../shared/components/assigned-users-dialog/assigned-users-dialog.component';
import { DataEntryWorkspaceComponent } from '../data-entry/data-entry-workspace.component';

type CrudLevel = 'main' | 'sub' | 'title' | 'category';

@Component({
  selector: 'app-builder',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    ModalComponent,
    ButtonComponent,
    FormInputComponent,
    FormSelectComponent,
    FormCheckboxComponent,
    TitleExcelActionsComponent,
    DataEntryWorkspaceComponent,
  ],
  templateUrl: './builder.component.html',
  styleUrls: ['./builder.component.scss'],
})
export class BuilderComponent implements OnInit {
  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private matDialog = inject(MatDialog);
  translation = inject(TranslationService);

  crudModalVisible = signal(false);
  deleteModalVisible = signal(false);
  attributeModalVisible = signal(false);
  optionsModalVisible = signal(false);

  mainSections = signal<MainSection[]>([]);
  subSections = signal<SubMainSection[]>([]);
  titles = signal<Title[]>([]);
  titleCategories = signal<TitleCategory[]>([]);
  selectedCategory = signal<number | null>(null);
  attributes = signal<Attribute[]>([]);
  cities = signal<City[]>([]);
  districts = signal<District[]>([]);
  subdistricts = signal<SubDistrictOption[]>([]);
  communities = signal<CommunityOption[]>([]);
  entityOptionsByType = signal<Record<string, { id: number; name: string }[]>>({});
  selectedCityId = signal<number | null>(null);
  selectedDistrictId = signal<number | null>(null);
  selectedSubdistrictId = signal<number | null>(null);

  selectedMain = signal<number | null>(null);
  selectedSub = signal<number | null>(null);
  selectedTitle = signal<number | null>(null);
  sectionsMode = signal(false);

  loading = signal(false);
  userAllAttributes = signal<Attribute[]>([]);
  titleFormVisibility = signal<Record<number, boolean>>({});
  titleSubmittingMap = signal<Record<number, boolean>>({});
  titleRowsMap = signal<Record<number, Record<string, unknown>[]>>({});
  isAdmin = computed(() => this.auth.isAdmin());
  canWrite = computed(() => {
    const u = this.auth.currentUser();
    return u ? u.is_admin || u.can_write_info : false;
  });

  private dataLoaded = false;
  private allowedSubMainIds = signal<number[]>([]);
  private allowedTitleIds = signal<number[]>([]);

  titleEntryFormConfigs = computed<Record<number, FormConfig>>(() => {
    const result: Record<number, FormConfig> = {};
    for (const t of this.titles()) {
      result[t.id] = this.buildTitleEntryFormConfig(t.id);
    }
    return result;
  });

  attributeTypeSelectOptions = computed((): SelectOption[] => {
    const t = (key: string) => this.translation.t(key);
    return [
      { value: 'text', label: t('builder.text') },
      { value: 'textarea', label: t('builder.textarea') },
      { value: 'number', label: t('builder.number') },
      { value: 'date', label: t('builder.date') },
      { value: 'boolean', label: t('builder.boolean') },
      { value: 'select', label: t('builder.select') },
      { value: 'city', label: t('builder.city') },
      { value: 'district', label: t('builder.district') },
      { value: 'sub_district', label: t('locations.subdistrict') },
      { value: 'community', label: t('locations.community') },
      ...ENTITY_ATTRIBUTE_TYPES.map((value) => ({
        value,
        label: t(`builder.${value}`),
      })),
      { value: 'image', label: t('builder.image') },
      { value: 'file', label: t('builder.file') },
    ];
  });

  crudLevel: CrudLevel = 'main';
  crudAction: 'add' | 'edit' = 'add';
  crudId = 0;
  crudName = '';
  crudOrder = 1;
  crudCategoryId: number | null = null;

  titleSelectGroups = computed(() => {
    const cats = this.titleCategories();
    const titles = this.titles();
    const byCat = new Map<number | null, Title[]>();
    for (const t of titles) {
      const key = t.category ?? null;
      const list = byCat.get(key) || [];
      list.push(t);
      byCat.set(key, list);
    }
    const groups: { key: string; label: string; titles: Title[] }[] = [];
    for (const cat of cats) {
      const rows = byCat.get(cat.id) || [];
      if (rows.length) {
        groups.push({
          key: `c-${cat.id}`,
          label: cat.name,
          titles: sortTitlesByOrder(rows),
        });
      }
    }
    const uncategorized = byCat.get(null) || [];
    if (uncategorized.length) {
      groups.push({
        key: 'none',
        label: this.translation.t('builder.uncategorized'),
        titles: sortTitlesByOrder(uncategorized),
      });
    }
    return groups;
  });

  categorySelectOptions = computed((): SelectOption[] => {
    const opts: SelectOption[] = [
      { value: null, label: this.translation.t('builder.no-category') },
    ];
    for (const c of this.titleCategories()) {
      opts.push({ value: c.id, label: c.name });
    }
    return opts;
  });

  deleteLevel: CrudLevel | 'attribute' = 'main';
  deleteId = 0;

  attrForm = {
    id: 0,
    label: '',
    type: 'text' as Attribute['type'],
    required: false,
    unit_ar: '',
  };
  attributeOptions: { id?: number; label: string }[] = [];
  private originalOptionIds: number[] = [];
  attributeOptionsLoading = signal(false);
  newOption = { label: '' };

  selectedTitleName = computed(() => {
    const id = this.selectedTitle();
    if (id == null) return '';
    return this.titles().find((t) => t.id === id)?.name ?? '';
  });

  crudTitle = computed(() => {
    const action =
      this.crudAction === 'add'
        ? this.translation.t('builder.add')
        : this.translation.t('builder.edit');
    const names: Record<CrudLevel, string> = {
      main: this.translation.t('builder.mainnSections'),
      sub: this.translation.t('builder.subSections'),
      title: this.translation.t('builder.title'),
      category: this.translation.t('builder.title-category'),
    };
    return `${action} ${names[this.crudLevel]}`;
  });

  constructor() {
    // Wait until the authenticated user is resolved before loading data.
    // This prevents the race condition where currentUser() is null on hard
    // reload, causing isAdmin() to be wrong and loading all sections.
    effect(() => {
      if (this.auth.currentUser() && !this.dataLoaded) {
        this.dataLoaded = true;
        untracked(() => {
          this.loadData();
          if (this.isAdmin()) {
            this.toast.info(this.translation.t('builder.management-mode'));
          } else {
            this.toast.info(this.translation.t('builder.data-entry'));
          }
        });
      }
    });
  }

  ngOnInit(): void {
    this.sectionsMode.set(this.router.url.startsWith('/sections-manage'));
  }

  loadData(): void {
    const isAdmin = this.isAdmin();

    if (isAdmin) {
      this.loadMainSections();
      this.loadTitleCategories();
      this.loadTitles();
    } else {
      // للمستخدمين العاديين، حمّل البيانات المصرح لهم بها فقط
      this.loadUserPermissions();
    }
  }

  private loadUserPermissions(): void {
    this.builder
      .getUserPermissions()
      .pipe(
        switchMap((perms) => {
          this.allowedSubMainIds.set(perms.sub_main_ids || []);
          this.allowedTitleIds.set(perms.title_ids || []);

          const subMainIdsRaw = perms.sub_main_ids || [];
          const titleIdsRaw = perms.title_ids || [];

          return forkJoin({
            mains: this.builder
              .getMainSections()
              .pipe(catchError(() => of({ results: [] as MainSection[] }))),
            subs: this.builder
              .getSubMainSections()
              .pipe(catchError(() => of({ results: [] as SubMainSection[] }))),
            titles: this.builder.getTitles().pipe(catchError(() => of({ results: [] as Title[] }))),
            attrs: this.builder
              .getAllAttributes()
              .pipe(catchError(() => of({ results: [] as Attribute[] }))),
          }).pipe(
            map(({ mains, subs, titles, attrs }) => {
              const subIdSet = new Set(
                subMainIdsRaw
                  .map((x: unknown) => Number(x))
                  .filter((n: number) => !Number.isNaN(n)),
              );
              const titleIdSet = new Set(
                titleIdsRaw.map((x: unknown) => Number(x)).filter((n: number) => !Number.isNaN(n)),
              );
              const allowedSubs = (subs.results || []).filter((s: SubMainSection) =>
                subIdSet.has(Number(s.id)),
              );
              const allowedTitles = (titles.results || []).filter((t: Title) =>
                titleIdSet.has(Number(t.id)),
              );
              const normalized = (attrs.results || []).map((a: Attribute & { title?: unknown }) => {
                const tid = this.coalesceNumericId(a.title_id ?? a.title);
                return { ...a, title_id: tid ?? 0 } as Attribute;
              });
              return {
                mainSections: mains.results || [],
                allowedSubs,
                allowedTitles,
                normalized,
              };
            }),
          );
        }),
      )
      .subscribe({
        next: ({ mainSections, allowedSubs, allowedTitles, normalized }) => {
          this.mainSections.set(mainSections);
          this.subSections.set(allowedSubs);
          this.titles.set(sortTitlesByOrder(allowedTitles));
          this.userAllAttributes.set(normalized);
          this.initializeTitleFormVisibility();
          this.loadLocations();
        },
        error: () => this.toast.error(this.translation.t('builder.title')),
      });
  }

  loadMainSections(): void {
    this.builder.getMainSections().subscribe({
      next: (data) => this.mainSections.set(data.results || []),
      error: () => this.toast.error(this.translation.t('builder.title')),
    });
  }

  loadSubSections(mainId: number): void {
    this.builder.getSubMainSections(mainId).subscribe({
      next: (data) => {
        let subs = data.results || [];
        // For data entry users, filter sub-sections based on their permissions
        if (!this.isAdmin()) {
          const allowedIds = this.allowedSubMainIds();
          subs = subs.filter((s) => allowedIds.includes(s.id));
        }
        this.subSections.set(subs);
      },
      error: () => this.toast.error(this.translation.t('builder.subSections')),
    });
  }

  loadTitleCategories(): void {
    this.builder.getTitleCategories().subscribe({
      next: (data) => this.titleCategories.set(data.results || []),
      error: () => this.titleCategories.set([]),
    });
  }

  loadTitles(): void {
    this.builder.getTitles().subscribe({
      next: (data) => this.titles.set(data.results || []),
      error: () => this.toast.error(this.translation.t('builder.title')),
    });
  }

  loadAttributes(titleId: number): void {
    this.loading.set(true);
    this.builder.getAttributes(titleId).subscribe({
      next: (data) => {
        const attrs = data.results || [];
        this.attributes.set(attrs);

        this.selectedCityId.set(null);
        this.selectedDistrictId.set(null);
        this.selectedSubdistrictId.set(null);
        this.districts.set([]);
        this.subdistricts.set([]);
        this.communities.set([]);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error(this.translation.t('builder.field-name'));
        this.loading.set(false);
      },
    });
  }

  onMainChange(value: number | null): void {
    this.selectedMain.set(value);
    this.selectedSub.set(null);
    this.subSections.set([]);
    if (value) this.loadSubSections(value);
  }

  onSubChange(value: number | null): void {
    if (this.selectedSub() === value) {
      return;
    }
    this.selectedSub.set(value);
    this.selectedCityId.set(null);
    this.selectedDistrictId.set(null);
    this.selectedSubdistrictId.set(null);
    this.districts.set([]);
    this.subdistricts.set([]);
    this.communities.set([]);
    if (!this.isAdmin()) {
      this.loadUserInfoRowsForSub(value);
      this.initializeTitleFormVisibility();
    }
  }

  onTitleChange(value: number | null): void {
    this.selectedTitle.set(value);
    this.attributes.set([]);
    this.selectedCityId.set(null);
    this.selectedDistrictId.set(null);
    this.selectedSubdistrictId.set(null);
    this.districts.set([]);
    this.subdistricts.set([]);
    this.communities.set([]);
    if (value) this.loadAttributes(value);
  }

  openTitleAssignedUsers(): void {
    const titleId = this.selectedTitle();
    if (!titleId) return;
    this.builder.getTitleAssignedUsers(titleId).subscribe({
      next: (users) => {
        this.matDialog.open(AssignedUsersDialogComponent, {
          data: {
            contextLabel: this.selectedTitleName(),
            users: users || [],
          },
          width: 'min(560px, 94vw)',
          maxHeight: '90vh',
        });
      },
      error: () => this.toast.error(this.translation.t('assigned-users.load-error')),
    });
  }

  openCrud(level: CrudLevel, action: 'add' | 'edit'): void {
    this.crudLevel = level;
    this.crudAction = action;
    this.crudCategoryId = null;
    if (action === 'edit') {
      const item = this.getCurrentItem(level);
      if (!item) return;
      this.crudId = item.id;
      this.crudName = item.name;
      if (level === 'title' || level === 'category') {
        this.crudOrder = item.order ?? 1;
      }
      if (level === 'title') {
        this.crudCategoryId = item.category ?? null;
      }
    } else {
      this.crudId = 0;
      this.crudName = '';
      if (level === 'title') {
        this.crudCategoryId = this.selectedCategory();
        this.crudOrder = this.nextTitleOrderForCategory(this.crudCategoryId);
      } else if (level === 'category') {
        const orders = this.titleCategories().map((c) => c.order);
        this.crudOrder = orders.length ? Math.max(...orders) + 1 : 1;
      }
    }
    this.crudModalVisible.set(true);
  }

  onCrudCategoryChange(categoryId: number | null): void {
    this.crudCategoryId = categoryId;
    if (this.crudLevel === 'title' && this.crudAction === 'add') {
      this.crudOrder = this.nextTitleOrderForCategory(categoryId);
    }
  }

  private nextTitleOrderForCategory(categoryId: number | null): number {
    const orders = this.titles()
      .filter((t) => (t.category ?? null) === categoryId)
      .map((t) => t.order);
    return orders.length ? Math.max(...orders) + 1 : 1;
  }

  closeCrud(): void {
    this.crudModalVisible.set(false);
  }

  saveCrud(): void {
    if (!this.crudName.trim()) {
      this.toast.error(this.translation.t('builder.mainnSections'));
      return;
    }
    let req;

    if (this.crudLevel === 'main') {
      const data = { name: this.crudName.trim() };
      req = this.crudId
        ? this.builder.updateMainSection(this.crudId, data)
        : this.builder.createMainSection(data);
    } else if (this.crudLevel === 'sub') {
      const data = { name: this.crudName.trim() };
      const mainId = this.selectedMain();
      if (!mainId) {
        this.toast.error(this.translation.t('builder.title'));
        return;
      }
      req = this.crudId
        ? this.builder.updateSubMainSection(this.crudId, data)
        : this.builder.createSubMainSection({ ...data, main_section_id: mainId });
    } else if (this.crudLevel === 'category') {
      const order = Math.trunc(Number(this.crudOrder));
      if (!Number.isFinite(order) || order < 1) {
        this.toast.error(this.translation.t('builder.title-order-invalid'));
        return;
      }
      const data = { name: this.crudName.trim(), order };
      req = this.crudId
        ? this.builder.updateTitleCategory(this.crudId, data)
        : this.builder.createTitleCategory(data);
    } else {
      const order = Math.trunc(Number(this.crudOrder));
      if (!Number.isFinite(order) || order < 1) {
        this.toast.error(this.translation.t('builder.title-order-invalid'));
        return;
      }
      const data = {
        name: this.crudName.trim(),
        order,
        category: this.crudCategoryId,
      };
      req = this.crudId
        ? this.builder.updateTitle(this.crudId, data)
        : this.builder.createTitle(data);
    }

    req.subscribe({
      next: () => {
        this.toast.success(this.translation.t('user-data.update-success'));
        this.closeCrud();
        this.refresh(this.crudLevel);
      },
      error: () => this.toast.error(this.translation.t('user-data.update-error')),
    });
  }

  openDelete(level: CrudLevel): void {
    const item = this.getCurrentItem(level);
    if (!item) return;
    this.deleteLevel = level;
    this.deleteId = item.id;
    this.deleteModalVisible.set(true);
  }

  openDeleteAttribute(id: number): void {
    this.deleteLevel = 'attribute';
    this.deleteId = id;
    this.deleteModalVisible.set(true);
  }

  closeDelete(): void {
    this.deleteModalVisible.set(false);
  }

  confirmDelete(): void {
    let req;
    if (this.deleteLevel === 'main') req = this.builder.deleteMainSection(this.deleteId);
    else if (this.deleteLevel === 'sub') req = this.builder.deleteSubMainSection(this.deleteId);
    else if (this.deleteLevel === 'category') req = this.builder.deleteTitleCategory(this.deleteId);
    else if (this.deleteLevel === 'title') req = this.builder.deleteTitle(this.deleteId);
    else req = this.builder.deleteAttribute(this.deleteId);

    req.subscribe({
      next: () => {
        this.toast.success(this.translation.t('user-data.delete-success'));
        this.closeDelete();
        if (this.deleteLevel === 'attribute') {
          const titleId = this.selectedTitle();
          if (titleId) this.loadAttributes(titleId);
        } else {
          this.refresh(this.deleteLevel);
        }
      },
      error: (err) => this.toast.error(this.deleteErrorMessage(err)),
    });
  }

  private deleteErrorMessage(err: { error?: { detail?: unknown } }): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    return this.translation.t('builder.delete-blocked-has-data');
  }

  openAttribute(attr: Attribute | null): void {
    this.attributeOptions = [];
    this.originalOptionIds = [];

    if (attr) {
      this.attrForm = {
        id: attr.id,
        label: attr.label,
        type: attr.type,
        required: attr.required,
        unit_ar: attr.unit_ar ?? '',
      };
      if (attr.type === 'select') {
        this.loadAttributeOptions(attr);
      }
    } else {
      this.attrForm = { id: 0, label: '', type: 'text', required: false, unit_ar: '' };
    }
    this.attributeModalVisible.set(true);
  }

  private loadAttributeOptions(attr: Attribute): void {
    const applyOptions = (options: Option[]) => {
      this.attributeOptions = options.map((option) => ({
        id: option.id,
        label: option.label,
      }));
      this.originalOptionIds = options.map((option) => option.id);
    };

    if (attr.options?.length) {
      applyOptions(attr.options);
      return;
    }

    this.attributeOptionsLoading.set(true);
    this.builder.getOptions(attr.id).subscribe({
      next: (res) => {
        applyOptions(res.results || []);
        this.attributeOptionsLoading.set(false);
      },
      error: () => {
        this.attributeOptionsLoading.set(false);
        this.toast.error(this.translation.t('user-data.load-error'));
      },
    });
  }

  closeAttribute(): void {
    this.closeOptionsDialog();
    this.attributeOptions = [];
    this.originalOptionIds = [];
    this.attributeOptionsLoading.set(false);
    this.attributeModalVisible.set(false);
  }

  saveAttribute(): void {
    if (!this.attrForm.label.trim()) {
      this.toast.error(this.translation.t('builder.field-name'));
      return;
    }
    if (this.attrForm.type === 'select' && this.attributeOptions.length === 0) {
      this.toast.error(this.translation.t('builder.no-options'));
      return;
    }

    const titleId = this.selectedTitle();
    if (!titleId) return;

    const data = {
      title: titleId,
      label: this.attrForm.label.trim(),
      type: this.attrForm.type,
      required: this.attrForm.required,
      unit_ar: this.attrForm.type === 'number' ? this.attrForm.unit_ar.trim() : '',
    };

    const req = this.attrForm.id
      ? this.builder.updateAttribute(this.attrForm.id, data)
      : this.builder.createAttribute(data);

    req.subscribe({
      next: (attr) => {
        if (this.attrForm.type === 'select') {
          this.syncOptions(attr.id, titleId);
        } else {
          this.finishAttributeSave(titleId);
        }
      },
      error: () => this.toast.error(this.translation.t('builder.save-error')),
    });
  }

  private finishAttributeSave(titleId: number): void {
    this.toast.success(this.translation.t('builder.save-success'));
    this.closeAttribute();
    this.loadAttributes(titleId);
  }

  private syncOptions(attributeId: number, titleId: number): void {
    const currentIds = new Set(
      this.attributeOptions.filter((option) => option.id != null).map((option) => option.id!),
    );
    const toDelete = this.originalOptionIds.filter((id) => !currentIds.has(id));
    const toCreate = this.attributeOptions.filter((option) => option.id == null);
    const toUpdate = this.attributeOptions.filter((option) => option.id != null);

    const requests: Observable<unknown>[] = [
      ...toDelete.map((id) => this.builder.deleteOption(id)),
      ...toCreate.map((option) =>
        this.builder.createOption({
          attribute_id: attributeId,
          label: option.label,
        }),
      ),
      ...toUpdate.map((option) =>
        this.builder.updateOption(option.id!, { label: option.label, value: option.label }),
      ),
    ];

    if (requests.length === 0) {
      this.toast.success(this.translation.t('builder.field-options-saved-success'));
      this.finishAttributeSave(titleId);
      return;
    }

    forkJoin(requests).subscribe({
      next: () => {
        this.toast.success(this.translation.t('builder.field-options-saved-success'));
        this.finishAttributeSave(titleId);
      },
      error: () => this.toast.error(this.translation.t('builder.options-save-error')),
    });
  }

  private initializeTitleFormVisibility(): void {
    const visibility: Record<number, boolean> = {};
    for (const t of this.titles()) {
      // Keep forms collapsed by default to avoid heavy render/freeze
      // when a sub-section has many titles.
      visibility[t.id] = false;
    }
    this.titleFormVisibility.set(visibility);
  }

  titleRows(titleId: number): Record<string, unknown>[] {
    return this.titleRowsMap()[titleId] ?? [];
  }

  titleRowsColumns(titleId: number): TableColumn[] {
    const attrs = this.getTitleAttributes(titleId);
    return attrs.map((a) => ({
      key: `attr_${a.id}`,
      label: a.label,
      type: 'media' as const,
    }));
  }

  isTitleFormVisible(titleId: number): boolean {
    return this.titleFormVisibility()[titleId] ?? true;
  }

  /** True when API returned at least one attribute linked to this title id. */
  titleHasFields(titleId: number): boolean {
    return this.getTitleAttributes(titleId).length > 0;
  }

  showTitleForm(titleId: number): void {
    this.titleFormVisibility.update((curr) => ({ ...curr, [titleId]: true }));
  }

  hideTitleForm(titleId: number): void {
    this.titleFormVisibility.update((curr) => ({ ...curr, [titleId]: false }));
  }

  titleSubmitting(titleId: number): boolean {
    return this.titleSubmittingMap()[titleId] ?? false;
  }

  private setTitleSubmitting(titleId: number, value: boolean): void {
    this.titleSubmittingMap.update((curr) => ({ ...curr, [titleId]: value }));
  }

  private getTitleAttributes(titleId: number): Attribute[] {
    const want = this.coalesceNumericId(titleId);
    if (want == null) return [];
    return this.userAllAttributes().filter((a) => this.coalesceNumericId(a.title_id) === want);
  }

  /** Coerce API ids (string/number/nested {id}) to a finite number or null. */
  private coalesceNumericId(value: unknown): number | null {
    if (value == null) return null;
    if (typeof value === 'object' && value !== null && 'id' in (value as Record<string, unknown>)) {
      const n = Number((value as { id: unknown }).id);
      return Number.isFinite(n) ? n : null;
    }
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  private buildTitleEntryFormConfig(titleId: number): FormConfig {
    const attrs = this.getTitleAttributes(titleId);
    const effectiveCityFieldKey = getEffectiveCityFieldKey(attrs);
    const fields = buildFormFieldsFromAttributes({
      attrs,
      location: {
        governorates: this.cities().map((c) => ({ id: c.id, name: c.name })),
        districts: this.districts().map((d) => ({ id: d.id, name: d.name })),
        subdistricts: this.subdistricts().map((s) => ({ id: s.id, name: s.name })),
        communities: this.communities().map((c) => ({ id: c.id, name: c.name })),
        selectedGovernorateId: this.selectedCityId(),
        selectedDistrictId: this.selectedDistrictId(),
        selectedSubdistrictId: this.selectedSubdistrictId(),
      },
      effectiveCityFieldKey,
      cityVirtualLabel: this.translation.t('builder.city'),
      entityOptionsByType: this.entityOptionsByType(),
    });

    return {
      title: this.translation.t('builder.data-entry'),
      subtitle: this.titles().find((t) => t.id === titleId)?.name ?? '',
      fields,
      hideSubmitButton: true,
    };
  }

  onTitleEntryFieldChange(
    titleId: number,
    titleForm: DynamicFormComponent,
    event: { key: string; value: string | number | null },
  ): void {
    const attrs = this.getTitleAttributes(titleId);
    const governorateKey = getEffectiveCityFieldKey(attrs);
    const districtKey = getDistrictAttributeKey(attrs);
    const subdistrictKey = getSubDistrictAttributeKey(attrs);
    const communityKey = getCommunityAttributeKey(attrs);

    const resetFormControl = (key: string | null) => {
      if (!key) return;
      titleForm.userForm?.get(key)?.reset();
    };

    if (governorateKey && event.key === governorateKey) {
      const govId = event.value ? Number(event.value) : null;
      const normalized = govId != null && !Number.isNaN(govId) ? govId : null;
      if (this.selectedCityId() === normalized) return;
      this.selectedCityId.set(normalized);
      this.selectedDistrictId.set(null);
      this.selectedSubdistrictId.set(null);
      if (normalized) {
        this.loadDistrictsByGovernorate(normalized);
      } else {
        this.districts.set([]);
      }
      this.subdistricts.set([]);
      this.communities.set([]);
      resetFormControl(districtKey);
      resetFormControl(subdistrictKey);
      resetFormControl(communityKey);
      return;
    }

    if (districtKey && event.key === districtKey) {
      const distId = event.value ? Number(event.value) : null;
      const normalized = distId != null && !Number.isNaN(distId) ? distId : null;
      if (this.selectedDistrictId() === normalized) return;
      this.selectedDistrictId.set(normalized);
      this.selectedSubdistrictId.set(null);
      if (normalized) {
        this.loadSubDistrictsByDistrict(normalized);
      } else {
        this.subdistricts.set([]);
      }
      this.communities.set([]);
      resetFormControl(subdistrictKey);
      resetFormControl(communityKey);
      return;
    }

    if (subdistrictKey && event.key === subdistrictKey) {
      const subId = event.value ? Number(event.value) : null;
      const normalized = subId != null && !Number.isNaN(subId) ? subId : null;
      if (this.selectedSubdistrictId() === normalized) return;
      this.selectedSubdistrictId.set(normalized);
      if (normalized) {
        this.loadCommunitiesBySubdistrict(normalized);
      } else {
        this.communities.set([]);
      }
      resetFormControl(communityKey);
    }
  }

  private loadUserInfoRowsForSub(_subId: number | null): void {
    // Session-only behavior: do not load old backend rows into this UI.
    this.titleRowsMap.set({});
  }

  submitTitleReport(titleId: number, titleForm: DynamicFormComponent): void {
    if (!this.canWrite()) {
      this.toast.error(this.translation.t('builder.no-entry-permission'));
      return;
    }
    const subId = this.selectedSub();
    if (!subId) {
      this.toast.error(this.translation.t('builder.select-sub-main'));
      return;
    }
    if (!titleForm || !titleForm.isFormValid()) {
      this.toast.error(this.translation.t('builder.complete-form-correctly'));
      return;
    }

    const attrs = this.getTitleAttributes(titleId);
    const formData = titleForm.getFormData() as Record<string, unknown>;
    const { attributeValues, displayRow } = collectNonEmptyAttributeValues(
      formData,
      attrs,
      (attr, raw) => this.resolveSubmittedValueByAttribute(attr, raw),
      { displayRowId: `tmp-${titleId}-${Date.now()}` },
    );

    if (!attributeValues.length) {
      this.toast.error(this.translation.t('builder.no-values-to-submit'));
      return;
    }

    this.setTitleSubmitting(titleId, true);
    this.builder
      .submitReport(titleId, {
        sub_main_id: subId,
        attribute_values: attributeValues,
      })
      .subscribe({
        next: () => {
          this.toast.success(this.translation.t('builder.report-saved-success'));
          this.titleRowsMap.update((curr) => ({
            ...curr,
            [titleId]: [...(curr[titleId] ?? []), displayRow!],
          }));
          titleForm.onReset();
          this.hideTitleForm(titleId);
          this.setTitleSubmitting(titleId, false);
        },
        error: () => {
          this.toast.error(this.translation.t('builder.report-save-error'));
          this.setTitleSubmitting(titleId, false);
        },
      });
  }

  private getCurrentItem(
    level: CrudLevel,
  ): { id: number; name: string; order?: number; category?: number | null } | null {
    if (level === 'main') {
      const id = this.selectedMain();
      return this.mainSections().find((m) => m.id === id) ?? null;
    }
    if (level === 'sub') {
      const id = this.selectedSub();
      return this.subSections().find((s) => s.id === id) ?? null;
    }
    if (level === 'category') {
      const id = this.selectedCategory();
      return this.titleCategories().find((c) => c.id === id) ?? null;
    }
    const id = this.selectedTitle();
    return this.titles().find((t) => t.id === id) ?? null;
  }

  private refresh(level: CrudLevel): void {
    if (level === 'main') {
      this.loadMainSections();
      this.selectedMain.set(null);
      this.selectedSub.set(null);
      this.subSections.set([]);
    } else if (level === 'sub') {
      const mainId = this.selectedMain();
      if (mainId) this.loadSubSections(mainId);
      this.selectedSub.set(null);
    } else if (level === 'category') {
      this.loadTitleCategories();
      this.selectedCategory.set(null);
      this.loadTitles();
    } else {
      this.loadTitles();
      this.selectedTitle.set(null);
      this.attributes.set([]);
    }
  }

  attributeModalTitle(): string {
    return this.attrForm.id
      ? this.translation.t('builder.edit-field')
      : this.translation.t('builder.add-new-field');
  }

  typeLabel(type: string): string {
    const keys: Record<string, string> = {
      text: 'builder.text',
      textarea: 'builder.textarea',
      number: 'builder.number',
      date: 'builder.date',
      boolean: 'builder.boolean',
      select: 'builder.select',
      city: 'builder.city',
      district: 'builder.district',
      sub_district: 'locations.subdistrict',
      community: 'locations.community',
      image: 'builder.image',
      file: 'builder.file',
    };
    const k = keys[type];
    return k ? this.translation.t(k) : type;
  }

  private loadLocations(): void {
    this.builder.getCities().subscribe({
      next: (data) => this.cities.set(data.results || []),
      error: () => this.cities.set([]),
    });
    this.districts.set([]);
    this.subdistricts.set([]);
    this.communities.set([]);
    this.loadEntityOptions();
  }

  private loadEntityOptions(): void {
    for (const entityType of ENTITY_ATTRIBUTE_TYPES) {
      this.builder.getEntityOptions(entityType, { limit: 500 }).subscribe({
        next: (rows) => {
          const mapped = (rows || []).map((r) => ({ id: r.id, name: r.label }));
          this.entityOptionsByType.update((prev) => ({ ...prev, [entityType]: mapped }));
        },
        error: () => {
          this.entityOptionsByType.update((prev) => ({ ...prev, [entityType]: [] }));
        },
      });
    }
  }

  private loadDistrictsByGovernorate(governorateId: number | null): void {
    if (!governorateId) {
      this.districts.set([]);
      return;
    }
    this.builder.getDistricts(governorateId).subscribe({
      next: (data) => this.districts.set(data.results || []),
      error: () => this.districts.set([]),
    });
  }

  private loadSubDistrictsByDistrict(districtId: number | null): void {
    if (!districtId) {
      this.subdistricts.set([]);
      return;
    }
    this.builder.getSubDistricts(districtId).subscribe({
      next: (data) => this.subdistricts.set(data.results || []),
      error: () => this.subdistricts.set([]),
    });
  }

  private loadCommunitiesBySubdistrict(subdistrictId: number | null): void {
    if (!subdistrictId) {
      this.communities.set([]);
      return;
    }
    this.builder.getCommunities(subdistrictId).subscribe({
      next: (data) => this.communities.set(data.results || []),
      error: () => this.communities.set([]),
    });
  }

  private resolveSubmittedValueByAttribute(
    attr: Attribute | undefined,
    rawValue: unknown,
  ): unknown {
    if (!attr) {
      return typeof rawValue === 'string' ? rawValue.trim() : rawValue;
    }

    if (attr && isLocationAttributeType(attr.type)) {
      return rawValue;
    }

    return typeof rawValue === 'string' ? rawValue.trim() : rawValue;
  }

  onAttributeTypeChange(): void {
    if (this.attrForm.type !== 'select') {
      this.attributeOptions = [];
      this.originalOptionIds = [];
    }
  }

  openOptionsDialog(): void {
    this.newOption = { label: '' };
    this.optionsModalVisible.set(true);
  }

  closeOptionsDialog(): void {
    this.optionsModalVisible.set(false);
  }

  saveOption(): void {
    if (!this.newOption.label.trim()) {
      this.toast.error(this.translation.t('builder.option-name-required'));
      return;
    }
    this.attributeOptions.push({ label: this.newOption.label.trim() });
    this.closeOptionsDialog();
  }

  removeOption(index: number): void {
    this.attributeOptions.splice(index, 1);
  }
}
