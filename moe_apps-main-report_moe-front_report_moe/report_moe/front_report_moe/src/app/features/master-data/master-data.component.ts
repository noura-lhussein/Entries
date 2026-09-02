import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import {
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormControl,
  UntypedFormGroup,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { FormCheckboxComponent } from '../../shared/components/form-checkbox/form-checkbox.component';
import { FormDateComponent } from '../../shared/components/form-date/form-date.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import { FormSearchSelectComponent } from '../../shared/components/form-search-select/form-search-select.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { PageLoaderComponent } from '../../shared/components/page-loader/page-loader.component';
import {
  TableComponent,
  type TableAction,
  type TableColumn,
} from '../../shared/components/table/table.component';
import { DialogService } from '../../shared/services/dialog.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { DATA_TABLE_PAGE_SIZE } from '../../shared/utils/data-table-page-size';
import { FilterState } from '../../shared/utils/filter-state';
import type {
  MasterFieldSchema,
  MasterRegistryGroup,
  MasterResourceMeta,
  MasterSector,
} from './master-data.models';
import { MasterDataService } from './master-data.service';

type FormMode = 'create' | 'edit' | 'view' | null;

const NAV_COLLAPSE_KEY = 'master-data.nav.collapsed';

@Component({
  selector: 'app-master-data',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    PageHeaderComponent,
    PageLoaderComponent,
    TableComponent,
    ModalComponent,
    FormInputComponent,
    FormSelectComponent,
    FormSearchSelectComponent,
    FormCheckboxComponent,
    FormDateComponent,
    FormMapPickerComponent,
    ButtonComponent,
  ],
  templateUrl: './master-data.component.html',
  styleUrl: './master-data.component.scss',
})
export class MasterDataComponent implements OnInit {
  private api = inject(MasterDataService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(UntypedFormBuilder);
  private toast = inject(ToastService);
  private dialogs = inject(DialogService);
  private auth = inject(AuthService);
  private translation = inject(TranslationService);

  t = (key: string) => this.translation.t(key);

  loadingRegistry = signal(true);
  resources = signal<MasterResourceMeta[]>([]);
  groups = signal<MasterRegistryGroup[]>([]);
  currentSlug = signal<string>('');
  rows = signal<Record<string, unknown>[]>([]);
  formMode = signal<FormMode>(null);
  saving = signal(false);
  editingPk = signal<string | number | null>(null);
  fkOptions = signal<Record<string, SelectOption[]>>({});
  form: UntypedFormGroup = this.fb.group({});
  navQuery = signal('');
  /** Set of group_en keys that are collapsed. */
  collapsedGroups = signal<Set<string>>(this.readCollapsedGroups());

  fs = new FilterState(() => this.loadRows(), 'search', DATA_TABLE_PAGE_SIZE);

  meta = computed(() => {
    const slug = this.currentSlug();
    return this.resources().find((r) => r.slug === slug) ?? null;
  });

  filteredGroups = computed(() => {
    const q = this.navQuery().trim().toLocaleLowerCase();
    const resources = this.resources();
    return this.groups()
      .map((group) => {
        const resourcesFiltered = group.resources.filter((slug) => {
          if (!q) return true;
          const meta = resources.find((r) => r.slug === slug);
          const hay = [slug, meta?.label_ar, meta?.label_en, group.group_ar, group.group_en]
            .filter(Boolean)
            .join(' ')
            .toLocaleLowerCase();
          return hay.includes(q);
        });
        return { ...group, resources: resourcesFiltered };
      })
      .filter((group) => group.resources.length > 0);
  });

  canWriteCurrent = computed(() => {
    const m = this.meta();
    if (!m || m.read_only) return false;
    return this.canWriteSector(m.sector);
  });

  columns = computed<TableColumn[]>(() => {
    const m = this.meta();
    if (!m) return [];
    return m.list_display.map((key) => ({
      key,
      label: this.columnLabel(key),
      sortable: true,
      type: this.columnType(m, key),
    }));
  });

  actions = computed<TableAction[]>(() => {
    const write = this.canWriteCurrent();
    const list: TableAction[] = [
      { type: 'view', label: this.t('master-data.view'), icon: 'visibility', color: 'view' },
    ];
    if (write) {
      list.push(
        { type: 'edit', label: this.t('master-data.edit'), icon: 'edit', color: 'edit' },
        { type: 'delete', label: this.t('master-data.delete'), icon: 'delete', color: 'delete' },
      );
    }
    return list;
  });

  visibleFields = computed(() => {
    const m = this.meta();
    const mode = this.formMode();
    if (!m || !mode) return [] as MasterFieldSchema[];
    return m.fields.filter((f) => {
      if (mode === 'view') return true;
      if (f.name === 'geometry_type') return false;
      if (f.name === 'id' && mode === 'create') return false;
      if (f.read_only && mode === 'create') return false;
      return true;
    });
  });

  showMapPicker = computed(() => {
    const m = this.meta();
    if (!m?.has_map) return false;
    const names = new Set(m.fields.map((f) => f.name));
    return names.has('latitude') && names.has('longitude');
  });

  modalTitle = computed(() => {
    const m = this.meta();
    const mode = this.formMode();
    if (!m || !mode) return '';
    const label = m.label_ar || m.label_en;
    if (mode === 'create') return `${this.t('master-data.add')} — ${label}`;
    if (mode === 'edit') return `${this.t('master-data.edit')} — ${label}`;
    return `${this.t('master-data.view')} — ${label}`;
  });

  ngOnInit(): void {
    this.api.getRegistry().subscribe({
      next: (res) => {
        this.resources.set(res.resources);
        this.groups.set(res.groups);
        this.loadingRegistry.set(false);
        const fromRoute = this.route.snapshot.paramMap.get('slug');
        const first = fromRoute || res.resources[0]?.slug || '';
        if (first) this.selectResource(first, false);
        this.route.paramMap.subscribe((pm) => {
          const slug = pm.get('slug');
          if (slug && slug !== this.currentSlug()) this.selectResource(slug, false);
        });
      },
      error: () => {
        this.loadingRegistry.set(false);
        this.toast.error(this.t('master-data.load-error'));
      },
    });
  }

  selectResource(slug: string, navigate = true): void {
    this.currentSlug.set(slug);
    this.ensureGroupExpandedForSlug(slug);
    this.fs.currentPage.set(1);
    this.fs.searchQuery.set('');
    if (navigate) {
      void this.router.navigate(['/master-data', slug]);
    }
    this.loadRows();
  }

  onNavSearch(value: string): void {
    this.navQuery.set(value);
    // While searching, expand all matching groups for visibility.
    if (value.trim()) {
      const next = new Set(this.collapsedGroups());
      for (const group of this.filteredGroups()) {
        next.delete(group.group_en);
      }
      this.collapsedGroups.set(next);
    }
  }

  isGroupCollapsed(groupEn: string): boolean {
    // Force-expand while filtering so matches stay visible.
    if (this.navQuery().trim()) return false;
    return this.collapsedGroups().has(groupEn);
  }

  toggleGroup(groupEn: string): void {
    if (this.navQuery().trim()) return;
    const next = new Set(this.collapsedGroups());
    if (next.has(groupEn)) next.delete(groupEn);
    else next.add(groupEn);
    this.collapsedGroups.set(next);
    this.persistCollapsedGroups(next);
  }

  loadRows(): void {
    const slug = this.currentSlug();
    if (!slug) return;
    this.fs.loading.set(true);
    this.api
      .list(slug, {
        search: this.fs.searchQuery() || undefined,
        page: this.fs.currentPage(),
        page_size: this.fs.pageSize(),
      })
      .subscribe({
        next: (res) => {
          this.rows.set(res.results);
          this.fs.setTotal(res.total_count);
          this.fs.loading.set(false);
        },
        error: () => {
          this.fs.loading.set(false);
          this.toast.error(this.t('master-data.load-error'));
        },
      });
  }

  onSearch(value: string): void {
    this.fs.onSearch(value);
  }

  onSort(event: { key: string; direction: 'asc' | 'desc' | '' }): void {
    const slug = this.currentSlug();
    if (!slug || !event.key || !event.direction) return;
    this.fs.loading.set(true);
    this.api
      .list(slug, {
        search: this.fs.searchQuery() || undefined,
        page: this.fs.currentPage(),
        page_size: this.fs.pageSize(),
        sort: event.key,
        direction: event.direction,
      })
      .subscribe({
        next: (res) => {
          this.rows.set(res.results);
          this.fs.setTotal(res.total_count);
          this.fs.loading.set(false);
        },
        error: () => this.fs.loading.set(false),
      });
  }

  onAction(event: { type: string; row: Record<string, unknown> }): void {
    const row = event.row;
    if (event.type === 'view') this.openView(row);
    else if (event.type === 'edit') this.openEdit(row);
    else if (event.type === 'delete') void this.deleteRow(row);
  }

  openCreate(): void {
    const m = this.meta();
    if (!m || !this.canWriteCurrent()) return;
    this.editingPk.set(null);
    this.buildForm(m, null, 'create');
    this.prefetchFk(m);
    this.formMode.set('create');
  }

  openEdit(row: Record<string, unknown>): void {
    const m = this.meta();
    if (!m) return;
    this.editingPk.set(this.rowPk(row));
    this.buildForm(m, row, 'edit');
    this.prefetchFk(m);
    this.formMode.set('edit');
  }

  openView(row: Record<string, unknown>): void {
    const m = this.meta();
    if (!m) return;
    this.editingPk.set(this.rowPk(row));
    this.buildForm(m, row, 'view');
    this.prefetchFk(m);
    this.formMode.set('view');
  }

  closeForm(): void {
    this.formMode.set(null);
    this.editingPk.set(null);
  }

  saveForm(): void {
    const m = this.meta();
    const mode = this.formMode();
    if (!m || !mode || mode === 'view') return;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.toast.error(this.t('master-data.fix-invalid'));
      return;
    }
    const body = this.buildPayload(m);
    this.saving.set(true);
    const req =
      mode === 'create'
        ? this.api.create(m.slug, body)
        : this.api.update(m.slug, this.editingPk()!, body);
    req.subscribe({
      next: () => {
        this.saving.set(false);
        this.toast.success(this.t('master-data.saved'));
        this.closeForm();
        this.loadRows();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail || this.t('master-data.save-error');
        this.toast.error(String(detail));
      },
    });
  }

