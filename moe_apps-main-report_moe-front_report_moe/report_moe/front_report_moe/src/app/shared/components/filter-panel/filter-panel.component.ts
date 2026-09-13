import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { TranslationService } from '../../services/translation.service';
import { isEmptyFilterValue, parseFilterIds, serializeFilterIds } from '../../utils/filter-params';
import { soleOptionValue } from '../../utils/sole-option';
import {
  FormSelectComponent,
  type SelectOption,
  type SelectValue,
} from '../form-select/form-select.component';
import { ModalComponent } from '../modal/modal.component';

/** Soft cap — searchable listbox handles long lists; hint shown past this. */
const MAX_FILTER_SELECT_OPTIONS = 500;

const FILTER_DIALOG_BODY_CLASS = 'filter-dialog-open';

export interface FilterGroup {
  label: string;
  key: string;
  type: 'select' | 'date' | 'checkbox';
  options?: { value: string; label: string }[];
}

export interface FilterChip {
  key: string;
  label: string;
  valueLabel: string;
}

@Component({
  selector: 'app-filter-panel',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, MatIconModule, FormSelectComponent, ModalComponent],
  template: `
    <div class="filters-section">
      @if (searchPlaceholder) {
        <div class="search-box">
          <mat-icon>search</mat-icon>
          <input
            type="text"
            [placeholder]="searchPlaceholder"
            (input)="onSearch($event)"
            class="search-input"
          />
        </div>
      }
      <button
        type="button"
        class="filter-btn"
        (click)="toggleFilters()"
        [class.active]="showFilters() || activeChipCount > 0"
        [title]="t('filter.toggle')"
      >
        <mat-icon>tune</mat-icon>
        <span>{{ t('filter.toggle') }}</span>
        @if (activeChipCount > 0) {
          <span class="filter-btn-count">{{ activeChipCount }}</span>
        }
      </button>

      @if (activeChips.length) {
        <div class="filter-chips" role="list">
          @for (chip of activeChips; track chip.key) {
            <span class="filter-chip" role="listitem">
              <span class="filter-chip-text">
                <span class="filter-chip-label">{{ chip.label }}:</span>
                {{ chip.valueLabel }}
              </span>
              <button
                type="button"
                class="filter-chip-remove"
                (click)="onClearFilter(chip.key)"
                [attr.aria-label]="t('filter.clear')"
                [title]="t('filter.clear')"
              >
                <mat-icon>close</mat-icon>
              </button>
            </span>
          }
        </div>
      }
    </div>

    <app-modal
      [title]="t('filter.title')"
      [visible]="showFilters()"
      size="large"
      (close)="closeFilters()"
    >
      <div class="filters-grid">
        @for (filter of filterGroups; track filter.key) {
          <div class="filter-group" [class.filter-group--active]="isFilterActive(filter.key)">
            @if (filter.type !== 'checkbox') {
              <label [class.has-selection]="isFilterActive(filter.key)">{{ filter.label }}</label>
            }
            <div class="filter-input-wrapper">
              @if (filter.type === 'select') {
                <app-form-select
                  class="filter-form-select"
                  [label]="''"
                  [placeholder]="t('filter.all')"
                  [searchPlaceholder]="t('filter.search-placeholder')"
                  [noResultsLabel]="t('filter.no-results')"
                  [clearLabel]="t('filter.clear')"
                  [options]="selectOptions(filter)"
                  [clearable]="true"
                  [searchThreshold]="10"
                  [ngModel]="selectModelValue(filter.key)"
                  (ngModelChange)="onSelectModelChange(filter.key, $event)"
                />
                @if (isOptionsTruncated(filter)) {
                  <p class="options-truncated-hint">{{ t('filter.options-truncated') }}</p>
                }
              }
              @if (filter.type === 'date') {
                <input
                  type="date"
                  class="filter-date"
                  [ngModel]="getFilterValue(filter.key)"
                  (ngModelChange)="onSelectChange(filter.key, $event)"
                  [class.has-value]="isFilterActive(filter.key)"
                  [class.is-placeholder]="!isFilterActive(filter.key)"
                />
                @if (isFilterActive(filter.key)) {
                  <button
                    type="button"
                    class="clear-field-btn"
                    (click)="onClearFilter(filter.key)"
                    [title]="t('filter.clear')"
                  >
                    <mat-icon>close</mat-icon>
                  </button>
                }
              }
            </div>
            @if (filter.type === 'checkbox') {
              <div class="checkbox-wrapper">
                <input
                  type="checkbox"
                  [id]="filter.key"
                  [checked]="isCheckboxChecked(filter.key)"
                  (change)="onFilterChange(filter.key, $event)"
                  class="checkbox"
                />
                <label [for]="filter.key" class="checkbox-label">{{ filter.label }}</label>
              </div>
            }
          </div>
        }
      </div>
      <div footer class="filters-actions">
        <button type="button" class="btn-clear" (click)="onClearFilters()">
          {{ t('filter.clear-all') }}
        </button>
      </div>
    </app-modal>
  `,
  styleUrl: './filter-panel.component.scss',
})
export class FilterPanelComponent implements OnChanges, OnDestroy {
  private translation = inject(TranslationService);
  private cdr = inject(ChangeDetectorRef);
  t = (key: string) => this.translation.t(key);

  @Input() searchPlaceholder = '';
  @Input() filterGroups: FilterGroup[] = [];
  @Input() activeFilters: Record<string, any> = {};
  @Output() search = new EventEmitter<string>();
  @Output() filterChange = new EventEmitter<{ key: string; value: any }>();
  @Output() clearFilters = new EventEmitter<void>();
  @Output() clearFilter = new EventEmitter<string>();
  /** Emitted when the filter panel is opened (lazy-load dependent options in parent). */
  @Output() panelOpened = new EventEmitter<void>();

