import { signal, computed } from '@angular/core';
import { isEmptyFilterValue, serializeFilterIds, parseFilterIds } from './filter-params';
import { debugLog } from './debug-log';

/** A single filter value — primitive or a list of ids. */
export type FilterValue = string | number | boolean | null | Array<string | number>;

/** Outgoing query params for a list/API call. */
export type ApiQueryParams = Record<string, string | number | boolean>;

/**
 * Unified filter/pagination state — instantiate once per list component.
 *
 * @param reload   callback that triggers the API call (e.g. () => this.load())
 * @param searchKey query-param name to use for the search string ('search' by default).
 *                  Pass '' to disable search (search box still works but nothing is sent).
 */
export class FilterState {
  readonly currentPage = signal(1);
  readonly pageSize = signal(10);
  readonly totalCount = signal(0);
  readonly totalPages = computed(() => Math.ceil(this.totalCount() / this.pageSize()));
  readonly hasMore = computed(
    () => this.currentPage() * this.pageSize() < this.totalCount(),
  );
  readonly loading = signal(false);
  readonly loadingMore = signal(false);
  readonly filters = signal<Record<string, FilterValue>>({});
  readonly searchQuery = signal('');

  constructor(
    private readonly reload: () => void,
    private readonly searchKey = 'search',
    initialPageSize = 10,
  ) {
    if (initialPageSize > 0) {
      this.pageSize.set(initialPageSize);
    }
  }

  /** Ready-to-use params object — spread directly into the API call. */
  get params(): ApiQueryParams {
    const base: ApiQueryParams = {
      page: this.currentPage(),
      page_size: this.pageSize(),
    };
    const q = this.searchQuery();
    if (q && this.searchKey) base[this.searchKey] = q;
    for (const [key, value] of Object.entries(this.filters())) {
      if (isEmptyFilterValue(value)) continue;
      base[key] = Array.isArray(value) ? serializeFilterIds(value.map(String)) : value!;
    }
    return base;
  }

  onSearch(query: string): void {
    this.searchQuery.set(query);
    this.resetToFirstPage();
    this.reload();
  }

  private resetToFirstPage(): void {
    this.currentPage.set(1);
    this.loadingMore.set(false);
  }

  onFilterChange(filter: { key: string; value: FilterValue }): void {
    debugLog(
      'filter-state.ts:onFilterChange',
      'reload scheduled',
      { key: filter.key, valueType: Array.isArray(filter.value) ? 'array' : typeof filter.value },
      'H3',
    );
    this.filters.update((f) => {
      const next = { ...f };
      if (isEmptyFilterValue(filter.value)) {
        delete next[filter.key];
      } else if (Array.isArray(filter.value)) {
        const ids = parseFilterIds(filter.value);
        if (ids.length) next[filter.key] = serializeFilterIds(ids);
        else delete next[filter.key];
      } else {
        next[filter.key] = filter.value;
      }
      return next;
    });
    this.resetToFirstPage();
    this.reload();
  }

  clearFilter(key: string): void {
    this.filters.update((f) => {
      const next = { ...f };
      delete next[key];
      return next;
    });
    this.resetToFirstPage();
    this.reload();
  }

  clearFilters(): void {
    this.filters.set({});
    this.searchQuery.set('');
    this.resetToFirstPage();
    this.reload();
  }

  previousPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update((p) => p - 1);
      this.reload();
    }
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update((p) => p + 1);
      this.reload();
    }
  }

  /** Append next page (infinite scroll). No-op if already loading or no more rows. */
  loadMore(): void {
    if (this.loading() || this.loadingMore() || !this.hasMore()) return;
    this.loadingMore.set(true);
    this.currentPage.update((p) => p + 1);
    this.reload();
  }

  goToPage(page: number): void {
    const target = Math.trunc(page);
    if (!Number.isFinite(target)) return;
    const clamped = Math.min(Math.max(target, 1), Math.max(this.totalPages(), 1));
    if (clamped === this.currentPage()) return;
    this.currentPage.set(clamped);
    this.reload();
  }

  setTotal(count: number): void {
    this.totalCount.set(count);
  }
}
