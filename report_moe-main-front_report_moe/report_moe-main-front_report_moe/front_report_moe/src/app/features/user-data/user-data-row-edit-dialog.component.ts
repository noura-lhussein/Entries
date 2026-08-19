import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { BuilderService } from '../../core/services/builder.service';
import { AttributeType, Info } from '../../core/models';
import type { Attribute as BuilderAttribute } from '../../core/services/builder.service';
import { ButtonComponent } from '../../shared/components/button/button.component';
import {
  FormSelectComponent,
  SelectOption,
} from '../../shared/components/form-select/form-select.component';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import { FormCheckboxComponent } from '../../shared/components/form-checkbox/form-checkbox.component';
import { StoredMediaValueComponent } from '../../shared/components/stored-media-value/stored-media-value.component';
import { isInfoAccepted } from '../../core/models/info-confirm-status';
import { isLocationAttributeType } from '../builder/builder-attribute-fields';
import { ENTITY_ATTRIBUTE_TYPES, isEntityAttributeType } from '../builder/entity-attribute-types';

export interface UserDataRowEditFieldColumn {
  id: string;
  label: string;
  preview: string;
}

export interface UserDataRowEditDialogData {
  infoIds: number[];
  fieldColumns: UserDataRowEditFieldColumn[];
}

interface RowFieldEdit {
  infoId: number;
  attributeId: number;
  label: string;
  type: AttributeType;
  value: string;
  options: SelectOption[];
}

