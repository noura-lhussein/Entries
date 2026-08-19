export interface TableScrollConfig {
  /** Vertical cap; omit = design token; `'none'` = no vertical scroll cap */
  maxHeight?: string | null;
  /** `'auto'` = vertical scroll when rows exceed maxHeight; `'off'` = grow with page */
  vertical?: 'auto' | 'off';
}

export interface TableColumnSizing {
  width?: string;
  minWidth?: string;
  maxWidth?: string;
}

export function tableScrollClasses(scroll: TableScrollConfig = {}): Record<string, boolean> {
  return {
    'table-scroll--y-off': scroll.vertical === 'off',
  };
}

export function tableScrollStyle(scroll: TableScrollConfig = {}): Record<string, string> {
  if (scroll.vertical === 'off' || scroll.maxHeight === 'none') {
    return { '--table-scroll-max-height': 'none' };
  }
  if (scroll.maxHeight) {
    return { '--table-scroll-max-height': scroll.maxHeight };
  }
  return {};
}

export function columnSizingStyle(
  column: TableColumnSizing,
  widthPx?: number,
): Record<string, string | undefined> {
  if (widthPx != null) {
    return {
      width: `${widthPx}px`,
      minWidth: `${widthPx}px`,
    };
  }
  return {
    width: column.width,
    minWidth: column.minWidth,
    maxWidth: column.maxWidth,
  };
}
