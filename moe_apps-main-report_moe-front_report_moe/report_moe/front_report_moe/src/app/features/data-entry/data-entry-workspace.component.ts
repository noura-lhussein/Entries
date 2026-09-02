import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  inject,
  signal,
  computed,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import {
  BuilderService,
  FormSchemaField,
  FormSchemaPayload,
  Title,
} from '../../core/services/builder.service';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormSelectComponent } from '../../shared/components/form-select/form-select.component';
import { FormCheckboxComponent } from '../../shared/components/form-checkbox/form-checkbox.component';
import { FormDateComponent } from '../../shared/components/form-date/form-date.component';
import { isEntityAttributeType } from '../builder/entity-attribute-types';
import { MasterDataQuickCreateComponent } from '../master-data/master-data-quick-create.component';
import { ENTITY_ADMIN_SLUGS } from '../master-data/master-data.models';
import type { InfoRow, PaginatedInfoRows } from '../../core/models/info-row';
import { TitleExcelActionsComponent } from '../../shared/components/title-excel-actions/title-excel-actions.component';

export type SectionStatus = 'empty' | 'draft' | 'complete' | 'error';

@Component({
  selector: 'app-data-entry-workspace',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatIconModule,
    ButtonComponent,
    FormInputComponent,
    FormSelectComponent,
    FormCheckboxComponent,
    FormDateComponent,
    MasterDataQuickCreateComponent,
    TitleExcelActionsComponent,
  ],
  templateUrl: './data-entry-workspace.component.html',
  styleUrls: ['./data-entry-workspace.component.scss'],
})
export class DataEntryWorkspaceComponent implements OnChanges {
  @Input({ required: true }) titles: Title[] = [];
  @Input() subMainId: number | null = null;