@Component({
  selector: 'app-user-data-row-edit-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatIconModule,
    ButtonComponent,
    FormSelectComponent,
    FormInputComponent,
    FormCheckboxComponent,
    StoredMediaValueComponent,
  ],
  template: `
    <div class="dialog-wrapper" dir="rtl">
      <div class="dialog-header">
        <span class="header-icon"><mat-icon>edit_note</mat-icon></span>
        <div class="header-text">
          <h2>{{ t('user-data.edit-row-modal-title') }}</h2>
          <p class="hint">{{ t('user-data.edit-row-modal-hint') }}</p>
        </div>
      </div>

      @if (loadError()) {
        <p class="load-error"><mat-icon>error_outline</mat-icon> {{ loadError() }}</p>
      } @else {
        <div
          class="fields-shell"
          [class.fields-shell--loading]="loading()"
          [class.fields-shell--revealed]="!loading()"
        >
          <div class="fields-scroll">
            <div class="fields-grid">
              @for (col of displayColumns(); track col.id; let i = $index) {
                <div
                  class="field-card"
                  [class.field-card--wide]="isWideColumn(col.id)"
                  [style.animation-delay.ms]="fieldCellDelay(i)"
                >
                  <label class="field-label">{{ col.label }}</label>
                  @if (loading()) {
                    <span class="preview-value">{{ col.preview }}</span>
                  } @else if (fieldForColumn(col.id); as field) {
                    @if (field.type === 'select') {
                      <app-form-select
                        [ngModel]="field.value"
                        (ngModelChange)="setFieldValue(field.infoId, $event)"
                        [label]="''"
                        [placeholder]="t('user-data.select-placeholder')"
                        [options]="field.options"
                        [required]="true"
                      />
                    } @else if (field.type === 'textarea') {
                      <app-form-input
                        [ngModel]="field.value"
                        (ngModelChange)="setFieldValue(field.infoId, $event)"
                        [label]="''"
                        [placeholder]="t('user-data.value-field-placeholder')"
                        [multiline]="true"
                        [rows]="3"
                        [required]="true"
                      />
                    } @else if (field.type === 'number') {
                      <app-form-input
                        [ngModel]="field.value"
                        (ngModelChange)="setFieldValue(field.infoId, $event)"
                        [label]="''"
                        [placeholder]="t('user-data.value-field-placeholder')"
                        type="number"
                        [required]="true"
                      />
                    } @else if (field.type === 'date') {
                      <app-form-input
                        [ngModel]="field.value"
                        (ngModelChange)="setFieldValue(field.infoId, $event)"
                        [label]="''"
                        type="date"
                        [required]="true"
                      />
                    } @else if (field.type === 'boolean') {
                      <app-form-checkbox
                        [ngModel]="booleanChecked(field)"
                        (ngModelChange)="setBooleanValue(field.infoId, $event)"
                        [label]="''"
                      />
                    } @else if (
                      field.type === 'city' ||
                      field.type === 'district' ||
                      field.type === 'sub_district' ||
                      field.type === 'community' ||
                      isEntityAttributeType(field.type)
                    ) {
                      <app-form-select
                        [ngModel]="field.value"
                        (ngModelChange)="
                          field.type === 'city' ||
                          field.type === 'district' ||
                          field.type === 'sub_district' ||
                          field.type === 'community'
                            ? onLocationFieldChange(field, $event)
                            : setFieldValue(field.infoId, $event)
                        "
                        [label]="''"
                        [placeholder]="t('user-data.select-placeholder')"
                        [options]="field.options"
                        [required]="true"
                      />
                    } @else if (field.type === 'image' || field.type === 'file') {
                      <p class="upload-hint">
                        {{ t('builder.file-max-hint').replace('{mb}', maxUploadMb()) }}
                      </p>
                      <input
                        type="file"
                        class="file-input"
                        [accept]="mediaAccept(field.type)"
                        [disabled]="uploadingFieldId() === field.infoId"
                        (change)="onMediaFileSelected($event, field)"
                      />
                      @if (field.value) {
                        <app-stored-media-value
                          variant="form"
                          [fileKind]="field.type === 'image' ? 'image' : 'file'"
                          [value]="field.value"
                        />
                      }
                    } @else {
                      <app-form-input
                        [ngModel]="field.value"
                        (ngModelChange)="setFieldValue(field.infoId, $event)"
                        [label]="''"
                        [placeholder]="t('user-data.value-field-placeholder')"
                        type="text"
                        [required]="true"
                      />
                    }
                  } @else {
                    <span class="preview-value">{{ col.preview }}</span>
                  }
                </div>
              }
            </div>
          </div>
          @if (loading()) {
            <div class="loading-overlay">
              <mat-icon class="spin">refresh</mat-icon>
              <span>{{ t('admin-report.loading') }}</span>
            </div>
          }
        </div>
      }

      <div class="footer">
        <app-button variant="ghost" [label]="t('user-data.cancel-button')" (clicked)="cancel()" />
        @if (!loading() && !loadError()) {
          <app-button
            variant="primary"
            [label]="t('user-data.save-button')"
            (clicked)="save()"
            [disabled]="saving() || uploadingFieldId() != null || !canSave()"
          />
        }
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        --gold: #054239;
        --gold-soft: #b9a779;
        --gold-bg: #f5f0e8;
        --line: #d8d3c9;
        --text: #353233;
        --muted: #6d6768;
        --danger: #c0392b;
      }
      .dialog-wrapper {
        padding: 22px 28px 18px;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        max-width: 100vw;
        min-height: 62vh;
        max-height: 94vh;
        display: flex;
        flex-direction: column;
        font-family: inherit;
        color: var(--text);
        opacity: 0;
        transform: translateY(12px);
      }
      :host-context(.user-data-row-expand-ready) .dialog-wrapper {
        animation: dialog-content-in 0.52s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards;
      }
      @keyframes dialog-content-in {
        from {
          opacity: 0;
          transform: translateY(12px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .dialog-header {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 16px;
        flex-shrink: 0;
      }
      .header-icon {
        flex: none;
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-soft) 100%);
        box-shadow: 0 6px 14px rgba(5, 66, 57, 0.28);
      }
      .header-icon mat-icon {
        color: #fff;
        font-size: 24px;
        width: 24px;
        height: 24px;
      }
      h2 {
        margin: 0 0 4px;
        font-size: 1.18rem;
        font-weight: 700;
        color: var(--gold);
      }
      .hint {
        margin: 0;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.55;
      }
      .spin {
        animation: spin 1s linear infinite;
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
      .load-error {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--danger);
        font-size: 0.85rem;
        margin: 0 0 12px;
      }
      .fields-shell {
        position: relative;
        flex: 1;
        min-height: min(44vh, 400px);
        display: flex;
        flex-direction: column;
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        background: #fff;
      }
      .fields-shell--loading .fields-grid {
        opacity: 0.72;
        transition: opacity 0.35s ease;
      }
      .fields-scroll {
        flex: 1;
        overflow: auto;
        min-height: min(36vh, 320px);
        max-height: min(70vh, 640px);
      }
      .fields-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 12px 14px;
        padding: 14px 16px 18px;
        align-content: start;
      }
      .field-card {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 0;
        padding: 10px 12px;
        border: 1px solid var(--line);
        border-radius: 10px;
        background: var(--gold-bg);
      }
      .field-card--wide {
        grid-column: 1 / -1;
      }
      .field-label {
        display: block;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--gold);
        line-height: 1.35;
        text-align: start;
        word-break: break-word;
      }
      .fields-shell--revealed .field-card {
        animation: field-card-in 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
      }
      @keyframes field-card-in {
        from {
          opacity: 0;
          transform: translateY(6px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      .preview-value {
        display: block;
        color: var(--muted);
        line-height: 1.45;
        word-break: break-word;
        font-size: 0.84rem;
        min-height: 2rem;
      }
      .field-card ::ng-deep .form-field,
      .field-card ::ng-deep .form-group {
        width: 100%;
        margin: 0;
      }
      .field-card ::ng-deep input,
      .field-card ::ng-deep textarea,
      .field-card ::ng-deep select {
        width: 100%;
        box-sizing: border-box;
      }
      @media (max-width: 720px) {
        .fields-grid {
          grid-template-columns: 1fr;
        }
      }
      .upload-hint {
        margin: 0 0 6px;
        font-size: 0.72rem;
        color: var(--muted);
      }
      .file-input {
        width: 100%;
        font-size: 0.75rem;
      }
      .loading-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: rgba(250, 247, 239, 0.5);
        color: var(--muted);
        pointer-events: none;
        animation: overlay-fade-in 0.35s ease forwards;
      }
      @keyframes overlay-fade-in {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        :host-context(.user-data-row-expand-ready) .dialog-wrapper,
        .fields-shell--revealed .field-card,
        .loading-overlay {
          animation: none !important;
          opacity: 1;
          transform: none;
        }
      }
      .footer {
        position: sticky;
        bottom: 0;
        z-index: var(--sticky-action-z, 20);
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 18px;
        margin-inline: -28px;
        margin-bottom: -18px;
        padding: 14px 28px 18px;
        padding-bottom: calc(18px + env(safe-area-inset-bottom, 0px));
        border-top: 1px solid var(--line, var(--sticky-action-border, #e5e7eb));
        background: var(--sticky-action-bg, rgba(255, 255, 255, 0.96));
        backdrop-filter: blur(6px);
        box-shadow: 0 -8px 16px -12px rgba(17, 24, 39, 0.18);
        flex-shrink: 0;
      }
    `,
  ],
})
export class UserDataRowEditDialogComponent implements OnInit {
  private dialogRef = inject(MatDialogRef<UserDataRowEditDialogComponent, boolean>);
  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  data = inject<UserDataRowEditDialogData>(MAT_DIALOG_DATA);