  async deleteRow(row: Record<string, unknown>): Promise<void> {
    const m = this.meta();
    if (!m) return;
    const label = this.rowLabel(row);
    const ok = await this.dialogs.delete(label);
    if (!ok) return;
    this.api.delete(m.slug, this.rowPk(row)).subscribe({
      next: () => {
        this.toast.success(this.t('master-data.deleted'));
        this.loadRows();
      },
      error: (err) => {
        const detail = err?.error?.detail || this.t('master-data.delete-error');
        this.toast.error(String(detail));
      },
    });
  }

  choiceOptions(field: MasterFieldSchema): SelectOption[] {
    return (field.choices || []).map((c) => ({ value: c.value, label: c.label }));
  }

  fkFieldOptions(field: MasterFieldSchema): SelectOption[] {
    if (!field.related_slug) return [];
    return this.fkOptions()[field.related_slug] || [];
  }

  isLatLonField(name: string): boolean {
    return name === 'latitude' || name === 'longitude';
  }

  // Admin only, exclusively — matches the backend's user_can_access_sector
  // (master_data/permissions.py). `sector` is accepted only to keep this call
  // site-compatible with canWriteCurrent(); it no longer affects the result.
  private canWriteSector(_sector: MasterSector): boolean {
    const u = this.auth.currentUser();
    if (!u) return false;
    return !!(u.is_admin || u.is_staff || u.is_superuser);
  }

