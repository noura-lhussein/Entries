import { Component, Input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';

@Component({
  selector: 'app-form-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormInputComponent),
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
        *ngIf="!multiline"
        [id]="id"
        [type]="type"
        [attr.min]="type === 'number' && min != null ? min : null"
        [attr.max]="type === 'number' && max != null ? max : null"
        [attr.step]="type === 'number' && step != null ? step : null"
        [placeholder]="placeholder"
        [disabled]="disabled"
        [(ngModel)]="value"
        (ngModelChange)="onValueChange($event)"
        (blur)="onTouched()"
      />
      <textarea
        *ngIf="multiline"
        [id]="id"
        [rows]="rows"
        [placeholder]="placeholder"
        [disabled]="disabled"
        [(ngModel)]="value"
        (ngModelChange)="onValueChange($event)"
        (blur)="onTouched()"
      ></textarea>
      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  styleUrl: './form-input.component.scss',
})
export class FormInputComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() placeholder = '';
  @Input() type: 'text' | 'email' | 'password' | 'number' | 'date' | 'tel' | 'url' = 'text';
  @Input() multiline = false;
  @Input() rows = 4;
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() min: number | null = null;
  @Input() max: number | null = null;
  @Input() step: number | string | null = null;
  @Input() id = `inp-${Math.random().toString(36).slice(2, 9)}`;

  value: string | number = '';

  onChange: (value: string | number) => void = () => {};
  onTouched: () => void = () => {};

  onValueChange(val: string | number): void {
    if (this.type === 'number') {
      if (val === '') {
        this.value = '';
        this.onChange('');
        return;
      }
      const parsed = Number(val);
      if (Number.isFinite(parsed)) {
        let normalized = parsed;
        if (this.min != null && normalized < this.min) normalized = this.min;
        if (this.max != null && normalized > this.max) normalized = this.max;
        this.value = normalized;
        this.onChange(normalized);
        return;
      }
    }

    this.value = val;
    this.onChange(val);
  }

  writeValue(value: string | number | null): void {
    this.value = value ?? '';
  }

  registerOnChange(fn: (value: string | number) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
