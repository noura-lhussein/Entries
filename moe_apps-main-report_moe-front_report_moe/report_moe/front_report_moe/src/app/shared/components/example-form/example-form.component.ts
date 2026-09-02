import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
  Output,
  EventEmitter,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormGroup,
  Validators,
  ValidatorFn,
} from '@angular/forms';
import { ButtonComponent } from '../button/button.component';
import { FormInputComponent } from '../form-input/form-input.component';
import { FormSelectComponent, type SelectOption } from '../form-select/form-select.component';
import { FormMultiSelectComponent } from '../form-multi-select/form-multi-select.component';
import { FormCheckboxComponent } from '../form-checkbox/form-checkbox.component';
import { FormDateComponent } from '../form-date/form-date.component';
import { TableComponent, type TableColumn, type TableRow } from '../table/table.component';
import { ToastService } from '../../services/toast.service';
import { DialogService } from '../../services/dialog.service';
import { TranslationService } from '../../services/translation.service';
import { BuilderService } from '../../../core/services/builder.service';
import { StoredMediaValueComponent } from '../stored-media-value/stored-media-value.component';

export type InputType = 'text' | 'email' | 'password' | 'number' | 'date' | 'tel' | 'url';

export interface FormFieldConfig {
  key: string;
  type: 'input' | 'textarea' | 'select' | 'multi-select' | 'checkbox' | 'date' | 'file';
  label: string;
  placeholder?: string;
  inputType?: InputType;
  icon?: string;
  hint?: string;
  required?: boolean;
  disabled?: boolean;
  validators?: ValidatorFn[];
  options?: SelectOption[];
  defaultValue?: any;
  filterFunction?: (option: SelectOption, formValues: any) => boolean;
  /** When type is `file`: restrict picker (browser hint only). */
  fileAccept?: string;
  /** When type is `file`: server-side validation category for upload. */
  fileKind?: 'image' | 'file';
}

export interface FormConfig {
  title: string;
  subtitle?: string;
  submitLabel?: string;
  hideSubmitButton?: boolean;
  fields: FormFieldConfig[];
  showTable?: boolean;
  tableColumns?: TableColumn[];
  tableActions?: any[];
  tableData?: TableRow[];
  showDebug?: boolean;
}

@Component({
  selector: 'app-example-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonComponent,
    FormInputComponent,
    FormSelectComponent,
    FormMultiSelectComponent,
    FormCheckboxComponent,
    FormDateComponent,
    TableComponent,
    StoredMediaValueComponent,
  ],
  templateUrl: './example-form.component.html',
  styleUrls: ['./example-form.component.scss'],
})
export class ExampleFormComponent implements OnInit, OnChanges {
  @Input() formConfig!: FormConfig;
  @Output() fieldChange = new EventEmitter<{ key: string; value: any }>();
  @Output() submit = new EventEmitter<void>();

  private fb = inject(FormBuilder);
  private toastService = inject(ToastService);
  private dialogService = inject(DialogService);
  private translation = inject(TranslationService);
  private builder = inject(BuilderService);
  t = (key: string) => this.translation.t(key);

  userForm!: FormGroup;
  uploadLimits: { max_upload_bytes: number } | null = null;
  fileUploading = false;