  private columnLabel(key: string): string {
    const translated = this.t(`master-data.col.${key}`);
    if (translated && translated !== `master-data.col.${key}`) return translated;
    return key.replace(/_/g, ' ');
  }

  private columnType(m: MasterResourceMeta, key: string): TableColumn['type'] {
    const field = m.fields.find((f) => f.name === key);
    if (!field) return 'text';
    if (field.type === 'boolean') return 'boolean';
    if (field.type === 'date' || field.type === 'datetime') return 'date';
    if (key === 'status' || field.type === 'choice') return 'badge';
    return 'text';
  }

  private rowPk(row: Record<string, unknown>): string | number {
    return (row['id'] as string | number) ?? '';
  }

  private rowLabel(row: Record<string, unknown>): string {
    for (const key of [
      'name_ar',
      'name_en',
      'name',
      'refinery_name',
      'well_code',
      'code',
      'slug',
    ]) {
      const v = row[key];
      if (v != null && String(v).trim()) return String(v);
    }
    return String(this.rowPk(row));
  }

  private buildForm(
    m: MasterResourceMeta,
    row: Record<string, unknown> | null,
    mode: FormMode,
  ): void {
    const group: Record<string, UntypedFormControl> = {};
    for (const field of m.fields) {
      if (field.name === 'id' && mode === 'create') continue;
      let value: unknown = row ? row[field.name] : '';
      if (field.type === 'foreign_key') {
        value = row ? (row[`${field.name}_id`] ?? row[field.name] ?? null) : null;
      }
      if (field.type === 'boolean') {
        value = row ? Boolean(row[field.name]) : false;
      }
      if (!row && m.default_create_values && field.name in m.default_create_values) {
        value = m.default_create_values[field.name];
      }
      const validators = field.required && !field.read_only ? [Validators.required] : [];
      const ctrl = new UntypedFormControl(
        {
          value: value ?? (field.type === 'boolean' ? false : ''),
          disabled: mode === 'view' || field.read_only,
        },
        validators,
      );
      group[field.name] = ctrl;
    }
    this.form = this.fb.group(group);
  }

