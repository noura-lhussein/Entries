import { Component, EventEmitter, Input, Output, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

type PageItem = { type: 'page'; value: number } | { type: 'gap'; value: string };

@Component({
  selector: 'app-pagination',
  standalone: true,
  imports: [CommonModule],
  template: `
    <nav class="pagination" *ngIf="totalPages > 1" role="navigation" aria-label="pagination">
      <div class="pagination__summary" *ngIf="totalItems > 0">
        {{ rangeStart() }}–{{ rangeEnd() }}
        <span class="pagination__summary-of">/</span>
        {{ totalItems }}
      </div>

      <ul class="pagination__list">
        <li>
          <button
            type="button"
            class="pagination__btn pagination__btn--nav"
            [disabled]="currentPage === 1"
            (click)="onPrevious()"
            aria-label="previous page"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                d="M15 6l-6 6 6 6"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </li>

        <li *ngFor="let item of pages()">
          <span *ngIf="item.type === 'gap'" class="pagination__gap" aria-hidden="true">…</span>
          <button
            *ngIf="item.type === 'page'"
            type="button"
            class="pagination__btn"
            [class.is-active]="item.value === currentPage"
            [attr.aria-current]="item.value === currentPage ? 'page' : null"
            (click)="onSelect(item.value)"
          >
            {{ item.value }}
          </button>
        </li>

        <li>
          <button
            type="button"
            class="pagination__btn pagination__btn--nav"
            [disabled]="currentPage === totalPages"
            (click)="onNext()"
            aria-label="next page"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                d="M9 6l6 6-6 6"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </li>
      </ul>
    </nav>
  `,
  styleUrl: './pagination.component.scss',
})
export class PaginationComponent {
  private currentPageSig = signal(1);
  private totalPagesSig = signal(1);

  @Input() set currentPage(value: number) {
    this.currentPageSig.set(value || 1);
  }
  get currentPage(): number {
    return this.currentPageSig();
  }

  @Input() set totalPages(value: number) {
    this.totalPagesSig.set(value || 1);
  }
  get totalPages(): number {
    return this.totalPagesSig();
  }

  /** Optional: total record count for the "x–y / total" summary. */
  @Input() totalItems = 0;
  /** Optional: page size, used to compute the visible range. */
  @Input() pageSize = 0;

  @Output() previous = new EventEmitter<void>();
  @Output() next = new EventEmitter<void>();
  @Output() goToPage = new EventEmitter<number>();

  rangeStart = computed(() => {
    if (!this.pageSize) return 1;
    return (this.currentPageSig() - 1) * this.pageSize + 1;
  });

  rangeEnd = computed(() => {
    if (!this.pageSize) return this.totalItems;
    return Math.min(this.currentPageSig() * this.pageSize, this.totalItems);
  });

  /** Windowed page list with leading/trailing ellipsis (1 … 4 5 [6] 7 8 … 20). */
  pages = computed<PageItem[]>(() => {
    const total = this.totalPagesSig();
    const current = this.currentPageSig();
    const siblings = 1;

    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => ({ type: 'page', value: i + 1 }) as PageItem);
    }

    const items: PageItem[] = [];
    const left = Math.max(current - siblings, 1);
    const right = Math.min(current + siblings, total);
    const showLeftGap = left > 2;
    const showRightGap = right < total - 1;

    items.push({ type: 'page', value: 1 });
    if (showLeftGap) items.push({ type: 'gap', value: 'left' });

    const start = showLeftGap ? left : 2;
    const end = showRightGap ? right : total - 1;
    for (let page = start; page <= end; page++) {
      items.push({ type: 'page', value: page });
    }

    if (showRightGap) items.push({ type: 'gap', value: 'right' });
    items.push({ type: 'page', value: total });

    return items;
  });

  onPrevious(): void {
    if (this.currentPage > 1) {
      this.previous.emit();
      this.goToPage.emit(this.currentPage - 1);
    }
  }

  onNext(): void {
    if (this.currentPage < this.totalPages) {
      this.next.emit();
      this.goToPage.emit(this.currentPage + 1);
    }
  }

  onSelect(page: number): void {
    if (page !== this.currentPage) {
      this.goToPage.emit(page);
    }
  }
}
