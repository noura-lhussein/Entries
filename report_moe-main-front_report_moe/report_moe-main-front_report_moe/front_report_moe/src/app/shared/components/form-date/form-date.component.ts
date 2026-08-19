import { Component, Input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';

@Component({
  selector: 'app-form-date',
  standalone: true,
  imports: [CommonModule, FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormDateComponent),
      multi: true,
    },
  ],
  template: `
    <div class="field" [class.has-error]="!!errorMessage">
      <label *ngIf="label" [for]="id">
        {{ label }}
        <span *ngIf="required" class="required">*</span>
      </label>
      <input
        type="date"
        [id]="id"
        [disabled]="disabled"
        [(ngModel)]="stringValue"
        (ngModelChange)="onValueChange($event)"
        (blur)="onTouched()"
      />
      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  styleUrl: './form-date.component.scss',
})
export class FormDateComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() id = `date-${Math.random().toString(36).slice(2, 9)}`;

  stringValue = '';

  onChange: (value: string | null) => void = () => {};
  onTouched: () => void = () => {};

  onValueChange(val: string): void {
    this.stringValue = val;
    this.onChange(val || null);
  }

  writeValue(value: Date | string | null): void {
    if (!value) {
      this.stringValue = '';
      return;
    }
    if (typeof value === 'string') {
      this.stringValue = value.slice(0, 10);
      return;
    }
    const y = value.getFullYear();
    const m = String(value.getMonth() + 1).padStart(2, '0');
    const d = String(value.getDate()).padStart(2, '0');
    this.stringValue = `${y}-${m}-${d}`;
  }

  registerOnChange(fn: (value: string | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