  private fb = inject(FormBuilder);
  private builder = inject(BuilderService);
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private auth = inject(AuthService);
  translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);
  canManageMasterData = this.auth.canManageMasterData;
  quickCreateSlug = signal<string | null>(null);
  quickCreateFieldType = signal<string | null>(null);

  activeTitleId = signal<number | null>(null);
  schema = signal<FormSchemaPayload | null>(null);
  loadingSchema = signal(false);
  saving = signal(false);
  saveState = signal<'idle' | 'saving' | 'saved' | 'failed'>('idle');
  lastSavedAt = signal<string | null>(null);
  fieldErrors = signal<Record<string, string>>({});
  fieldWarnings = signal<Record<string, string>>({});
  collapsedGroups = signal<Record<string, boolean>>({});
  previousRows = signal<InfoRow[]>([]);
  historyOpen = signal(false);
  expandedRowIds = signal<Set<string>>(new Set());
  sectionStatus = signal<Record<number, SectionStatus>>({});
  entityOptions = signal<Record<string, { label: string; value: string | number }[]>>({});
  /** Shown under the date field when another report already exists for that day. */
  dateDuplicateWarning = signal<string | null>(null);

  form: FormGroup = this.fb.group({});

  activeTitle = computed(() => {
    const id = this.activeTitleId();
    return this.titles.find((t) => t.id === id) ?? null;
  });

  progressDone = computed(() => {
    const st = this.sectionStatus();
    return this.titles.filter((t) => st[t.id] === 'complete').length;
  });

  progressLabel = computed(() =>
    this.t('data-entry.progress-of')
      .replace('{done}', String(this.progressDone()))
      .replace('{total}', String(this.titles.length)),
  );

  groupedFields = computed(() => {
    const s = this.schema();
    if (!s) return [];
    const byGroup = new Map<string, FormSchemaField[]>();
    for (const f of [...s.fields].sort((a, b) => a.order - b.order)) {
      const gid = f.group || 'other';
      if (!byGroup.has(gid)) byGroup.set(gid, []);
      byGroup.get(gid)!.push(f);
    }
    const groups = [...s.section.groups].sort((a, b) => a.order - b.order);
    const known = new Set(groups.map((g) => g.id));
    const result = groups.map((g) => ({
      ...g,
      fields: byGroup.get(g.id) || [],
    }));
    for (const [gid, fields] of byGroup) {
      if (!known.has(gid) && fields.length) {
        result.push({
          id: gid,
          title_ar: gid === 'other' ? 'أخرى' : gid,
          order: 999,
          collapsed_by_default: true,
          fields,
        });
      }
    }
    return result.filter((g) => g.fields.length > 0);
  });

  previewKeys = computed(() => this.schema()?.section.preview_field_keys ?? []);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['titles'] && this.titles.length) {
      const current = this.activeTitleId();
      if (!current || !this.titles.some((t) => t.id === current)) {
        this.selectTitle(this.titles[0].id);
      }
    }
    if (changes['subMainId'] && this.activeTitleId()) {
      this.loadHistory();
    }
  }

  selectTitle(titleId: number): void {
    this.activeTitleId.set(titleId);
    this.dateDuplicateWarning.set(null);
    this.loadSchema(titleId);
    this.loadHistory();
  }

  private loadSchema(titleId: number): void {
    this.loadingSchema.set(true);
    this.schema.set(null);
    this.fieldErrors.set({});
    this.fieldWarnings.set({});
    this.builder.getFormSchema(titleId).subscribe({
      next: (payload) => {
        this.schema.set(payload);
        const collapsed: Record<string, boolean> = {};
        for (const g of payload.section.groups) {
          collapsed[g.id] = !!g.collapsed_by_default;
        }
        this.collapsedGroups.set(collapsed);
        this.buildForm(payload.fields);
        this.loadEntityOptions(payload.fields);
        this.loadingSchema.set(false);
      },
      error: () => {
        this.loadingSchema.set(false);
        this.toast.error(this.t('builder.load-error') || 'تعذّر تحميل النموذج');
      },
    });
  }

  private buildForm(fields: FormSchemaField[]): void {
    const controls: Record<string, unknown> = {};
    for (const f of [...fields].sort((a, b) => a.order - b.order)) {
      const validators = [];
      if (f.required && !f.readonly) validators.push(Validators.required);
      controls[f.key] = [
        { value: '', disabled: !!f.readonly },
        validators,
      ];
    }
    this.form = this.fb.group(controls);
    this.form.valueChanges.subscribe(() => this.recomputeAndWarn());
  }

  private recomputeAndWarn(): void {
    const s = this.schema();
    if (!s) return;
    const raw = this.form.getRawValue() as Record<string, unknown>;
    const warnings: Record<string, string> = {};

    for (const f of s.fields) {
      if (f.computed_from) {
        const expr = f.computed_from.replace(/\s+/g, '');
        const m = expr.match(/^([a-zA-Z0-9_]+)-([a-zA-Z0-9_]+)$/);
        if (m) {
          const a = Number(raw[m[1]]);
          const b = Number(raw[m[2]]);
          if (!Number.isNaN(a) && !Number.isNaN(b)) {
            this.form.get(f.key)?.setValue(String(a - b), { emitEvent: false });
          }
        }
      }
      if (f.warn_if_gt_field) {
        const v = Number(raw[f.key]);
        const cap = Number(raw[f.warn_if_gt_field]);
        if (!Number.isNaN(v) && !Number.isNaN(cap) && v > cap) {
          warnings[f.key] = f.message_ar || 'القيمة أعلى من الحد';
        }
      }
    }
    this.fieldWarnings.set(warnings);
  }

  toggleGroup(groupId: string): void {
    const cur = { ...this.collapsedGroups() };
    cur[groupId] = !cur[groupId];
    this.collapsedGroups.set(cur);
  }

  isGroupCollapsed(groupId: string): boolean {
    return !!this.collapsedGroups()[groupId];
  }

  fieldError(key: string): string {
    return this.fieldErrors()[key] || '';
  }

  fieldWarning(key: string): string {
    return this.fieldWarnings()[key] || '';
  }

  onBlur(field: FormSchemaField): void {
    const ctrl = this.form.get(field.key);
    if (!ctrl || field.readonly) return;
    const errors = { ...this.fieldErrors() };
    delete errors[field.key];
    const raw = ctrl.value;
    if (field.required && (raw === '' || raw == null)) {
      errors[field.key] = 'هذا الحقل مطلوب';
    }
    if (field.type === 'number' && raw !== '' && raw != null) {
      const n = Number(raw);
      if (Number.isNaN(n)) errors[field.key] = 'قيمة غير صالحة';
      else {
        if (field.min != null && n < field.min) errors[field.key] = `الحد الأدنى ${field.min}`;
        if (field.max != null && n > field.max) errors[field.key] = `الحد الأعلى ${field.max}`;
        if (field.max_field) {
          const cap = Number(this.form.getRawValue()[field.max_field]);
          if (!Number.isNaN(cap) && n > cap) {
            errors[field.key] = field.message_ar || `أعلى من ${field.max_field}`;
          }
        }
      }
    }
    this.fieldErrors.set(errors);
    this.recomputeAndWarn();
    if (
      field.type === 'date' ||
      this.isReportDateField(field) ||
      this.currentEntityFromForm().entity_type === field.type
    ) {
      this.checkDuplicateReportDate(
        field.type === 'date' || this.isReportDateField(field) ? field : undefined,
      );
    }
  }

  private isReportDateField(field: FormSchemaField): boolean {
    const key = (field.key || '').trim();
    const label = (field.label_ar || '').trim();
    return (
      field.type === 'date' ||
      key === 'report_date' ||
      key === 'reading_date' ||
      key === 'update_date' ||
      label === 'تاريخ التقرير' ||
      label === 'تاريخ القراءة' ||
      label === 'تاريخ التحديث'
    );
  }

  private normalizeDateValue(raw: unknown): string | null {
    if (raw == null || raw === '') return null;
    const text = String(raw).trim();
    if (text.length >= 10 && text[4] === '-' && text[7] === '-') {
      return text.slice(0, 10);
    }
    return null;
  }

  private currentEntityFromForm(): { entity_type?: string; entity_id?: number } {
    const s = this.schema();
    if (!s) return {};
    const raw = this.form.getRawValue() as Record<string, unknown>;
    for (const f of s.fields) {
      if (!isEntityAttributeType(f.type)) continue;
      const v = raw[f.key];
      if (v === '' || v == null) continue;
      const id = Number(v);
      if (!Number.isNaN(id)) return { entity_type: f.type, entity_id: id };
    }
    return {};
  }

  private checkDuplicateReportDate(field?: FormSchemaField): void {
    const titleId = this.activeTitleId();
    const subId = this.subMainId;
    const s = this.schema();
    if (!titleId || !subId || !s) {
      this.dateDuplicateWarning.set(null);
      return;
    }
    const dateField =
      field && this.isReportDateField(field)
        ? field
        : s.fields.find((f) => this.isReportDateField(f));
    if (!dateField) {
      this.dateDuplicateWarning.set(null);
      return;
    }
    const dateValue = this.normalizeDateValue(this.form.getRawValue()[dateField.key]);
    if (!dateValue) {
      this.dateDuplicateWarning.set(null);
      return;
    }
    const entity = this.currentEntityFromForm();
    this.api
      .get<{ duplicate: boolean; detail?: string; date?: string }>('/reports/check-date/', {
        title_id: titleId,
        sub_main_id: subId,
        date: dateValue,
        ...entity,
      })
      .subscribe({
        next: (res) => {
          if (res.duplicate) {
            const msg =
              res.detail ||
              `يوجد تقرير مسجّل مسبقاً لهذا القسم بتاريخ ${dateValue}. لا يمكن إدخال أكثر من تقرير لنفس التاريخ.`;
            this.dateDuplicateWarning.set(msg);
            this.toast.warning(msg, 6000);
            const errors = { ...this.fieldErrors() };
            errors[dateField.key] = msg;
            this.fieldErrors.set(errors);
          } else {
            this.dateDuplicateWarning.set(null);
            const errors = { ...this.fieldErrors() };
            if (errors[dateField.key]?.includes('نفس التاريخ')) {
              delete errors[dateField.key];
              this.fieldErrors.set(errors);
            }
          }
        },
        error: () => {
          /* non-blocking pre-check */
        },
      });
  }

  saveDraft(): void {
    this.persist(false);
  }

  commitAndNext(): void {
    this.persist(true);
  }

  private persist(requireComplete: boolean): void {
    const titleId = this.activeTitleId();
    const subId = this.subMainId;
    const s = this.schema();
    if (!titleId || !subId || !s) {
      this.toast.error(this.t('builder.select-sub-main'));
      return;
    }

    const errors: Record<string, string> = {};
    if (requireComplete) {
      for (const f of s.fields) {
        if (f.readonly || !f.required) continue;
        const v = this.form.getRawValue()[f.key];
        if (v === '' || v == null) errors[f.key] = 'هذا الحقل مطلوب';
      }
    }
    this.fieldErrors.set(errors);
    if (Object.keys(errors).length) {
      this.markSection('error');
      this.toast.error('أكمل الحقول المطلوبة قبل الاعتماد');
      return;
    }

    if (this.dateDuplicateWarning()) {
      this.toast.error(this.dateDuplicateWarning()!);
      this.markSection('error');
      return;
    }

    const attribute_values = s.fields
      .filter((f) => !f.readonly)
      .map((f) => ({
        id: f.id,
        value: this.form.getRawValue()[f.key] ?? '',
      }))
      .filter((row) => String(row.value).trim() !== '');

    this.saving.set(true);
    this.saveState.set('saving');
    this.builder
      .submitReport(titleId, { sub_main_id: subId, attribute_values })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.saveState.set('saved');
          const now = new Date();
          this.lastSavedAt.set(
            now.toLocaleTimeString('ar-SY', {
              hour: '2-digit',
              minute: '2-digit',
              numberingSystem: 'latn',
            }),
          );
          this.markSection(requireComplete ? 'complete' : 'draft');
          this.loadHistory();
          this.toast.success(
            requireComplete ? 'تم اعتماد القسم' : 'حُفظت المسودة',
          );
          if (requireComplete) this.goNext();
        },
        error: (err) => {
          this.saving.set(false);
          this.saveState.set('failed');
          const body = err?.error;
          if (body?.code === 'duplicate_report_date' || err?.status === 409) {
            const msg =
              body?.detail ||
              'يوجد تقرير مسجّل مسبقاً لهذا التاريخ. لا يمكن إدخال أكثر من تقرير لنفس التاريخ.';
            this.dateDuplicateWarning.set(msg);
            this.toast.error(msg, 7000);
            this.markSection('error');
            return;
          }
          this.toast.error('فشل الحفظ — القيم ما زالت في النموذج');
        },
      });
  }

  private markSection(status: SectionStatus): void {
    const id = this.activeTitleId();
    if (id == null) return;
    this.sectionStatus.set({ ...this.sectionStatus(), [id]: status });
  }

  goNext(): void {
    const idx = this.titles.findIndex((t) => t.id === this.activeTitleId());
    if (idx >= 0 && idx < this.titles.length - 1) {
      this.selectTitle(this.titles[idx + 1].id);
    }
  }

  statusOf(titleId: number): SectionStatus {
    return this.sectionStatus()[titleId] || 'empty';
  }

  statusLabel(titleId: number): string {
    const status = this.statusOf(titleId);
    return this.t(`data-entry.status-${status}`);
  }

  statusIcon(titleId: number): string {
    switch (this.statusOf(titleId)) {
      case 'complete':
        return 'check_circle';
      case 'draft':
        return 'edit_note';
      case 'error':
        return 'error';
      default:
        return 'radio_button_unchecked';
    }
  }

  private loadHistory(): void {
    const titleId = this.activeTitleId();
    const subId = this.subMainId;
    if (!titleId || !subId) {
      this.previousRows.set([]);
      return;
    }
    this.api
      .get<PaginatedInfoRows>('/info-rows/', {
        title_id: titleId,
        sub_main_id: subId,
        page_size: 5,
        page: 1,
      })
      .subscribe({
        next: (res) => this.previousRows.set(res.results || []),
        error: () => this.previousRows.set([]),
      });
  }

  onExcelImported(): void {
    this.loadHistory();
    this.historyOpen.set(true);
  }

  previewValue(row: InfoRow, key: string): string {
    const fields = row.fields || {};
    // fields keyed by Arabic label often — try key, label_ar
    if (fields[key] != null) return String(fields[key]);
    const f = this.schema()?.fields.find((x) => x.key === key);
    if (f && fields[f.label_ar] != null) return String(fields[f.label_ar]);
    return '—';
  }

  toggleRow(rowId: string): void {
    const next = new Set(this.expandedRowIds());
    if (next.has(rowId)) next.delete(rowId);
    else next.add(rowId);
    this.expandedRowIds.set(next);
  }

  isRowExpanded(rowId: string): boolean {
    return this.expandedRowIds().has(rowId);
  }

  extraFieldEntries(row: InfoRow): { label: string; value: string }[] {
    const preview = new Set(this.previewKeys());
    const s = this.schema();
    const labelByKey = new Map((s?.fields || []).map((f) => [f.key, f.label_ar]));
    return Object.entries(row.fields || [])
      .filter(([k]) => !preview.has(k) && ![...labelByKey.values()].some((l) => preview.has(l) && l === k))
      .map(([label, value]) => ({ label, value: String(value) }));
  }

  trackField(_: number, f: FormSchemaField): string {
    return f.key;
  }

  previewHeaderLabel(key: string): string {
    const f = this.schema()?.fields.find((x) => x.key === key);
    return f?.label_ar || key;
  }

  protected readonly isEntityAttributeType = isEntityAttributeType;

  /** Manual `select` options, or Master-table options for entity field types. */
  adminSlugForField(field: FormSchemaField): string | null {
    if (!isEntityAttributeType(field.type)) return null;
    return ENTITY_ADMIN_SLUGS[field.type] || null;
  }

  openMasterData(field: FormSchemaField): void {
    const slug = this.adminSlugForField(field);
    if (!slug) return;
    this.quickCreateFieldType.set(field.type);
    this.quickCreateSlug.set(slug);
  }

  onQuickCreateSaved(): void {
    const type = this.quickCreateFieldType();
    if (!type || !isEntityAttributeType(type)) return;
    this.builder.getEntityOptions(type, { limit: 500 }).subscribe({
      next: (rows) => {
        this.entityOptions.set({
          ...this.entityOptions(),
          [type]: rows.map((r) => ({ label: r.label, value: r.id })),
        });
      },
    });
  }

  closeQuickCreate(): void {
    this.quickCreateSlug.set(null);
    this.quickCreateFieldType.set(null);
  }

  isDropdownField(field: FormSchemaField): boolean {
    return field.type === 'select' || isEntityAttributeType(field.type);
  }

  selectOptions(field: FormSchemaField): { label: string; value: string | number }[] {
    if (field.options?.length) {
      return field.options.map((o) => ({ label: o.label, value: o.id }));
    }
    return this.entityOptions()[field.type] || [];
  }

  private loadEntityOptions(fields: FormSchemaField[]): void {
    const types = [...new Set(fields.map((f) => f.type).filter(isEntityAttributeType))];
    for (const type of types) {
      this.builder.getEntityOptions(type, { limit: 500 }).subscribe({
        next: (rows) => {
          this.entityOptions.set({
            ...this.entityOptions(),
            [type]: rows.map((r) => ({ label: r.label, value: r.id })),
          });
        },
      });
    }
  }
}
