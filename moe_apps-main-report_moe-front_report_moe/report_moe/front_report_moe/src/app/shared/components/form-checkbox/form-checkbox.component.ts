import { Component, Input, forwardRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';

@Component({
  selector: 'app-form-checkbox',
  standalone: true,
  imports: [CommonModule, FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormCheckboxComponent),
      multi: true,
    },
  ],
  template: `
    <div class="field">
      <label class="checkbox-row" [for]="id">
        <input
          type="checkbox"
          [id]="id"
          [checked]="value"
          [disabled]="disabled"
          (change)="onValueChange($any($event.target).checked)"
          (blur)="onTouched()"
        />
        <span class="text">{{ label }}</span>
      </label>
      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  styleUrl: './form-checkbox.component.scss',
})
export class FormCheckboxComponent implements ControlValueAccessor {
  @Input() label = '';
  @Input() disabled = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() id = `chk-${Math.random().toString(36).slice(2, 9)}`;

  value = false;

  onChange: (value: boolean) => void = () => {};
  onTouched: () => void = () => {};

  onValueChange(val: boolean): void {
    this.value = val;
    this.onChange(val);
  }

  writeValue(value: unknown): void {
    this.value = !!value;
  }

  registerOnChange(fn: (value: boolean) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
