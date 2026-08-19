import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, input, output, signal } from '@angular/core';
import {
  ReactiveFormsModule,
  UntypedFormBuilder,
  UntypedFormControl,
  UntypedFormGroup,
  Validators,
} from '@angular/forms';
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
import { PageLoaderComponent } from '../../shared/components/page-loader/page-loader.component';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import type { MasterFieldSchema, MasterResourceMeta } from './master-data.models';
import { MasterDataService } from './master-data.service';

@Component({
  selector: 'app-master-data-quick-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ModalComponent,
    PageLoaderComponent,
    FormInputComponent,
    FormSelectComponent,
    FormSearchSelectComponent,
    FormCheckboxComponent,
    FormDateComponent,
    FormMapPickerComponent,
    ButtonComponent,
  ],
  template: `
    <app-modal
      [visible]="visible()"
      [title]="title()"
      size="large"
      (close)="closed.emit()"
    >
      <app-page-loader *ngIf="loading()" [message]="t('dashboard.loading')" />
      <form *ngIf="!loading() && meta()" class="qc-form" [formGroup]="form">
        <app-form-map-picker
          *ngIf="showMap()"
          [form]="form"
          latitudeControl="latitude"
          longitudeControl="longitude"
          [label]="t('master-data.map')"
        />
        <div class="qc-fields">
          <ng-container *ngFor="let field of visibleFields()">
            <div
              class="qc-field"
              *ngIf="!(showMap() && (field.name === 'latitude' || field.name === 'longitude'))"
              [class.qc-field--full]="field.type === 'textarea'"
            >
              <app-form-input
                *ngIf="field.type === 'string' || field.type === 'number'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
                [type]="field.type === 'number' ? 'number' : 'text'"
                [required]="field.required"
              />
              <app-form-input
                *ngIf="field.type === 'textarea'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
                type="text"
                [multiline]="true"
                [rows]="3"
                [required]="field.required"
              />
              <app-form-checkbox
                *ngIf="field.type === 'boolean'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
              />
              <app-form-date
                *ngIf="field.type === 'date' || field.type === 'datetime'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
                [required]="field.required"
              />
              <app-form-select
                *ngIf="field.type === 'choice'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
                [options]="choiceOpts(field)"
                [required]="field.required"
              />
              <app-form-search-select
                *ngIf="field.type === 'foreign_key'"
                [formControlName]="field.name"
                [label]="labelOf(field.name)"
                [options]="fkOpts(field)"
                [required]="field.required"
              />
            </div>
          </ng-container>
        </div>
      </form>
      <div footer class="qc-actions" *ngIf="!loading() && meta()">
        <app-button variant="ghost" [label]="t('master-data.cancel')" type="button" (clicked)="closed.emit()" />
        <app-button
          variant="primary"
          [label]="t('master-data.save')"
          type="button"
          [disabled]="saving()"
          (clicked)="save()"
        />
      </div>
    </app-modal>
  `,
  styles: [
    `
      .qc-fields {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem 1rem;
      }
      .qc-field--full {
        grid-column: 1 / -1;
      }
      .qc-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.65rem;
      }
      .qc-form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }
      @media (max-width: 720px) {
        .qc-fields {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class MasterDataQuickCreateComponent implements OnInit {
  slug = input.required<string>();
  visible = input(true);
  saved = output<void>();
  closed = output<void>();

  private api = inject(MasterDataService);
  private fb = inject(UntypedFormBuilder);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  loading = signal(true);
  saving = signal(false);
  meta = signal<MasterResourceMeta | null>(null);
  form: UntypedFormGroup = this.fb.group({});
  fkOptions = signal<Record<string, SelectOption[]>>({});

  title = signal('');

  ngOnInit(): void {
    this.api.getRegistry().subscribe({
      next: (res) => {
        const m = res.resources.find((r) => r.slug === this.slug()) || null;
        this.meta.set(m);
        this.title.set(
          m ? `${this.t('master-data.add')} — ${m.label_ar || m.label_en}` : this.t('master-data.add'),
        );
        if (m) {
          this.buildForm(m);
          this.prefetchFk(m);
        }
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.toast.error(this.t('master-data.load-error'));
        this.closed.emit();
      },
    });
  }

  visibleFields(): MasterFieldSchema[] {
    const m = this.meta();
    if (!m) return [];
    return m.fields.filter(
      (f) => f.name !== 'id' && !f.read_only && f.name !== 'geometry_type',
    );
  }

  showMap(): boolean {
    const m = this.meta();
    if (!m?.has_map) return false;
    const names = new Set(m.fields.map((f) => f.name));
    return names.has('latitude') && names.has('longitude');
  }

  labelOf(name: string): string {
    const key = `master-data.col.${name}`;
    const translated = this.t(key);
    return translated !== key ? translated : name.replace(/_/g, ' ');
  }

  choiceOpts(field: MasterFieldSchema): SelectOption[] {
    return (field.choices || []).map((c) => ({ value: c.value, label: c.label }));
  }

  fkOpts(field: MasterFieldSchema): SelectOption[] {
    if (!field.related_slug) return [];
    return this.fkOptions()[field.related_slug] || [];
  }

  save(): void {
    const m = this.meta();
    if (!m) return;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.toast.error(this.t('master-data.form-invalid'));
      return;
    }
    const body: Record<string, unknown> = { ...(m.default_create_values || {}) };
    const raw = this.form.getRawValue() as Record<string, unknown>;
    for (const field of this.visibleFields()) {
      let val = raw[field.name];
      if (val === '' && !field.required) continue;
      if (field.type === 'boolean') val = Boolean(val);
      else if (field.type === 'number' || field.type === 'foreign_key') {
        val = val === '' || val == null ? null : Number(val);
      }
      body[field.name] = val;
    }
    this.saving.set(true);
    this.api.create(m.slug, body).subscribe({
      next: () => {
        this.saving.set(false);
        this.toast.success(this.t('master-data.saved'));
        this.saved.emit();
        this.closed.emit();
      },
      error: (err) => {
        this.saving.set(false);
        this.toast.error(String(err?.error?.detail || this.t('master-data.save-error')));
      },
    });
  }

  private buildForm(m: MasterResourceMeta): void {
    const group: Record<string, UntypedFormControl> = {};
    for (const field of m.fields) {
      if (field.name === 'id' || field.read_only) continue;
      let value: unknown = field.type === 'boolean' ? false : '';
      if (m.default_create_values && field.name in m.default_create_values) {
        value = m.default_create_values[field.name];
      }
      group[field.name] = new UntypedFormControl(
        value,
        field.required ? [Validators.required] : [],
      );
    }
    this.form = this.fb.group(group);
  }

  private prefetchFk(m: MasterResourceMeta): void {
    for (const field of m.fields) {
      if (field.type !== 'foreign_key' || !field.related_slug) continue;
      const slug = field.related_slug;
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
}
