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

/** Input events that count as the user driving a scroll. */
const INPUT_EVENTS = ['wheel', 'touchmove', 'keydown', 'pointerdown', 'pointerup', 'pointercancel'];

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
  /** One emit per load cycle, whichever trigger fires first. Cleared when a cycle ends. */
  private emittedForCycle = false;
  private scrollTarget: EventTarget | null = null;
  private inputTarget: EventTarget | null = null;
  private rootEl: Element | null = null;
  /** Set by a real input event, cleared on emit — one request per fresh gesture. */
  private userGestureSinceEmit = false;
  /** True between pointerdown and pointerup, i.e. while a scrollbar is dragged. */
  private pointerDragging = false;

  /**
   * Scroll-gesture trigger. The observer alone cannot drive these pages: rows
   * land inside app-tables capped at min(40vh, 22rem) with their own scrollbar,
   * so a new batch adds no page height and the sentinel never leaves the
   * prefetch zone — nothing re-arms it, and loading stalls.
   *
   * Registered in the capture phase because `scroll` does not bubble — that is
   * the only way to see the user scrolling *inside* one of those capped tables,
   * which on these pages is where the rows actually are.
   *
   * A `scroll` event on its own proves nothing about intent: the browser fires
   * plenty of its own during a load cycle (scroll anchoring compensating for
   * inserted rows, scrollTop being clamped as the DOM re-renders). Treating
   * those as gestures made loading cascade with the user's hands off entirely,
   * so an emit additionally requires an input event since the last one.
   */
  private readonly onScroll = (event: Event): void => {
    if (this.appInfiniteScrollDisabled || this.emittedForCycle) return;
    if (!this.userGestureSinceEmit && !this.pointerDragging) return;

    const scrolled = event.target instanceof Element ? event.target : null;
    if (scrolled && scrolled !== this.rootEl) {
      // An inner scroller (a capped table): load once it nears its own end.
      if (this.isNearEnd(scrolled)) this.emitLoad();
      return;
    }
    if (this.isSentinelInZone()) this.emitLoad();
  };

  private readonly onUserInput = (event: Event): void => {
    if (event.type === 'pointerdown') this.pointerDragging = true;
    else if (event.type === 'pointerup' || event.type === 'pointercancel') {
      this.pointerDragging = false;
    }
    this.userGestureSinceEmit = true;
  };

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
        // Load cycle finished — the next gesture may request another page.
        this.emittedForCycle = false;
      }
      if (
        changes['appInfiniteScrollDisabled'] &&
        !this.appInfiniteScrollDisabled &&
        !this.isScrollRootFilled()
      ) {
        // A load cycle just finished and the scrollport still has no scrollbar
        // (short list, tall screen) — allow one more automatic emit to keep
        // filling it. Once there's real scrollable content, do NOT force a
        // re-arm here: the observer's own `!isIntersecting` branch already
        // re-arms it the moment the sentinel is scrolled out of view, so the
        // next load only fires on an actual scroll gesture. Forcing `armed =
        // true` unconditionally on every load-cycle completion caused loads
        // to cascade back-to-back with no further scrolling, since a fresh
        // IntersectionObserver reports the sentinel's *current* (still
        // in-range) position immediately on `.observe()`.
        this.armed = true;
      }
      this.setup();
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    this.observer = null;
    this.detachScrollListener();
  }

  private setup(): void {
    this.detachScrollListener();
    if (typeof IntersectionObserver === 'undefined') return;
    this.observer?.disconnect();
    this.observer = null;

    const root = this.resolveScrollRoot();
    this.rootEl = root;
    this.observer = new IntersectionObserver(
      (entries) => {
        const entry = entries.find((e) => e.target === this.el.nativeElement) ?? entries[0];
        if (!entry) return;

        if (!entry.isIntersecting) {
          this.armed = true;
          return;
        }

        if (!this.armed) return;

        this.emitLoad();
      },
      {
        root,
        rootMargin: this.appInfiniteScrollRootMargin,
        threshold: 0,
      },
    );

    if (!this.appInfiniteScrollDisabled) {
      this.observer.observe(this.el.nativeElement);
      this.attachScrollListener(root);
    }
  }

  private emitLoad(): void {
    if (this.appInfiniteScrollDisabled || this.emittedForCycle) return;
    this.emittedForCycle = true;
    this.userGestureSinceEmit = false;
    this.armed = false;
    this.appInfiniteScroll.emit();
  }

  private attachScrollListener(root: Element | null): void {
    const target: EventTarget = root ?? document;
    target.addEventListener('scroll', this.onScroll, { passive: true, capture: true });
    this.scrollTarget = target;

    // On document, so a keyboard scroll counts wherever focus happens to be,
    // and a scrollbar drag (which fires no wheel or touch event) still counts.
    for (const type of INPUT_EVENTS) {
      document.addEventListener(type, this.onUserInput, { passive: true, capture: true });
    }
    this.inputTarget = document;
  }

  private detachScrollListener(): void {
    this.scrollTarget?.removeEventListener('scroll', this.onScroll, { capture: true });
    this.scrollTarget = null;

    for (const type of INPUT_EVENTS) {
      this.inputTarget?.removeEventListener(type, this.onUserInput, { capture: true });
    }
    this.inputTarget = null;
  }

  /** True when a genuinely scrollable element is scrolled near its own bottom. */
  private isNearEnd(el: Element): boolean {
    if (el.scrollHeight <= el.clientHeight + 1) return false; // not vertically scrollable
    return el.scrollHeight - el.scrollTop - el.clientHeight <= this.rootMarginPx;
  }

  private get rootMarginPx(): number {
    return Number.parseInt(this.appInfiniteScrollRootMargin, 10) || 0;
  }

  /** Mirrors the observer's own test: is the sentinel within the prefetch zone? */
  private isSentinelInZone(): boolean {
    const root = this.resolveScrollRoot();
    const viewportBottom = root
      ? root.getBoundingClientRect().bottom
      : (globalThis.innerHeight ?? 0);
    return this.el.nativeElement.getBoundingClientRect().top <= viewportBottom + this.rootMarginPx;
  }

  /** True when the scrollport already has enough content to need a scrollbar. */
  private isScrollRootFilled(): boolean {
    const root = this.resolveScrollRoot();
    const el = root ?? document.documentElement;
    return el.scrollHeight > el.clientHeight + 1;
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