  showFilters = signal(false);
  private lastGroupsSignature = '';
  private lastFiltersSignature = '';

  get activeChips(): FilterChip[] {
    return this.filterGroups
      .filter((g) => this.isFilterActive(g.key))
      .map((g) => ({
        key: g.key,
        label: g.label,
        valueLabel: this.resolveValueLabel(g),
      }));
  }

  get activeChipCount(): number {
    return this.activeChips.length;
  }

  ngOnChanges(changes: SimpleChanges): void {
    const groupsSig = this.groupsSignature(this.filterGroups);
    const filtersSig = this.filtersSignature(this.activeFilters);
    const groupsChanged = !!changes['filterGroups'] && groupsSig !== this.lastGroupsSignature;
    const filtersChanged = !!changes['activeFilters'] && filtersSig !== this.lastFiltersSignature;
    if (groupsChanged) this.lastGroupsSignature = groupsSig;
    if (filtersChanged) this.lastFiltersSignature = filtersSig;
    if (groupsChanged || filtersChanged) {
      this.cdr.markForCheck();
      // Defer so parent bindings settle before we emit cascade defaults.
      queueMicrotask(() => this.applySingleOptionDefaults());
    }
  }

  /** When a select filter has exactly one option, pick it so cascaded UIs unlock. */
  private applySingleOptionDefaults(): void {
    for (const group of this.filterGroups) {
      if (group.type !== 'select') continue;
      const only = soleOptionValue(this.rawSelectOptions(group));
      if (only == null) continue;
      if (this.sameAsActive(group.key, only)) continue;
      this.filterChange.emit({ key: group.key, value: only });
    }
  }

  ngOnDestroy(): void {
    this.setFilterDialogBodyClass(false);
  }

  toggleFilters(): void {
    if (this.showFilters()) {
      this.closeFilters();
      return;
    }
    this.openFilters();
  }

  openFilters(): void {
    this.showFilters.set(true);
    this.setFilterDialogBodyClass(true);
    this.panelOpened.emit();
    this.cdr.markForCheck();
  }

  closeFilters(): void {
    if (!this.showFilters()) return;
    this.showFilters.set(false);
    this.setFilterDialogBodyClass(false);
    this.cdr.markForCheck();
  }

  private setFilterDialogBodyClass(open: boolean): void {
    if (typeof document === 'undefined') return;
    document.body.classList.toggle(FILTER_DIALOG_BODY_CLASS, open);
  }

  onSearch(event: Event): void {
    this.search.emit((event.target as HTMLInputElement).value);
  }

  selectModelValue(key: string): SelectValue {
    const val = this.getFilterValue(key);
    return val === '' ? null : val;
  }

  onSelectModelChange(key: string, value: SelectValue): void {
    this.onSelectChange(key, value == null ? '' : String(value));
  }

  onSelectChange(key: string, value: string): void {
    if (this.sameAsActive(key, value)) return;
    this.filterChange.emit({ key, value: value ?? '' });
  }

  onFilterChange(key: string, event: Event): void {
    const target = event.target as HTMLInputElement;
    const value = target.type === 'checkbox' ? target.checked : target.value;
    this.filterChange.emit({ key, value });
  }

  onClearFilter(key: string): void {
    this.clearFilter.emit(key);
  }

  onClearFilters(): void {
    this.clearFilters.emit();
  }

  isFilterActive(key: string): boolean {
    return !isEmptyFilterValue(this.activeFilters[key]);
  }

  isCheckboxChecked(key: string): boolean {
    const v = this.activeFilters[key];
    return v === true || v === 'true' || v === 1 || v === '1';
  }

  getFilterValue(key: string): string {
    return parseFilterIds(this.activeFilters[key])[0] ?? '';
  }

  selectOptions(filter: FilterGroup): SelectOption[] {
    return this.rawSelectOptions(filter).slice(0, MAX_FILTER_SELECT_OPTIONS);
  }

  isOptionsTruncated(filter: FilterGroup): boolean {
    return this.rawSelectOptions(filter).length > MAX_FILTER_SELECT_OPTIONS;
  }

  private resolveValueLabel(filter: FilterGroup): string {
    const raw = this.activeFilters[filter.key];
    if (filter.type === 'checkbox') {
      return this.isCheckboxChecked(filter.key) ? this.t('filter.yes') : this.t('filter.no');
    }
    if (filter.type === 'date') {
      return String(raw ?? '');
    }
    const ids = parseFilterIds(raw);
    if (!ids.length) return String(raw ?? '');
    const options = filter.options ?? [];
    const labels = ids.map((id) => {
      const match = options.find((o) => String(o.value) === String(id));
      return match?.label || id;
    });
    return labels.join(', ');
  }

  private rawSelectOptions(filter: FilterGroup): SelectOption[] {
    return (filter.options ?? [])
      .filter((o) => o.value !== '' && o.value != null)
      .map((o) => ({ value: o.value, label: o.label }));
  }

  private sameAsActive(key: string, value: unknown): boolean {
    const prev = serializeFilterIds(parseFilterIds(this.activeFilters[key]));
    const next = serializeFilterIds(parseFilterIds(value));
    return prev === next;
  }

  private groupsSignature(groups: FilterGroup[]): string {
    return groups
      .map(
        (g) =>
          `${g.key}|${g.type}|${(g.options ?? []).map((o) => `${o.value}:${o.label}`).join(',')}`,
      )
      .join(';;');
  }

  private filtersSignature(filters: Record<string, unknown>): string {
    return Object.keys(filters)
      .sort()
      .map((k) => `${k}=${serializeFilterIds(parseFilterIds(filters[k]))}`)
      .join('|');
  }
}
