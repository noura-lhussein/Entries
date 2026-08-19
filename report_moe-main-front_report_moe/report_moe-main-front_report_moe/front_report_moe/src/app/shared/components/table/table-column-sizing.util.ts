import type { TableColumn, TableRow } from './table.component';

export const ACTIONS_COLUMN_KEY = '__actions__';
export const SELECT_COLUMN_KEY = '__select__';

const MIN_COL_WIDTH = 72;
const MAX_COL_WIDTH = 520;
const CELL_PADDING = 36;
const SAMPLE_ROW_LIMIT = 40;

const measureCanvas = document.createElement('canvas');
const measureCtx = measureCanvas.getContext('2d');

function measureText(text: string, font: string): number {
  if (!text || !measureCtx) {
    return 0;
  }
  measureCtx.font = font;
  return measureCtx.measureText(text).width;
}

function clampWidth(width: number, min = MIN_COL_WIDTH, max = MAX_COL_WIDTH): number {
  return Math.min(max, Math.max(min, Math.round(width)));
}

function parsePx(value: string | undefined): number | null {
  if (!value) {
    return null;
  }
  const match = /^(\d+(?:\.\d+)?)px$/i.exec(value.trim());
  return match ? Number(match[1]) : null;
}

function cellDisplayText(column: TableColumn, value: unknown): string {
  if (value == null || value === '') {
    return '—';
  }
  if (column.format) {
    return String(column.format(value));
  }
  if (column.type === 'date') {
    const d = value instanceof Date ? value : new Date(String(value));
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString('en-US');
    }
  }
  if (column.type === 'boolean') {
    return value ? column.trueLabel || 'مفعّل' : column.falseLabel || 'غير مفعّل';
  }
  return String(value);
}

function defaultMaxForColumn(column: TableColumn): number {
  if (column.maxWidth) {
    const parsed = parsePx(column.maxWidth);
    if (parsed) {
      return parsed;
    }
  }
  if (column.key === 'user_name') {
    return 160;
  }
  if (column.type === 'note' || column.type === 'commit-note') {
    return 320;
  }
  if (column.type === 'media') {
    return MAX_COL_WIDTH;
  }
  if (column.type === 'avatar') {
    return 220;
  }
  return MAX_COL_WIDTH;
}

function defaultMinForColumn(column: TableColumn): number {
  if (column.minWidth) {
    const parsed = parsePx(column.minWidth);
    if (parsed) {
      return parsed;
    }
  }
  if (column.type === 'media') {
    return 96;
  }
  return MIN_COL_WIDTH;
}

export function estimateColumnWidth(
  column: TableColumn,
  rows: TableRow[],
  headerFont = '600 12px system-ui, sans-serif',
  cellFont = '400 14px system-ui, sans-serif',
): number {
  const explicit = parsePx(column.width);
  if (explicit) {
    return clampWidth(explicit, defaultMinForColumn(column), defaultMaxForColumn(column));
  }

  let maxContent = measureText(column.label, headerFont);
  const sample = rows.slice(0, SAMPLE_ROW_LIMIT);

  for (const row of sample) {
    const text = cellDisplayText(column, row[column.key]);
    maxContent = Math.max(maxContent, measureText(text, cellFont));
  }

  return clampWidth(
    maxContent + CELL_PADDING,
    defaultMinForColumn(column),
    defaultMaxForColumn(column),
  );
}

export function computeInitialColumnWidths(
  columns: TableColumn[],
  rows: TableRow[],
  options: {
    selectable?: boolean;
    actionCount?: number;
    actionsLabel?: string;
    confirmStatusInActions?: boolean;
  } = {},
): Record<string, number> {
  const widths: Record<string, number> = {};

  if (options.selectable) {
    widths[SELECT_COLUMN_KEY] = 48;
  }

  for (const column of columns) {
    widths[column.key] = estimateColumnWidth(column, rows);
  }

  const actionCount = options.actionCount ?? 0;
  const confirmIcons = options.confirmStatusInActions ? 3 : 0;
  if (actionCount > 0 || options.confirmStatusInActions) {
    const labelWidth = measureText(options.actionsLabel || '', '600 12px system-ui, sans-serif');
    const actionsWidth = actionCount * 36 + confirmIcons * 30 + 28;
    widths[ACTIONS_COLUMN_KEY] = clampWidth(
      Math.max(labelWidth + CELL_PADDING, actionsWidth),
      options.confirmStatusInActions ? 132 : 96,
      260,
    );
  }

  return widths;
}

export function parseColumnWidthPx(value: string | undefined): number | null {
  return parsePx(value);
}