  protected readonly isEntityAttributeType = isEntityAttributeType;
  t = (key: string) => this.translation.t(key);

  displayColumns(): UserDataRowEditFieldColumn[] {
    const map = new Map<string, UserDataRowEditFieldColumn>();
    for (const col of this.data.fieldColumns || []) {
      map.set(col.id, col);
    }
    for (const field of this.fields()) {
      const id = String(field.attributeId);
      const existing = map.get(id);
      map.set(id, {
        id,
        label: field.label,
        preview: existing?.preview ?? field.value ?? '—',
      });
    }
    return [...map.values()].sort((a, b) => a.label.localeCompare(b.label, 'ar'));
  }

  fieldForColumn(attrId: string): RowFieldEdit | null {
    return this.fields().find((f) => String(f.attributeId) === attrId) ?? null;
  }

  fieldCellDelay(index: number): number {
    return 180 + Math.min(index, 16) * 35;
  }

  isWideColumn(attrId: string): boolean {
    const field = this.fieldForColumn(attrId);
    if (!field) return false;
    return field.type === 'textarea' || field.type === 'image' || field.type === 'file';
  }

  loading = signal(true);
  saving = signal(false);
  loadError = signal('');
  fields = signal<RowFieldEdit[]>([]);
  attributes = signal<BuilderAttribute[]>([]);
  uploadLimits = signal<{ max_upload_bytes: number }>({ max_upload_bytes: 2 * 1024 * 1024 });
  uploadingFieldId = signal<number | null>(null);