  private defaultConfig: FormConfig = {
    title: 'نموذج المستخدم - User Form Example',
    subtitle: 'Demonstrates all reusable form components',
    fields: [
      {
        key: 'name',
        type: 'input',
        label: 'Full Name',
        placeholder: 'Enter full name',
        inputType: 'text',
        icon: 'person',
        hint: 'First and last name',
        required: true,
        validators: [Validators.minLength(3)],
      },
      {
        key: 'email',
        type: 'input',
        label: 'Email Address',
        placeholder: 'user@example.com',
        inputType: 'email',
        icon: 'email',
        required: true,
        validators: [Validators.email],
      },
      {
        key: 'age',
        type: 'input',
        label: 'Age',
        placeholder: '25',
        inputType: 'number',
        validators: [Validators.min(18), Validators.max(100)],
      },
      {
        key: 'phone',
        type: 'input',
        label: 'Phone Number',
        placeholder: '+966 50 000 0000',
        inputType: 'tel',
        icon: 'phone',
      },
      {
        key: 'joinDate',
        type: 'date',
        label: 'Join Date',
        required: true,
      },
      {
        key: 'role',
        type: 'select',
        label: 'Role',
        placeholder: 'Select a role',
        icon: 'work',
        options: [
          { value: 'admin', label: 'Administrator' },
          { value: 'manager', label: 'Manager' },
          { value: 'user', label: 'User' },
          { value: 'viewer', label: 'Viewer' },
        ],
        required: true,
      },
      {
        key: 'departments',
        type: 'multi-select',
        label: 'Departments',
        placeholder: 'Select departments',
        options: [
          { value: 1, label: 'Engineering' },
          { value: 2, label: 'Sales' },
          { value: 3, label: 'Marketing' },
          { value: 4, label: 'HR' },
          { value: 5, label: 'Finance' },
        ],
        required: true,
      },
      {
        key: 'active',
        type: 'checkbox',
        label: 'Active Account',
        hint: 'Check to enable this account',
        defaultValue: true,
      },
    ],
    showTable: true,
    tableColumns: [
      { key: 'id', label: 'ID', sortable: true, width: '60px' },
      { key: 'name', label: 'Name', sortable: true },
      { key: 'email', label: 'Email', sortable: true },
      { key: 'role', label: 'Role', sortable: true },
      {
        key: 'joinDate',
        label: 'Join Date',
        sortable: true,
        format: (val) => new Date(val).toLocaleDateString('ar-SA'),
      },
      { key: 'active', label: 'Status', format: (val) => (val ? '✓ Active' : '✗ Inactive') },
    ],
    tableActions: [
      { type: 'edit', label: 'Edit', icon: 'edit', color: 'primary' },
      { type: 'delete', label: 'Delete', icon: 'delete', color: 'warn' },
    ],
    tableData: [
      {
        id: 1,
        name: 'أحمد محمد',
        email: 'ahmed@example.com',
        role: 'admin',
        department: 'Engineering',
        joinDate: '2024-01-15',
        active: true,
      },
      {
        id: 2,
        name: 'فاطمة علي',
        email: 'fatima@example.com',
        role: 'manager',
        department: 'Sales',
        joinDate: '2024-02-20',
        active: true,
      },
      {
        id: 3,
        name: 'محمود حسن',
        email: 'mahmoud@example.com',
        role: 'user',
        department: 'Marketing',
        joinDate: '2024-03-10',
        active: false,
      },
      {
        id: 4,
        name: 'نورا خالد',
        email: 'nora@example.com',
        role: 'viewer',
        department: 'HR',
        joinDate: '2024-04-05',
        active: true,
      },
      {
        id: 5,
        name: 'سارة إبراهيم',
        email: 'sarah@example.com',
        role: 'user',
        department: 'Finance',
        joinDate: '2024-04-12',
        active: true,
      },
    ],
    showDebug: true,
  };

  ngOnInit(): void {
    this.formConfig = this.formConfig || this.defaultConfig;
    this.initForm();
    const needsLimits = this.formConfig.fields.some((f) => f.type === 'file');
    if (needsLimits) {
      this.builder.getUploadLimits().subscribe({
        next: (l) => (this.uploadLimits = l),
        error: () => (this.uploadLimits = { max_upload_bytes: 2 * 1024 * 1024 }),
      });
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['formConfig'] && !changes['formConfig'].firstChange && this.userForm) {
      this.formConfig.fields.forEach((field) => {
        const control = this.userForm.get(field.key);
        if (!control) return;
        if (field.disabled) {
          control.disable({ emitEvent: false });
        } else {
          control.enable({ emitEvent: false });
        }
      });
    }
  }

  private initForm(): void {
    const formConfig: { [key: string]: any } = {};

    this.formConfig.fields.forEach((field) => {
      const validators = [];
      if (field.required) {
        validators.push(Validators.required);
      }
      if (field.validators) {
        validators.push(...field.validators);
      }

      const defaultValue = field.defaultValue ?? '';
      formConfig[field.key] = [
        { value: defaultValue, disabled: field.disabled ?? false },
        validators,
      ];
    });

    this.userForm = this.fb.group(formConfig);

    // Emit fieldChange per individual control
    Object.keys(this.userForm.controls).forEach((key) => {
      this.userForm.get(key)?.valueChanges.subscribe((value) => {
        this.fieldChange.emit({ key, value });
      });
    });
  }

  getFormData(): any {
    return this.userForm.getRawValue();
  }

  isFormValid(): boolean {
    if (!this.userForm.valid) {
      this.userForm.markAllAsTouched();
      return false;
    }
    return true;
  }

  setServerErrors(errors: Record<string, string | string[]>): void {
    for (const [field, messages] of Object.entries(errors)) {
      const control = this.userForm.get(field);
      if (control) {
        const message = Array.isArray(messages) ? messages[0] : messages;
        control.setErrors({ serverError: message });
        control.markAsTouched();
      }
    }
  }

