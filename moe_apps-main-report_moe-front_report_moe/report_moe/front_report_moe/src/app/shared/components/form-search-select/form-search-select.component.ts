import { OverlayModule, type ConnectedPosition } from '@angular/cdk/overlay';
import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  Input,
  ViewChild,
  forwardRef,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';
import type { SelectOption, SelectValue } from '../form-select/form-select.component';

export type { SelectOption } from '../form-select/form-select.component';

@Component({
  selector: 'app-form-search-select',
  standalone: true,
  imports: [CommonModule, FormsModule, OverlayModule],
  host: {
    '[class.is-dropdown-open]': 'open()',
  },
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormSearchSelectComponent),
      multi: true,
    },
  ],
  template: `
    <div class="field" [class.has-error]="!!errorMessage" #root>
      <label *ngIf="label" [for]="id">
        {{ label }}
        <span *ngIf="required" class="required">*</span>
      </label>

      <div
        class="search-select"
        cdkOverlayOrigin
        #origin="cdkOverlayOrigin"
        #selectControl
        [class.is-open]="open()"
        [class.is-disabled]="disabled"
      >
        <div class="control-shell">
          <span class="search-icon material-icons" aria-hidden="true">search</span>
          <input
            [id]="id"
            type="text"
            dir="auto"
            class="search-input"
            role="combobox"
            autocomplete="off"
            [disabled]="disabled"
            [placeholder]="effectivePlaceholder()"
            [value]="inputText"
            [attr.aria-expanded]="open()"
            (input)="onInput($event)"
            (focus)="onFocus()"
            (keydown.escape)="closeDropdown()"
          />
          <button
            *ngIf="value != null && !disabled"
            type="button"
            class="clear-btn"
            [attr.aria-label]="clearLabel"
            (mousedown)="clearSelection($event)"
          >
            ✕
          </button>
          <span class="chevron material-icons" [class.is-open]="open()" aria-hidden="true">
            expand_more
          </span>
        </div>
      </div>

      <ng-template
        cdkConnectedOverlay
        [cdkConnectedOverlayOrigin]="origin"
        [cdkConnectedOverlayOpen]="open()"
        [cdkConnectedOverlayWidth]="panelWidth"
        [cdkConnectedOverlayPositions]="overlayPositions"
        [cdkConnectedOverlayPush]="true"
        [cdkConnectedOverlayViewportMargin]="8"
        [cdkConnectedOverlayHasBackdrop]="false"
        (overlayOutsideClick)="closeDropdown()"
        (detach)="onOverlayDetach()"
      >
        <ul class="dropdown dropdown--overlay" role="listbox">
          <li
            *ngFor="let option of filteredOptions"
            class="dropdown-option"
            role="option"
            [class.is-selected]="option.value === value"
            (mousedown)="selectOption(option, $event)"
          >
            <span dir="auto">{{ option.label }}</span>
            <span *ngIf="option.value === value" class="check material-icons" aria-hidden="true">
              check
            </span>
          </li>
          <li *ngIf="filteredOptions.length === 0" class="dropdown-empty">
            {{ noResultsLabel }}
          </li>
        </ul>
      </ng-template>

      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-search-select.component.scss',
})
export class FormSearchSelectComponent implements ControlValueAccessor {
  @ViewChild('selectControl') selectControlRef?: ElementRef<HTMLElement>;

  @Input() label = '';
  @Input() placeholder = 'Select an option';
  @Input() searchPlaceholder = '';
  @Input() noResultsLabel = 'No matches found';
  @Input() clearLabel = 'Clear';
  @Input() options: SelectOption[] = [];
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() id = `search-sel-${Math.random().toString(36).slice(2, 9)}`;

  value: SelectValue = null;
  open = signal(false);
  query = signal('');
  panelWidth = 0;

  readonly overlayPositions: ConnectedPosition[] = [
    {
      originX: 'start',
      originY: 'bottom',
      overlayX: 'start',
      overlayY: 'top',
      offsetY: 4,
    },
    {
      originX: 'start',
      originY: 'top',
      overlayX: 'start',
      overlayY: 'bottom',
      offsetY: -4,
    },
  ];

  get inputText(): string {
    if (this.open()) return this.query();
    return this.selectedLabel();
  }

  get filteredOptions(): SelectOption[] {
    const term = this.normalize(this.query());
    if (!term) return this.options;
    return this.options.filter((option) => this.normalize(option.label).includes(term));
  }

  onChange: (value: SelectValue) => void = () => {};
  onTouched: () => void = () => {};

  effectivePlaceholder(): string {
    if (this.open() || this.value == null) {
      return this.searchPlaceholder || this.placeholder;
    }
    return '';
  }

  onFocus(): void {
    if (this.disabled) return;
    this.openPanel();
    this.query.set(this.selectedLabel());
    this.onTouched();
  }

  onInput(event: Event): void {
    const next = (event.target as HTMLInputElement).value;
    this.query.set(next);
    this.openPanel();
  }

  selectOption(option: SelectOption, event: MouseEvent): void {
    event.preventDefault();
    if (option.disabled) return;
    this.setValue(option.value);
    this.closeDropdown();
  }

  clearSelection(event: MouseEvent): void {
    event.preventDefault();
    this.setValue(null);
    this.closeDropdown();
  }

  closeDropdown(): void {
    this.open.set(false);
    this.query.set('');
  }

  onOverlayDetach(): void {
    if (this.open()) this.closeDropdown();
  }

  writeValue(value: SelectValue): void {
    this.value = value ?? null;
  }

  registerOnChange(fn: (value: SelectValue) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  private openPanel(): void {
    this.panelWidth = this.selectControlRef?.nativeElement.getBoundingClientRect().width ?? 0;
    this.open.set(true);
  }

  private setValue(next: SelectValue): void {
    this.value = next;
    this.onChange(next);
  }

  private selectedLabel(): string {
    const match = this.options.find((option) => option.value === this.value);
    return match?.label ?? '';
  }

  private normalize(text: string): string {
    return text.trim().toLocaleLowerCase();
  }
}