  ngOnInit(): void {
    this.builder.getUploadLimits().subscribe({
      next: (res) => this.uploadLimits.set(res),
    });
    this.loadRowFields();
  }

  private loadRowFields(): void {
    const ids = this.data.infoIds.filter((id) => id > 0);
    if (!ids.length) {
      this.loadError.set(this.t('user-data.load-error'));
      this.loading.set(false);
      return;
    }
    forkJoin({
      attrs: this.builder.getAllAttributes(),
      infos: forkJoin(
        ids.map((id) =>
          this.api.get<Info>(`/infos/${id}/detail/`).pipe(catchError(() => of(null))),
        ),
      ),
    })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe(({ attrs, infos }) => {
        this.attributes.set(attrs.results || []);
        const valid = infos.filter((i): i is Info => i != null);
        if (valid.length !== ids.length) {
          this.loadError.set(this.t('user-data.load-error'));
          return;
        }
        if (valid.some((i) => isInfoAccepted(i.confirmed))) {
          this.loadError.set(this.t('user-data.cannot-modify-approved'));
          return;
        }
        const attrList = this.attributes();
        const built: RowFieldEdit[] = valid.map((info) => {
          const attr = attrList.find((a) => a.id === info.attribute) ?? {
            id: info.attribute,
            title_id: info.title_id ?? 0,
            label: info.attribute_label,
            type: 'text',
            required: false,
            order: 0,
            options: [],
          };
          const attrType = (attr.type as AttributeType) || 'text';
          return {
            infoId: info.id,
            attributeId: info.attribute,
            label: info.attribute_label || attr.label,
            type: attrType,
            value: isLocationAttributeType(attrType)
              ? this.initialLocationValue(info, attrType)
              : (info.value ?? ''),
            options:
              attrType === 'select'
                ? (attr.options || []).map((o) => ({
                    value: o.label,
                    label: o.label,
                  }))
                : [],
          };
        });
        built.sort((a, b) => a.label.localeCompare(b.label, 'ar'));
        this.fields.set(built);
        this.hydrateLocationFields(built, attrList);
        this.hydrateEntityFields(built, attrList);
      });
  }

  private hydrateEntityFields(built: RowFieldEdit[], attrList: BuilderAttribute[]): void {
    for (const entityType of ENTITY_ATTRIBUTE_TYPES) {
      if (!attrList.some((a) => a.type === entityType) && !built.some((f) => f.type === entityType)) {
        continue;
      }
      this.builder.getEntityOptions(entityType, { limit: 500 }).subscribe({
        next: (rows) => {
          this.fields.update((list) =>
            list.map((f) => {
              if (f.type !== entityType) return f;
              const options = (rows || []).map((r) => ({
                value: String(r.id),
                label: r.label,
              }));
              const hasCurrent =
                !f.value || options.some((o) => String(o.value) === String(f.value));
              if (!hasCurrent && f.value) {
                options.unshift({ value: String(f.value), label: String(f.value) });
              }
              return { ...f, options };
            }),
          );
        },
      });
    }
  }

  private initialLocationValue(info: Info, type: AttributeType): string {
    const idByType: Partial<Record<AttributeType, number | null | undefined>> = {
      city: info.loc_governorate,
      district: info.loc_district,
      sub_district: info.loc_subdistrict,
      community: info.loc_community,
    };
    const locId = idByType[type];
    if (locId != null) return String(locId);
    return info.value ?? '';
  }

