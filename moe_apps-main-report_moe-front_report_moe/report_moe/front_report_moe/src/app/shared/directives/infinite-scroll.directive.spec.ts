import { Component } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';
import { beforeEach, afterEach, describe, expect, it } from 'vitest';
import { InfiniteScrollDirective } from './infinite-scroll.directive';

/**
 * IntersectionObserver double. Two real-browser semantics drive these tests and
 * are modelled exactly:
 *  1. `observe()` queues an *initial* observation reporting the target's current
 *     position — this is what a freshly-created observer re-fires on its own.
 *  2. Afterwards the callback runs only when the intersecting state *changes*;
 *     scrolling around while staying inside the zone fires nothing.
 */
class FakeIntersectionObserver implements IntersectionObserver {
  static instances: FakeIntersectionObserver[] = [];
  static pending: Array<() => void> = [];
  /** px from the sentinel to the bottom edge of the scrollport (may be negative). */
  static sentinelOffset = 0;

  static reset(): void {
    FakeIntersectionObserver.instances = [];
    FakeIntersectionObserver.pending = [];
    FakeIntersectionObserver.sentinelOffset = 0;
  }

  /** Deliver queued initial observations (the browser does this after layout). */
  static flush(): void {
    const queue = FakeIntersectionObserver.pending;
    FakeIntersectionObserver.pending = [];
    for (const fn of queue) fn();
  }

  static setOffset(offset: number): void {
    FakeIntersectionObserver.sentinelOffset = offset;
    for (const obs of FakeIntersectionObserver.instances) obs.reevaluate();
  }

  readonly root: Element | Document | null;
  readonly rootMargin: string;
  readonly thresholds: ReadonlyArray<number> = [0];

  private readonly targets = new Set<Element>();
  private readonly lastState = new Map<Element, boolean>();
  private dead = false;

  constructor(
    private readonly cb: IntersectionObserverCallback,
    options?: IntersectionObserverInit,
  ) {
    this.root = (options?.root as Element | null) ?? null;
    this.rootMargin = options?.rootMargin ?? '0px';
    FakeIntersectionObserver.instances.push(this);
  }

  observe(target: Element): void {
    this.targets.add(target);
    FakeIntersectionObserver.pending.push(() => {
      if (this.dead || !this.targets.has(target)) return;
      const state = this.isIntersecting();
      this.lastState.set(target, state);
      this.deliver(target, state);
    });
  }

  unobserve(target: Element): void {
    this.targets.delete(target);
  }

  disconnect(): void {
    this.dead = true;
    this.targets.clear();
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  reevaluate(): void {
    if (this.dead) return;
    for (const target of this.targets) {
      const state = this.isIntersecting();
      if (this.lastState.get(target) === state) continue;
      this.lastState.set(target, state);
      this.deliver(target, state);
    }
  }

  private get marginPx(): number {
    return Number.parseInt(this.rootMargin, 10) || 0;
  }

  private isIntersecting(): boolean {
    return FakeIntersectionObserver.sentinelOffset <= this.marginPx;
  }

  private deliver(target: Element, isIntersecting: boolean): void {
    this.cb(
      [
        {
          target,
          isIntersecting,
          intersectionRatio: isIntersecting ? 1 : 0,
        } as IntersectionObserverEntry,
      ],
      this,
    );
  }
}

/** Mirrors the sentinel block in title-grouped-tables.component.html. */
@Component({
  standalone: true,
  imports: [InfiniteScrollDirective],
  template: `
    <div class="page-body">
      <!-- an app-table capped at min(40vh, 22rem) with its own scrollbar -->
      <div class="table-scroll"></div>
      @if (hasMore || loadingMore) {
        <div
          class="infinite-scroll-sentinel"
          appInfiniteScrollRoot=".page-body"
          [appInfiniteScrollDisabled]="!hasMore || loadingMore"
          (appInfiniteScroll)="onLoadMore()"
        ></div>
      }
    </div>
  `,
})
class HostComponent {
  hasMore = true;
  loadingMore = false;
  loads = 0;

