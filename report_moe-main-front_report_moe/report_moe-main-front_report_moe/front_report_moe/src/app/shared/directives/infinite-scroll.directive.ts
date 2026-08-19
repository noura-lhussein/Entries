import {
  AfterViewInit,
  Directive,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';

/**
 * Emits when the host element nears its scrollport (IntersectionObserver).
 * Place on a sentinel at the bottom of a scrollable list.
 *
 * For info pages the scroll owner is `main.content` — never a table-inner scroller.
 */
@Directive({
  selector: '[appInfiniteScroll]',
  standalone: true,
})
export class InfiniteScrollDirective implements AfterViewInit, OnChanges, OnDestroy {
  private readonly el = inject(ElementRef<HTMLElement>);

  /** When true, observer does not emit. */
  @Input() appInfiniteScrollDisabled = false;
  /** Root margin below the scrollport to prefetch early. */
  @Input() appInfiniteScrollRootMargin = '240px';
  /** CSS selector(s) for the scroll root; defaults to main.content. */
  @Input() appInfiniteScrollRoot = 'main.content';

  @Output() appInfiniteScroll = new EventEmitter<void>();

  private observer: IntersectionObserver | null = null;
  /** Blocks repeat emits until the sentinel leaves the intersection (or disabled clears). */
  private armed = true;

  ngAfterViewInit(): void {
    this.setup();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (
      changes['appInfiniteScrollRootMargin'] ||
      changes['appInfiniteScrollRoot'] ||
      (changes['appInfiniteScrollDisabled'] && !changes['appInfiniteScrollDisabled'].firstChange)
    ) {
      if (changes['appInfiniteScrollDisabled'] && !this.appInfiniteScrollDisabled) {
        // Finished a load cycle — allow one more emit if still visible (fill viewport).
        this.armed = true;
      }
      this.setup();
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    this.observer = null;
  }

  private setup(): void {
    if (typeof IntersectionObserver === 'undefined') return;
    this.observer?.disconnect();
    this.observer = null;

    const root = this.resolveScrollRoot();
    this.observer = new IntersectionObserver(
      (entries) => {
        const entry = entries.find((e) => e.target === this.el.nativeElement) ?? entries[0];
        if (!entry) return;

        if (!entry.isIntersecting) {
          this.armed = true;
          return;
        }

        if (this.appInfiniteScrollDisabled || !this.armed) return;

        this.armed = false;
        this.appInfiniteScroll.emit();
      },
      {
        root,
        rootMargin: this.appInfiniteScrollRootMargin,
        threshold: 0,
      },
    );

    if (!this.appInfiniteScrollDisabled) {
      this.observer.observe(this.el.nativeElement);
    }
  }

  private resolveScrollRoot(): Element | null {
    const host = this.el.nativeElement;

    if (this.appInfiniteScrollRoot) {
      for (const selector of this.appInfiniteScrollRoot
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)) {
        const explicit = host.closest(selector);
        if (explicit instanceof Element && !this.isTableInnerScroller(explicit)) {
          return explicit;
        }
      }
    }

    const content = host.closest('main.content, .content');
    if (content instanceof Element && !this.isTableInnerScroller(content)) {
      return content;
    }

    let node: HTMLElement | null = host.parentElement;
    while (node && node !== document.body) {
      if (this.isScrollContainer(node) && !this.isTableInnerScroller(node)) {
        return node;
      }
      node = node.parentElement;
    }

    return null;
  }

  /** Table body scroll layers must never drive infinite-scroll. */
  private isTableInnerScroller(el: Element): boolean {
    if (el.classList.contains('table-scroll') || el.classList.contains('table-wrapper')) {
      return true;
    }
    // Only treat as table-inner when the element itself is inside a table scroller,
    // not when a page root merely contains a table as a descendant.
    return false;
  }

  private isScrollContainer(el: HTMLElement): boolean {
    if (this.isTableInnerScroller(el)) return false;
    const style = getComputedStyle(el);
    const oy = style.overflowY;
    if (oy !== 'auto' && oy !== 'scroll' && oy !== 'overlay') return false;
    return el.scrollHeight > el.clientHeight + 1 || el.clientHeight > 0;
  }
}