  onReset(): void {
    if (!this.userForm || !this.formConfig?.fields?.length) return;
    const patch: Record<string, unknown> = {};
    for (const field of this.formConfig.fields) {
      if (field.type === 'checkbox') {
        patch[field.key] = field.defaultValue ?? false;
      } else if (field.type === 'multi-select') {
        patch[field.key] = field.defaultValue ?? [];
      } else {
        patch[field.key] = field.defaultValue ?? '';
      }
    }
    this.userForm.reset(patch);
    this.clearNativeFileInputs();
  }

  /** Native file inputs are not bound to reactive controls; clear them after save/reset. */
  private clearNativeFileInputs(): void {
    for (const field of this.formConfig.fields) {
      if (field.type !== 'file') continue;
      const el = document.getElementById(`file-${field.key}`) as HTMLInputElement | null;
      if (el) el.value = '';
    }
  }

  async onDelete(): Promise<void> {
    const confirmed = await this.dialogService.delete('this record');
    if (confirmed) {
      this.toastService.success(this.t('example-form.deleted-success'));
      this.onReset();
    }
  }

  onPageChange(event: any): void {
    this.toastService.info(
      this.t('example-form.page-info')
        .replace('{page}', String(event.pageIndex + 1))
        .replace('{size}', String(event.pageSize)),
    );
  }

  onSortChange(_event: unknown): void {}

  onRowClick(row: TableRow): void {
    this.toastService.info(
      this.t('example-form.selected-row').replace('{name}', String(row['name'] ?? '')),
    );
  }

  onTableAction(event: { type: string; row: TableRow }): void {
    if (event.type === 'edit') {
      this.toastService.info(
        this.t('example-form.edit-row').replace('{name}', String(event.row['name'] ?? '')),
      );
    } else if (event.type === 'delete') {
      this.dialogService.delete(event.row['name'] as string).then((confirmed) => {
        if (confirmed) {
          this.toastService.success(
            this.t('example-form.deleted-row').replace('{name}', String(event.row['name'] ?? '')),
          );
        }
      });
    }
  }

  onSelectionChange(selected: TableRow[]): void {
    if (selected.length > 0) {
      this.toastService.info(
        this.t('example-form.records-selected').replace('{count}', String(selected.length)),
      );
    }
  }

  getFieldError(fieldName: string): string {
    const field = this.userForm.get(fieldName);
    if (!field?.errors || !field?.touched) return '';

    const t = (key: string) => this.translation.t(key);

    if (field.hasError('serverError')) return field.getError('serverError');
    if (field.hasError('required')) return t('validation.required');
    if (field.hasError('minlength'))
      return t('validation.minlength').replace('{n}', field.getError('minlength').requiredLength);
    if (field.hasError('email')) return t('validation.email');
    if (field.hasError('min')) return t('validation.min').replace('{n}', field.getError('min').min);
    if (field.hasError('max')) return t('validation.max').replace('{n}', field.getError('max').max);

    return '';
  }

  getFilterFunction(field: FormFieldConfig): (option: SelectOption) => boolean {
    if (!field.filterFunction) {
      return () => true;
    }
    return (option: SelectOption) => field.filterFunction!(option, this.userForm.value);
  }

  maxUploadMb(): string {
    const b = this.uploadLimits?.max_upload_bytes ?? 2 * 1024 * 1024;
    return (b / (1024 * 1024)).toFixed(1).replace(/\.0$/, '');
  }

  onFileInputChange(field: FormFieldConfig, event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const max = this.uploadLimits?.max_upload_bytes ?? 2 * 1024 * 1024;
    if (file.size > max) {
      this.toastService.error(this.t('builder.file-too-large').replace('{mb}', this.maxUploadMb()));
      input.value = '';
      return;
    }

    const kind = field.fileKind ?? 'file';
    this.fileUploading = true;
    this.builder.uploadFormFile(file, kind).subscribe({
      next: (res) => {
        this.userForm.get(field.key)?.setValue(res.url);
        this.fileUploading = false;
        this.fieldChange.emit({ key: field.key, value: res.url });
        this.toastService.success(this.t('builder.file-upload-success'));
      },
      error: () => {
        this.fileUploading = false;
        this.toastService.error(this.t('builder.file-upload-error'));
        input.value = '';
      },
    });
  }

  clearUploadedFile(field: FormFieldConfig, inputId: string): void {
    this.userForm.get(field.key)?.setValue('');
    const el = document.getElementById(inputId) as HTMLInputElement | null;
    if (el) el.value = '';
    this.fieldChange.emit({ key: field.key, value: '' });
  }
}