  onLoadMore(): void {
    this.loads++;
    this.loadingMore = true;
  }
}

describe('InfiniteScrollDirective', () => {
  const VIEWPORT = 800;
  const REAL_IO = globalThis.IntersectionObserver;

  const REAL_RECT = HTMLElement.prototype.getBoundingClientRect;

  let fixture: ComponentFixture<HostComponent>;
  let host: HostComponent;
  let root: HTMLElement;
  let innerTable: HTMLElement;
  /** Simulated scrollport: total content height and current scroll position. */
  let contentHeight = 0;
  let scrollTop = 0;

  /**
   * The sentinel is the last element in the scrollport, so its distance below
   * the visible area is content - (scrollTop + viewport). Negative means it is
   * already on screen.
   */
  function syncSentinel(): void {
    FakeIntersectionObserver.setOffset(contentHeight - (scrollTop + VIEWPORT));
  }

  function maxScrollTop(): number {
    return Math.max(0, contentHeight - VIEWPORT);
  }

  function scrollTo(position: number): void {
    const next = Math.min(Math.max(position, 0), maxScrollTop());
    const moved = next !== scrollTop;
    scrollTop = next;
    syncSentinel();
    // A browser only fires `scroll` when the position actually changed, and a
    // user-driven scroll is always preceded by the input event that caused it.
    if (moved) {
      root.dispatchEvent(new WheelEvent('wheel', { bubbles: true }));
      root.dispatchEvent(new Event('scroll'));
    }
  }

  /** The user spins the wheel inside a capped table, which has its own scrollbar. */
  function scrollInnerTableTo(position: number): void {
    innerTable.scrollTop = position;
    innerTable.dispatchEvent(new WheelEvent('wheel', { bubbles: true }));
    innerTable.dispatchEvent(new Event('scroll'));
  }

  /**
   * A scroll event with no user input behind it. Browsers emit these on their
   * own during a load cycle: scroll anchoring compensating for inserted rows,
   * scrollTop being clamped as the DOM re-renders, the loading hint appearing
   * and disappearing. They must never be mistaken for a scroll gesture.
   */
  function browserEmitsScroll(target: HTMLElement = root): void {
    target.dispatchEvent(new Event('scroll'));
  }

  function scrollToBottom(): void {
    scrollTo(maxScrollTop());
  }

  /** Initial page state before any user interaction. */
  function layout(content: number, position = 0): void {
    contentHeight = content;
    scrollTo(position);
    fixture.detectChanges();
    FakeIntersectionObserver.flush();
  }

  /**
   * Change detection as zone.js runs it at the end of the event turn that
   * emitted — this is what pushes `loadingMore = true` into the directive's
   * `disabled` input and tears the observer down for the duration of the load.
   */
  function angularReacts(): void {
    fixture.detectChanges();
    FakeIntersectionObserver.flush();
  }

  /**
   * One full load cycle, both halves of it: `disabled` goes true while the
   * request is in flight, then false when the rows land. `batchHeight = 0`
   * models the real "بياناتي" layout, where the new rows land inside an
   * app-table already capped at min(40vh, 22rem) with its own scrollbar — the
   * page itself does not grow by a single pixel. The scroll position is
   * untouched throughout, exactly as in a browser.
   */
  function serverResponds(batchHeight: number): void {
    angularReacts(); // loadingMore = true → disabled
    contentHeight += batchHeight;
    syncSentinel();
    host.loadingMore = false;
    angularReacts(); // rows rendered, disabled cleared → re-arm decision point
  }

  beforeEach(async () => {
    FakeIntersectionObserver.reset();
    globalThis.IntersectionObserver =
      FakeIntersectionObserver as unknown as typeof IntersectionObserver;
    contentHeight = 0;
    scrollTop = 0;

    await TestBed.configureTestingModule({ imports: [HostComponent] }).compileComponents();
    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();

    root = fixture.nativeElement.querySelector('.page-body') as HTMLElement;
    Object.defineProperty(root, 'scrollHeight', { get: () => contentHeight, configurable: true });
    Object.defineProperty(root, 'clientHeight', { get: () => VIEWPORT, configurable: true });

    // A table capped at 352px holding 4000px of rows behind its own scrollbar.
    innerTable = fixture.nativeElement.querySelector('.table-scroll') as HTMLElement;
    Object.defineProperty(innerTable, 'scrollHeight', { value: 4000, configurable: true });
    Object.defineProperty(innerTable, 'clientHeight', { value: 352, configurable: true });
    innerTable.scrollTop = 0;

    // jsdom has no layout, so lay the two elements out from the scroll model.
    HTMLElement.prototype.getBoundingClientRect = function (this: HTMLElement) {
      if (this.classList.contains('page-body')) {
        return { top: 0, bottom: VIEWPORT } as DOMRect;
      }
      if (this.classList.contains('infinite-scroll-sentinel')) {
        return { top: contentHeight - scrollTop, bottom: contentHeight - scrollTop } as DOMRect;
      }
      return { top: 0, bottom: 0 } as DOMRect;
    };
  });

  afterEach(() => {
    globalThis.IntersectionObserver = REAL_IO;
    HTMLElement.prototype.getBoundingClientRect = REAL_RECT;
    fixture.destroy();
  });

  it('stays idle until the user scrolls the sentinel into the prefetch zone', () => {
    layout(4000);
    expect(host.loads).toBe(0);

    scrollToBottom();
    expect(host.loads).toBe(1);
  });

  it('does not cascade when appended rows do not grow the page', () => {
    layout(4000);
    scrollToBottom();
    expect(host.loads).toBe(1);

    // Ten consecutive load cycles that add no page height. Without the
    // isScrollRootFilled() guard each one re-armed the directive and the fresh
    // observer immediately re-fired, loading page after page with the user's
    // finger off the wheel — the reported bug.
    for (let i = 0; i < 10; i++) {
      serverResponds(0);
    }

    expect(host.loads).toBe(1);
  });

  it('does not cascade when appended rows do grow the page', () => {
    layout(4000);
    scrollToBottom();
    expect(host.loads).toBe(1);

    serverResponds(2000);
    expect(host.loads).toBe(1);

    serverResponds(2000);
    expect(host.loads).toBe(1);
  });

  it('re-arms on a genuine scroll-away-and-back gesture', () => {
    layout(4000);
    scrollToBottom();
    expect(host.loads).toBe(1);
    serverResponds(0);

    scrollTo(maxScrollTop() - 400); // scroll up, past the 240px margin
    scrollToBottom(); // and back down
    expect(host.loads).toBe(2);
  });

  it('auto-fills an unscrollable viewport, then stops once a scrollbar exists', () => {
    layout(300); // 300px of content in an 800px viewport → nothing to scroll
    expect(host.loads).toBe(1);

    serverResponds(300); // 600px, still short of the viewport → keep filling
    expect(host.loads).toBe(2);

    serverResponds(300); // 900px > 800px → scrollbar exists, stop auto-loading
    expect(host.loads).toBe(2);
  });

  it('does not emit while a load is in flight', () => {
    layout(4000);
    scrollToBottom();
    expect(host.loads).toBe(1);
    angularReacts(); // loadingMore = true reaches the directive

    // Scrolling away and back mid-request must not queue a second one.
    scrollTo(maxScrollTop() - 400);
    scrollToBottom();
    expect(host.loads).toBe(1);
  });

  it('keeps loading on scroll when the page scroll range is under the 240px margin', () => {
    // The real "بياناتي" state: page barely taller than the viewport (100px of
    // scroll range) and batches that add no height. The sentinel can never
    // leave the prefetch zone, so the observer can never re-arm — only the
    // scroll-gesture trigger can keep this page going.
    layout(900);
    scrollToBottom();
    expect(host.loads).toBe(1);
    serverResponds(0);

    scrollTo(0);
    scrollToBottom();
    expect(host.loads).toBe(2);

    serverResponds(0);
    scrollTo(0);
    scrollToBottom();
    expect(host.loads).toBe(3);
  });

  it('loads more when the user scrolls inside a capped table', () => {
    // Rows live behind the table's own scrollbar, and `scroll` does not bubble.
    // Only a capture-phase listener sees this gesture.
    layout(900);
    scrollToBottom();
    expect(host.loads).toBe(1);
    serverResponds(0);

    scrollInnerTableTo(100); // nowhere near the table's end → no request
    expect(host.loads).toBe(1);

    scrollInnerTableTo(4000 - 352); // scrolled to the last row
    expect(host.loads).toBe(2);
  });

  it('ignores scroll events that no user gesture produced', () => {
    layout(900);
    scrollToBottom();
    expect(host.loads).toBe(1);

    // Ten load cycles, each shaking out the browser-generated scroll events
    // that DOM churn causes. Not one of them is a request to load more.
    for (let i = 0; i < 10; i++) {
      serverResponds(0);
      browserEmitsScroll();
      browserEmitsScroll(innerTable);
    }

    expect(host.loads).toBe(1);
  });

  it('stops as soon as the user stops scrolling', () => {
    layout(900);
    scrollToBottom();
    expect(host.loads).toBe(1);

    // Sentinel parked inside the zone, inner table parked at its end: with no
    // further gesture, ten completed load cycles must request nothing.
    innerTable.scrollTop = 4000 - 352;
    for (let i = 0; i < 10; i++) {
      serverResponds(0);
    }

    expect(host.loads).toBe(1);
  });
});
