import { OverlayModule, type ConnectedPosition } from '@angular/cdk/overlay';
import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';

export type SelectValue = string | number | boolean | null;

export interface SelectOption {
  value: SelectValue;
  label: string;
  disabled?: boolean;
}

/** Options at or above this count show an in-panel search field. */
const DEFAULT_SEARCH_THRESHOLD = 10;

@Component({
  selector: 'app-form-select',
  standalone: true,
  imports: [CommonModule, FormsModule, OverlayModule],
  host: {
    '[class.is-dropdown-open]': 'open()',
  },
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormSelectComponent),
      multi: true,
    },
  ],
  template: `
    <div class="field" [class.has-error]="!!errorMessage" #root>
      <label *ngIf="label" [for]="id">
        {{ label }}
        <span *ngIf="required" class="required">*</span>
      </label>

      <div class="select-row">
        <div
          class="select-control"
          cdkOverlayOrigin
          #origin="cdkOverlayOrigin"
          #selectControl
          [class.is-open]="open()"
          [class.is-disabled]="disabled"
          [class.is-placeholder]="value == null"
        >
          <button
            [id]="id"
            type="button"
            class="trigger"
            role="combobox"
            [attr.aria-expanded]="open()"
            [attr.aria-controls]="listboxId"
            [attr.aria-activedescendant]="activeOptionId()"
            [disabled]="disabled"
            (click)="toggleDropdown()"
            (keydown)="onTriggerKeydown($event)"
          >
            <span class="trigger-label" dir="auto">{{ displayLabel() }}</span>
          </button>

          <div class="select-affixes">
            <button
              *ngIf="clearable && value != null && !disabled"
              type="button"
              class="clear-btn"
              [attr.aria-label]="clearLabel"
              (mousedown)="clearSelection($event)"
            >
              ✕
            </button>
            <span class="chevron material-icons" [class.is-open]="open()" aria-hidden="true"
              >expand_more</span
            >
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
          <div class="dropdown dropdown--overlay" role="presentation">
            <div *ngIf="showSearch" class="dropdown-search">
              <span class="search-icon material-icons" aria-hidden="true">search</span>
              <input
                #searchInput
                type="text"
                dir="auto"
                class="search-input"
                role="searchbox"
                autocomplete="off"
                [placeholder]="searchPlaceholder"
                [value]="query()"
                (input)="onSearchInput($event)"
                (keydown)="onListKeydown($event)"
                (keydown.escape)="closeDropdown()"
              />
            </div>

            <ul [id]="listboxId" class="dropdown-list" role="listbox">
              <li *ngIf="visibleOptions.length === 0" class="dropdown-empty" role="presentation">
                {{ noResultsLabel }}
              </li>
              <li
                *ngFor="let option of visibleOptions; let i = index; trackBy: trackByValue"
                [id]="optionDomId(i)"
                role="option"
                class="dropdown-option"
                [class.is-selected]="option.value === value"
                [class.is-active]="i === activeIndex()"
                [class.is-disabled]="!!option.disabled"
                [attr.aria-selected]="option.value === value"
                [attr.aria-disabled]="option.disabled || null"
                (mousedown)="selectOption(option, $event)"
                (mouseenter)="activeIndex.set(i)"
              >
                <span class="option-label" dir="auto">{{ option.label }}</span>
                <span
                  *ngIf="option.value === value"
                  class="check material-icons"
                  aria-hidden="true"
                >
                  check
                </span>
              </li>
            </ul>
          </div>
        </ng-template>

        <button
          *ngIf="addable"
          type="button"
          class="add-btn"
          (click)="addClicked.emit()"
          aria-label="Add"
        >
          +
        </button>
      </div>

      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  styleUrl: './form-select.component.scss',
})
export class FormSelectComponent implements ControlValueAccessor {
  @ViewChild('selectControl') selectControlRef?: ElementRef<HTMLElement>;
  @ViewChild('searchInput') searchInputRef?: ElementRef<HTMLInputElement>;

  @Input() label = '';
  @Input() placeholder = 'Select an option';
  @Input() searchPlaceholder = 'Search...';
  @Input() noResultsLabel = 'No matches found';
  @Input() clearLabel = 'Clear';
  @Input() options: SelectOption[] = [];
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() addable = false;
  /** Show clear button when a value is selected. */
  @Input() clearable = true;
  /** Show in-panel search when option count >= this value. Set 0 to always search. */
  @Input() searchThreshold = DEFAULT_SEARCH_THRESHOLD;
  @Input() id = `sel-${Math.random().toString(36).slice(2, 9)}`;

  @Output() addClicked = new EventEmitter<void>();

  value: SelectValue = null;
  open = signal(false);
  query = signal('');
  activeIndex = signal(-1);
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

  onChange: (value: SelectValue) => void = () => {};
  onTouched: () => void = () => {};

  get listboxId(): string {
    return `${this.id}-listbox`;
  }

  get showSearch(): boolean {
    return this.options.length >= this.searchThreshold;
  }

  get visibleOptions(): SelectOption[] {
    const term = this.normalize(this.query());
    if (!term) return this.options;
    return this.options.filter((option) => this.normalize(option.label).includes(term));
  }

  displayLabel(): string {
    if (this.value == null) return this.placeholder;
    return this.selectedLabel() || this.placeholder;
  }

  trackByValue(_index: number, option: SelectOption): SelectValue {
    return option.value;
  }

  optionDomId(index: number): string {
    return `${this.listboxId}-opt-${index}`;
  }

  activeOptionId(): string | null {
    const i = this.activeIndex();
    if (!this.open() || i < 0) return null;
    return this.optionDomId(i);
  }

  toggleDropdown(): void {
    if (this.disabled) return;
    if (this.open()) {
      this.closeDropdown();
      return;
    }
    this.openDropdown();
  }

  openDropdown(): void {
    if (this.disabled) return;
    this.panelWidth = this.selectControlRef?.nativeElement.getBoundingClientRect().width ?? 0;
    this.open.set(true);
    this.query.set('');
    this.activeIndex.set(this.indexOfValue(this.value));
    this.onTouched();
    if (this.showSearch) {
      queueMicrotask(() => this.searchInputRef?.nativeElement.focus());
    }
  }

  closeDropdown(): void {
    this.open.set(false);
    this.query.set('');
    this.activeIndex.set(-1);
  }

  onOverlayDetach(): void {
    if (this.open()) this.closeDropdown();
  }

  onSearchInput(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
    this.activeIndex.set(this.visibleOptions.length ? 0 : -1);
  }

  selectOption(option: SelectOption, event: MouseEvent): void {
    event.preventDefault();
    if (option.disabled) return;
    this.setValue(option.value);
    this.closeDropdown();
  }

  clearSelection(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.setValue(null);
    this.closeDropdown();
  }

  onTriggerKeydown(event: KeyboardEvent): void {
    if (this.disabled) return;

    switch (event.key) {
      case 'ArrowDown':
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (!this.open()) {
          this.openDropdown();
        } else if (event.key === 'Enter' || event.key === ' ') {
          this.commitActive();
        } else {
          this.moveActive(1);
        }
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (!this.open()) {
          this.openDropdown();
        } else {
          this.moveActive(-1);
        }
        break;
      case 'Escape':
        if (this.open()) {
          event.preventDefault();
          this.closeDropdown();
        }
        break;
      case 'Home':
        if (this.open()) {
          event.preventDefault();
          this.activeIndex.set(this.firstEnabledIndex());
        }
        break;
      case 'End':
        if (this.open()) {
          event.preventDefault();
          this.activeIndex.set(this.lastEnabledIndex());
        }
        break;
      default:
        break;
    }
  }

  onListKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.moveActive(1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.moveActive(-1);
        break;
      case 'Enter':
        event.preventDefault();
        this.commitActive();
        break;
      case 'Home':
        event.preventDefault();
        this.activeIndex.set(this.firstEnabledIndex());
        break;
      case 'End':
        event.preventDefault();
        this.activeIndex.set(this.lastEnabledIndex());
        break;
      default:
        break;
    }
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

  private indexOfValue(value: SelectValue): number {
    if (value == null) return this.firstEnabledIndex();
    const idx = this.visibleOptions.findIndex((o) => o.value === value && !o.disabled);
    return idx >= 0 ? idx : this.firstEnabledIndex();
  }

  private firstEnabledIndex(): number {
    return this.visibleOptions.findIndex((o) => !o.disabled);
  }

  private lastEnabledIndex(): number {
    for (let i = this.visibleOptions.length - 1; i >= 0; i--) {
      if (!this.visibleOptions[i].disabled) return i;
    }
    return -1;
  }

  private moveActive(delta: number): void {
    const opts = this.visibleOptions;
    if (!opts.length) {
      this.activeIndex.set(-1);
      return;
    }
    let i = this.activeIndex();
    if (i < 0) {
      this.activeIndex.set(delta > 0 ? this.firstEnabledIndex() : this.lastEnabledIndex());
      return;
    }
    for (let step = 0; step < opts.length; step++) {
      i = (i + delta + opts.length) % opts.length;
      if (!opts[i].disabled) {
        this.activeIndex.set(i);
        return;
      }
    }
  }

  private commitActive(): void {
    const i = this.activeIndex();
    const option = i >= 0 ? this.visibleOptions[i] : undefined;
    if (!option || option.disabled) return;
    this.setValue(option.value);
    this.closeDropdown();
  }
}