  private hydrateLocationFields(built: RowFieldEdit[], attrList: BuilderAttribute[]): void {
    this.builder.getCities().subscribe({
      next: (res) => {
        const governorates = res.results || [];
        this.fields.update((list) =>
          list.map((f) => {
            const attr = attrList.find((a) => a.id === f.attributeId);
            if (attr?.type === 'city') {
              return {
                ...f,
                options: this.idOptions(governorates, f.value),
              };
            }
            return f;
          }),
        );
        this.loadDependentLocationOptions(built, attrList, governorates);
      },
    });
  }

  private loadDependentLocationOptions(
    built: RowFieldEdit[],
    attrList: BuilderAttribute[],
    governorates: { id: number; name: string }[],
  ): void {
    const govField = built.find(
      (f) => attrList.find((a) => a.id === f.attributeId)?.type === 'city',
    );
    const govId = govField
      ? Number(govField.value) ||
        governorates.find((g) => g.name === govField.value.trim())?.id ||
        null
      : null;

    const distField = built.find(
      (f) => attrList.find((a) => a.id === f.attributeId)?.type === 'district',
    );
    const distIdFromField = distField ? Number(distField.value) || null : null;

    const loadChain = (districtId: number | null, subdistrictId: number | null) => {
      if (subdistrictId) {
        this.builder.getCommunities(subdistrictId).subscribe({
          next: (res) => this.applyOptionsForType('community', res.results || [], attrList),
        });
      }
      if (districtId) {
        this.builder.getSubDistricts(districtId).subscribe({
          next: (res) => {
            this.applyOptionsForType('sub_district', res.results || [], attrList);
            const subField = this.fields().find(
              (f) => attrList.find((a) => a.id === f.attributeId)?.type === 'sub_district',
            );
            const subId = subField ? Number(subField.value) || null : null;
            if (subId) {
              this.builder.getCommunities(subId).subscribe({
                next: (r) => this.applyOptionsForType('community', r.results || [], attrList),
              });
            }
          },
        });
      }
    };

    if (govId) {
      this.builder.getDistricts(govId).subscribe({
        next: (res) => {
          this.applyOptionsForType('district', res.results || [], attrList);
          const districtId =
            distIdFromField ||
            (distField
              ? ((res.results || []).find((d) => d.name === distField.value.trim())?.id ?? null)
              : null);
          loadChain(districtId, null);
        },
      });
      return;
    }

    if (distIdFromField) {
      this.builder.getDistricts().subscribe({
        next: (res) => {
          this.applyOptionsForType('district', res.results || [], attrList);
          loadChain(distIdFromField, null);
        },
      });
    }
  }

  private applyOptionsForType(
    type: AttributeType,
    items: { id: number; name: string }[],
    attrList: BuilderAttribute[],
  ): void {
    this.fields.update((list) =>
      list.map((f) => {
        const attr = attrList.find((a) => a.id === f.attributeId);
        if (attr?.type !== type) return f;
        return { ...f, options: this.idOptions(items, f.value) };
      }),
    );
  }

  private idOptions(items: { id: number; name: string }[], currentValue: string): SelectOption[] {
    const opts = items.map((item) => ({ value: String(item.id), label: item.name }));
    return this.withLegacyOption(opts, currentValue);
  }

  onLocationFieldChange(field: RowFieldEdit, value: string | number): void {
    this.setFieldValue(field.infoId, value);
    const attrList = this.attributes();
    const attr = attrList.find((a) => a.id === field.attributeId);
    if (!attr || !isLocationAttributeType(attr.type)) return;

    if (attr.type === 'city') {
      const govId = Number(value) || null;
      this.builder.getDistricts(govId ?? undefined).subscribe({
        next: (res) => {
          this.applyOptionsForType('district', res.results || [], attrList);
          this.clearLowerLocationValues(['district', 'sub_district', 'community'], attrList);
        },
      });
      return;
    }

    if (attr.type === 'district') {
      const distId = Number(value) || null;
      this.builder.getSubDistricts(distId ?? undefined).subscribe({
        next: (res) => {
          this.applyOptionsForType('sub_district', res.results || [], attrList);
          this.clearLowerLocationValues(['sub_district', 'community'], attrList);
        },
      });
      return;
    }

    if (attr.type === 'sub_district') {
      const subId = Number(value) || null;
      this.builder.getCommunities(subId ?? undefined).subscribe({
        next: (res) => {
          this.applyOptionsForType('community', res.results || [], attrList);
          this.clearLowerLocationValues(['community'], attrList);
        },
      });
    }
  }