  private buildPayload(m: MasterResourceMeta): Record<string, unknown> {
    const body: Record<string, unknown> = {};
    const raw = this.form.getRawValue() as Record<string, unknown>;
    for (const field of m.fields) {
      if (field.read_only) continue;
      if (!(field.name in raw)) continue;
      let val = raw[field.name];
      if (val === '' && !field.required) continue;
      if (field.type === 'boolean') val = Boolean(val);
      else if (field.type === 'number' || field.type === 'foreign_key') {
        val = val === '' || val === null || val === undefined ? null : Number(val);
      }
      body[field.name] = val;
    }
    for (const [k, v] of Object.entries(m.default_create_values || {})) {
      body[k] = body[k] ?? v;
    }
    return body;
  }

  private prefetchFk(m: MasterResourceMeta): void {
    for (const field of m.fields) {
      if (field.type !== 'foreign_key' || !field.related_slug) continue;
      const slug = field.related_slug;
      if (this.fkOptions()[slug]?.length) continue;
      this.api.options(slug).subscribe({
        next: (res) => {
          this.fkOptions.set({
            ...this.fkOptions(),
            [slug]: res.options.map((o) => ({ value: o.value, label: o.label })),
          });
        },
      });
    }
  }

  /** Display helper for table cells with FK labels. */
  mappedRows = computed(() => {
    const m = this.meta();
    return this.rows().map((row) => {
      if (!m) return row;
      const out: Record<string, unknown> = { ...row };
      for (const col of m.list_display) {
        const field = m.fields.find((f) => f.name === col);
        if (field?.type === 'foreign_key') {
          out[col] = row[`${col}_label_ar`] || row[`${col}_label_en`] || row[col];
        }
        if (typeof row[col] === 'boolean') {
          out[col] = row[col];
        }
      }
      return out;
    });
  });

  resourceLabel(slug: string): string {
    const r = this.resources().find((x) => x.slug === slug);
    return r?.label_ar || r?.label_en || slug;
  }

  columnLabelPublic(key: string): string {
    return this.columnLabel(key);
  }

  openCreateBound = (): void => {
    this.openCreate();
  };

  private ensureGroupExpandedForSlug(slug: string): void {
    const group = this.groups().find((g) => g.resources.includes(slug));
    if (!group) return;
    const next = new Set(this.collapsedGroups());
    if (!next.has(group.group_en)) return;
    next.delete(group.group_en);
    this.collapsedGroups.set(next);
    this.persistCollapsedGroups(next);
  }

  private readCollapsedGroups(): Set<string> {
    try {
      const raw = localStorage.getItem(NAV_COLLAPSE_KEY);
      if (!raw) return new Set();
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return new Set();
      return new Set(parsed.filter((x): x is string => typeof x === 'string'));
    } catch {
      return new Set();
    }
  }

  private persistCollapsedGroups(value: Set<string>): void {
    try {
      localStorage.setItem(NAV_COLLAPSE_KEY, JSON.stringify([...value]));
    } catch {
      // ignore quota / private mode
    }
  }
}
