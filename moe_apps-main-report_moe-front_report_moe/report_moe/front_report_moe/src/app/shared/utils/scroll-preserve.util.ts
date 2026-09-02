const SCROLL_CONTAINER_SELECTOR = 'main.content';

export function getAppScrollContainer(): HTMLElement | null {
  return document.querySelector<HTMLElement>(SCROLL_CONTAINER_SELECTOR);
}

/** Captures scroll position in the app layout and returns a restore function. */
export function captureScrollPosition(): () => void {
  const container = getAppScrollContainer();
  const scrollTop = container?.scrollTop ?? window.scrollY;
  const scrollLeft = container?.scrollLeft ?? window.scrollX;

  const restore = () => {
    if (container) {
      container.scrollTo({ top: scrollTop, left: scrollLeft, behavior: 'auto' });
      return;
    }
    window.scrollTo({ top: scrollTop, left: scrollLeft, behavior: 'auto' });
  };

  return () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        restore();
        setTimeout(restore, 50);
        setTimeout(restore, 150);
        setTimeout(restore, 300);
      });
    });
  };
}
