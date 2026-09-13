import {
  Component,
  Input,
  Output,
  EventEmitter,
  forwardRef,
  OnChanges,
  SimpleChanges,
  inject,
  computed,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, FormsModule } from '@angular/forms';
import { LanguageService } from '../../services/language.service';
import type { SelectOption, SelectValue } from '../form-select/form-select.component';

export type { SelectOption } from '../form-select/form-select.component';

/** Selected values are stored as primitive IDs. */
export type MultiSelectValue = SelectValue;

/** Show this many chips before collapsing the rest behind «+N more». */
const CHIP_PREVIEW_LIMIT = 8;

@Component({
  selector: 'app-form-multi-select',
  standalone: true,
  imports: [CommonModule, FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormMultiSelectComponent),
      multi: true,
    },
  ],
  template: `
    <div class="field" [class.has-error]="!!errorMessage">
      <label *ngIf="label">
        {{ label }}
        <span *ngIf="required" class="required">*</span>
      </label>

      <!-- Select Dropdown + Select All -->
      <div class="select-row">
        <select class="custom-select" (change)="onSelectChange($event)" [disabled]="disabled">
          <option value="">{{ placeholder }}</option>
          <option *ngFor="let option of availableOptions()" [value]="option.value">
            {{ option.label }}
          </option>
        </select>
        <button
          *ngIf="availableOptions().length > 0 && !disabled"
          type="button"
          class="select-all-btn"
          (click)="selectAll()"
          [title]="labels().selectAll"
        >
          {{ labels().selectAll }}
        </button>
      </div>

      <!-- Selected Chips Box -->
      <div class="chips-box">
        <div *ngIf="value.length === 0" class="empty-state">
          {{ labels().empty }}
        </div>
        <ng-container *ngIf="value.length > 0">
          <div *ngFor="let item of visibleChips()" class="chip-item">
            <span>{{ item.label }}</span>
            <button
              type="button"
              class="chip-remove"
              (click)="removeItem(item.value)"
              [title]="labels().remove"
              [disabled]="disabled"
            >
              ✕
            </button>
          </div>
          <button
            *ngIf="hiddenChipCount() > 0 && !chipsExpanded()"
            type="button"
            class="more-chips-btn"
            (click)="chipsExpanded.set(true)"
          >
            +{{ hiddenChipCount() }} {{ labels().more }}
          </button>
          <button
            *ngIf="chipsExpanded() && selectedItems().length > CHIP_PREVIEW_LIMIT"
            type="button"
            class="more-chips-btn"
            (click)="chipsExpanded.set(false)"
          >
            {{ labels().showLess }}
          </button>
          <button
            *ngIf="!disabled"
            type="button"
            class="clear-all-btn"
            (click)="clearAll()"
            [title]="labels().clearAll"
          >
            {{ labels().clearAll }}
          </button>
        </ng-container>
      </div>

      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-multi-select.component.scss',
})
export class FormMultiSelectComponent implements ControlValueAccessor, OnChanges {
  private language = inject(LanguageService);

  readonly CHIP_PREVIEW_LIMIT = CHIP_PREVIEW_LIMIT;
  chipsExpanded = signal(false);

  labels = computed(() =>
    this.language.lang() === 'ar'
      ? {
          selectAll: 'تحديد الكل',
          clearAll: 'إلغاء الكل',
          empty: 'لم يتم الاختيار بعد',
          remove: 'إزالة',
          more: 'أخرى',
          showLess: 'عرض أقل',
        }
      : {
          selectAll: 'Select All',
          clearAll: 'Clear All',
          empty: 'No items selected',
          remove: 'Remove',
          more: 'more',
          showLess: 'Show less',
        },
  );

  @Input() label = '';
  @Input() placeholder = 'اختر';
  @Input() options: SelectOption[] = [];
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() filterByParent: (option: SelectOption) => boolean = () => true;
  @Input() formValues: Record<string, unknown> = {};
  /** Maximum selected items (0 = unlimited). */
  @Input() maxSelections = 0;

  @Output() valueChange = new EventEmitter<MultiSelectValue[]>();

  value: MultiSelectValue[] = [];
  selectedValue: MultiSelectValue | '' = '';

  onChange: (value: MultiSelectValue[]) => void = () => {};
  onTouched: () => void = () => {};

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['options'] && !changes['options'].firstChange) {
      // Options have been updated, force template re-render
    }
  }

  availableOptions(): SelectOption[] {
    return this.options.filter((opt) => {
      const notSelected = !this.value.includes(opt.value);
      const passesFilter = this.filterByParent ? this.filterByParent(opt) : true;
      return notSelected && passesFilter;
    });
  }

  selectedItems(): SelectOption[] {
    return this.value
      .map((v) => this.options.find((o) => o.value === v))
      .filter((item): item is SelectOption => !!item);
  }

  visibleChips(): SelectOption[] {
    const items = this.selectedItems();
    if (this.chipsExpanded() || items.length <= CHIP_PREVIEW_LIMIT) {
      return items;
    }
    return items.slice(0, CHIP_PREVIEW_LIMIT);
  }

  hiddenChipCount(): number {
    const total = this.selectedItems().length;
    if (this.chipsExpanded() || total <= CHIP_PREVIEW_LIMIT) return 0;
    return total - CHIP_PREVIEW_LIMIT;
  }

  onSelectChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    const stringValue = select.value;
    if (stringValue !== '') {
      // Convert back to the actual type (number if it looks like a number)
      const actualValue = isNaN(Number(stringValue)) ? stringValue : Number(stringValue);
      this.addItem(actualValue);
    }
    // Reset native select so the same option can be re-picked after removal,
    // and avoid leaving focus on a destroyed option list (scroll jump).
    select.selectedIndex = 0;
  }

  addItem(val?: MultiSelectValue): void {
    const itemValue = val !== undefined ? val : this.selectedValue;
    if (itemValue === '' || itemValue === null || itemValue === undefined) return;
    if (this.maxSelections > 0 && this.value.length >= this.maxSelections) return;
    this.value = [...this.value, itemValue];
    this.onChange(this.value);
    this.valueChange.emit(this.value);
  }

  removeItem(val: MultiSelectValue): void {
    this.value = this.value.filter((v) => v !== val);
    this.onChange(this.value);
    this.valueChange.emit(this.value);
  }

  selectAll(): void {
    const allValues = this.availableOptions().map((o) => o.value);
    let merged = [...this.value, ...allValues];
    if (this.maxSelections > 0) {
      merged = merged.slice(0, this.maxSelections);
    }
    this.value = merged;
    this.onChange(this.value);
    this.valueChange.emit(this.value);
  }

  clearAll(): void {
    this.value = [];
    this.chipsExpanded.set(false);
    this.onChange(this.value);
    this.valueChange.emit(this.value);
  }

  writeValue(value: MultiSelectValue[] | null): void {
    this.value = Array.isArray(value) ? value : [];
    if (this.value.length <= CHIP_PREVIEW_LIMIT) {
      this.chipsExpanded.set(false);
    }
  }

  registerOnChange(fn: (value: MultiSelectValue[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