  private clearLowerLocationValues(types: AttributeType[], attrList: BuilderAttribute[]): void {
    const ids = new Set(
      types
        .map((type) => attrList.find((a) => a.type === type)?.id)
        .filter((id): id is number => id != null),
    );
    this.fields.update((list) =>
      list.map((f) => (ids.has(f.attributeId) ? { ...f, value: '' } : f)),
    );
  }

  private withLegacyOption(opts: SelectOption[], currentValue: string): SelectOption[] {
    const current = String(currentValue ?? '').trim();
    if (!current) return opts;
    if (opts.some((o) => String(o.value) === current)) return opts;
    const legacyLabel = /^\d+$/.test(current)
      ? current
      : this.t('user-data.legacy-option-label').replace('{value}', current);
    return [{ value: current, label: legacyLabel }, ...opts];
  }

  booleanChecked(field: RowFieldEdit): boolean {
    const v = String(field.value ?? '')
      .trim()
      .toLowerCase();
    return v === 'true' || v === '1' || v === 'yes' || v === 'نعم';
  }

  setBooleanValue(infoId: number, checked: boolean): void {
    this.setFieldValue(infoId, checked ? 'true' : 'false');
  }

  setFieldValue(infoId: number, value: string | number): void {
    const normalized = value == null ? '' : String(value).trim();
    this.fields.update((list) =>
      list.map((f) => (f.infoId === infoId ? { ...f, value: normalized } : f)),
    );
  }

  canSave(): boolean {
    return this.fields().every((f) => {
      if (f.type === 'boolean') return true;
      return String(f.value ?? '').trim().length > 0;
    });
  }

  save(): void {
    if (!this.canSave() || this.saving()) return;
    this.saving.set(true);
    const patches = this.fields().map((f) =>
      this.api.patch(`/infos/${f.infoId}/`, { value: f.value.trim() }),
    );
    let done = 0;
    let failed = false;
    for (const req of patches) {
      req.subscribe({
        next: () => {
          done++;
          if (done === patches.length && !failed) {
            this.toast.success(this.t('user-data.update-success'));
            this.dialogRef.close(true);
          }
        },
        error: () => {
          if (!failed) {
            failed = true;
            this.saving.set(false);
            this.toast.error(this.t('user-data.update-error'));
          }
        },
      });
    }
  }

  cancel(): void {
    this.dialogRef.close(false);
  }

  maxUploadMb(): string {
    const b = this.uploadLimits().max_upload_bytes || 2 * 1024 * 1024;
    return (b / (1024 * 1024)).toFixed(1).replace(/\.0$/, '');
  }

  mediaAccept(type: AttributeType): string {
    if (type === 'image') {
      return 'image/jpeg,image/png,image/gif,image/webp,.jpg,.jpeg,.png,.gif,.webp';
    }
    return [
      'application/pdf',
      '.pdf',
      '.doc',
      '.docx',
      '.xls',
      '.xlsx',
      '.txt',
      '.csv',
      '.zip',
      'image/jpeg',
      'image/png',
      '.jpg',
      '.jpeg',
      '.png',
    ].join(',');
  }

  onMediaFileSelected(event: Event, field: RowFieldEdit): void {
    const kind = field.type === 'image' ? 'image' : 'file';
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > this.uploadLimits().max_upload_bytes) {
      this.toast.error(this.t('builder.file-too-large').replace('{mb}', this.maxUploadMb()));
      input.value = '';
      return;
    }
    this.uploadingFieldId.set(field.infoId);
    this.builder.uploadFormFile(file, kind).subscribe({
      next: (res) => {
        this.setFieldValue(field.infoId, res.url);
        this.uploadingFieldId.set(null);
        this.toast.success(this.t('builder.file-upload-success'));
      },
      error: () => {
        this.uploadingFieldId.set(null);
        this.toast.error(this.t('builder.file-upload-error'));
        input.value = '';
      },
    });
  }
}
