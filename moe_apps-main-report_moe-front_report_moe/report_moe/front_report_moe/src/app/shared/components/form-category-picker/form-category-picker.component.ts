import { OverlayModule, type ConnectedPosition } from '@angular/cdk/overlay';
import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  Input,
  ViewChild,
  forwardRef,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';
import type { CategorySelectOption } from '../../../features/project-budget/project-budget.models';
import {
  buildCategoryTree,
  categoryDisplayLabel,
  filterCategoryTree,
  findCategoryById,
  flattenCategoryTree,
  groupCategorySections,
  type CategorySection,
  type CategoryTreeNode,
  type CategoryTreeRow,
} from '../../../features/project-budget/category-tree.utils';
import { TranslationService } from '../../services/translation.service';
import type { SelectValue } from '../form-select/form-select.component';

@Component({
  selector: 'app-form-category-picker',
  standalone: true,
  imports: [CommonModule, FormsModule, OverlayModule],
  host: {
    '[class.is-dropdown-open]': 'open()',
  },
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => FormCategoryPickerComponent),
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
        class="category-picker"
        cdkOverlayOrigin
        #origin="cdkOverlayOrigin"
        #selectControl
        [class.is-open]="open()"
        [class.is-disabled]="isDisabled"
      >
        <div class="control-shell">
          <input
            [id]="id"
            type="text"
            dir="auto"
            class="trigger-input"
            role="combobox"
            autocomplete="off"
            readonly
            [disabled]="isDisabled"
            [placeholder]="effectivePlaceholder()"
            [value]="selectedLabel"
            [attr.aria-expanded]="open()"
            (click)="openDropdown()"
            (focus)="openDropdown()"
            (keydown.escape)="closeDropdown()"
          />
          <button
            *ngIf="value != null && !isDisabled"
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
        <div class="dropdown-panel dropdown-panel--overlay" role="listbox">
          <div class="dropdown-search">
            <span class="search-icon material-icons" aria-hidden="true">search</span>
            <input
              type="text"
              dir="auto"
              class="search-input"
              autocomplete="off"
              [placeholder]="searchPlaceholder"
              [value]="query()"
              (input)="onSearchInput($event)"
              (keydown.escape)="closeDropdown()"
            />
          </div>

          <div class="dropdown-body">
            <div *ngIf="emptyHint && !categories.length" class="dropdown-empty">
              {{ emptyHint }}
            </div>

            <ng-container *ngIf="categories.length">
              <div *ngIf="sections.length === 0" class="dropdown-empty">{{ noResultsLabel }}</div>

              <div *ngFor="let section of sections" class="category-section">
                <div class="section-head">
                  <span *ngIf="section.prefix !== 'other'" class="section-code">{{
                    section.prefix
                  }}</span>
                  <span class="section-title">{{ t(section.labelKey) }}</span>
                </div>
                <button
                  *ngFor="let row of sectionRows(section)"
                  type="button"
                  class="category-row"
                  role="option"
                  [class.is-selected]="row.node.id === value"
                  [style.padding-inline-start.px]="12 + row.depth * 20"
                  (mousedown)="selectCategory(row.node, $event)"
                >
                  <span *ngIf="row.node.code" class="row-code">{{ row.node.code }}</span>
                  <span class="row-name">{{ row.node.name }}</span>
                </button>
              </div>
            </ng-container>
          </div>
        </div>
      </ng-template>

      <small *ngIf="hint && !errorMessage" class="hint">{{ hint }}</small>
      <small *ngIf="errorMessage" class="error">{{ errorMessage }}</small>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-category-picker.component.scss',
})
export class FormCategoryPickerComponent implements ControlValueAccessor {
  private translation = inject(TranslationService);

  @ViewChild('selectControl') selectControlRef?: ElementRef<HTMLElement>;

  @Input() label = '';
  @Input() placeholder = 'Select an option';
  @Input() searchPlaceholder = 'Search...';
  @Input() noResultsLabel = 'No matches found';
  @Input() emptyHint = '';
  @Input() clearLabel = 'Clear';
  @Input() categories: CategorySelectOption[] = [];
  @Input() disabled = false;
  @Input() required = false;
  @Input() errorMessage = '';
  @Input() hint = '';
  @Input() id = `cat-pick-${Math.random().toString(36).slice(2, 9)}`;

  value: SelectValue = null;
  open = signal(false);
  query = signal('');
  controlDisabled = false;
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

  t = (key: string) => this.translation.t(key);

  get isDisabled(): boolean {
    return this.disabled || this.controlDisabled;
  }

  get selectedLabel(): string {
    const item = findCategoryById(this.categories, this.value != null ? Number(this.value) : null);
    return item ? categoryDisplayLabel(item) : '';
  }

  get categoryTree(): CategoryTreeNode[] {
    return buildCategoryTree(this.categories);
  }

  get visibleTree(): CategoryTreeNode[] {
    return filterCategoryTree(this.categoryTree, this.query());
  }

  get sections(): CategorySection[] {
    return groupCategorySections(this.visibleTree);
  }

  effectivePlaceholder(): string {
    if (this.value != null) return '';
    return this.emptyHint || this.placeholder;
  }

  sectionRows(section: CategorySection): CategoryTreeRow[] {
    return flattenCategoryTree(section.roots);
  }

  openDropdown(): void {
    if (this.isDisabled) return;
    this.panelWidth = this.selectControlRef?.nativeElement.getBoundingClientRect().width ?? 0;
    this.open.set(true);
    this.query.set('');
    this.onTouched();
  }

  onSearchInput(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
  }

  selectCategory(node: CategoryTreeNode, event: MouseEvent): void {
    event.preventDefault();
    this.setValue(node.id);
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
    this.controlDisabled = isDisabled;
  }

  private setValue(next: SelectValue): void {
    this.value = next;
    this.onChange(next);
  }
}
