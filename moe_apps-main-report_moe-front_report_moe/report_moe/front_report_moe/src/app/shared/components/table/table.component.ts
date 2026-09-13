import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnChanges,
  OnDestroy,
  AfterViewInit,
  ChangeDetectorRef,
  ElementRef,
  ViewChild,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { TranslationService } from '../../services/translation.service';
import { StoredMediaValueComponent } from '../stored-media-value/stored-media-value.component';
import {
  type TableScrollConfig,
  columnSizingStyle,
  tableScrollClasses,
  tableScrollStyle,
} from './table-scroll.config';
import { normalizeInfoConfirmStatus } from '../../../core/models/info-confirm-status';
import {
  ACTIONS_COLUMN_KEY,
  computeInitialColumnWidths,
  parseColumnWidthPx,
} from './table-column-sizing.util';

export type { TableScrollConfig } from './table-scroll.config';

export type ColumnType =
  | 'text'
  | 'avatar'
  | 'badge'
  | 'date'
  | 'boolean'
  | 'status'
  | 'media'
  | 'note'
  | 'commit-note'
  | 'confirm-status'
  | 'confirmed-field';
export type SortDirection = 'asc' | 'desc' | '';

export interface BadgeStyle {
  bg: string;
  color: string;
}

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  minWidth?: string;
  maxWidth?: string;
  type?: ColumnType;
  format?: (value: any) => string;
  subKey?: string;
  badgeMap?: { [value: string]: BadgeStyle };
  trueLabel?: string;
  falseLabel?: string;
}

export interface TableRow {
  [key: string]: any;
  id?: string | number;
}

export interface TableAction {
  type: string;
  label: string;
  icon: string;
  color?: 'view' | 'edit' | 'delete' | 'primary' | 'default' | 'warning';
  disabled?: boolean | ((row: TableRow) => boolean);
  /** When set, the action is only rendered for rows where this returns true. */
  show?: (row: TableRow) => boolean;
}

@Component({
  selector: 'app-table',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, MatTooltipModule, StoredMediaValueComponent],
  template: `
    <div
      class="table-wrapper"
      [class.is-h-scrollable]="hScrollable"
      [class.has-more-left]="moreLeft"
      [class.has-more-right]="moreRight"
      [class.with-actions-col]="showActionsColumn"
      [style.--actions-sticky-width.px]="actionsStickyWidthPx"
      [attr.aria-label]="hScrollable ? hScrollHintLabel : null"
    >
      <div class="h-scroll-fade h-scroll-fade--left" aria-hidden="true"></div>
      <div class="h-scroll-fade h-scroll-fade--right" aria-hidden="true"></div>
      <div class="h-scroll-cue h-scroll-cue--left" *ngIf="moreLeft" aria-hidden="true">
        <mat-icon>chevron_left</mat-icon>
      </div>
      <div class="h-scroll-cue h-scroll-cue--right" *ngIf="moreRight" aria-hidden="true">
        <mat-icon>chevron_right</mat-icon>
      </div>
      <div
        #scrollContainer
        class="table-scroll"
        [ngClass]="scrollClasses"
        [ngStyle]="scrollStyles"
        (scroll)="onTableScroll()"
      >
        <table
          class="data-table"
          [class.resizable-columns]="resizableColumns"
          [style.minWidth.px]="tableMinWidthPx"
        >
          <thead>
            <tr>
              <th *ngIf="selectable" class="select-col">
                <input type="checkbox" [checked]="isAllSelected()" (change)="toggleSelectAll()" />
              </th>
              <th
                *ngFor="let column of columns"
                class="data-col-header"
                [ngStyle]="columnStyle(column)"
                [class.sortable]="column.sortable"
                (click)="column.sortable && onSort(column.key)"
              >
                <div class="th-content">
                  <span>{{ column.label }}</span>
                  <span *ngIf="column.sortable" class="sort-icon">
                    <mat-icon [class.active]="sortKey === column.key && sortDir === 'asc'"
                      >expand_less</mat-icon
                    >
                    <mat-icon [class.active]="sortKey === column.key && sortDir === 'desc'"
                      >expand_more</mat-icon
                    >
                  </span>
                </div>
                <span
                  *ngIf="resizableColumns"
                  class="col-resizer"
                  role="separator"
                  [attr.aria-label]="resizeColumnLabel"
                  [matTooltip]="resizeColumnLabel"
                  matTooltipPosition="above"
                  (mousedown)="onResizeStart($event, column.key)"
                ></span>
              </th>
              <th *ngIf="showActionsColumn" class="actions-col" [ngStyle]="actionsColumnStyle()">
                <div class="actions-header" (click)="$event.stopPropagation()">
                  <span class="actions-header-label">{{ resolvedActionsLabel }}</span>
                  <div *ngIf="bulkActionsInHeader" class="actions-group actions-group--bulk">
                    <button
                      *ngIf="showBulkRejectAction"
                      type="button"
                      class="confirm-status-icon confirm-status-icon--reject is-active"
                      [matTooltip]="confirmStatusRejectLabel"
                      (click)="onBulkAction('reject')"
                    >
                      <mat-icon>cancel</mat-icon>
                    </button>
                    <button
                      *ngIf="showBulkCommitNoteAction"
                      type="button"
                      class="action-btn action-warning"
                      [matTooltip]="bulkCommitNoteLabel"
                      (click)="onBulkAction('commit-note')"
                    >
                      <mat-icon>comment</mat-icon>
                    </button>
                    <button
                      *ngIf="showBulkApproveAction"
                      type="button"
                      class="confirm-status-icon confirm-status-icon--approve is-active"
                      [matTooltip]="confirmStatusApproveLabel"
                      (click)="onBulkAction('approve')"
                    >
                      <mat-icon>check_circle</mat-icon>
                    </button>
                  </div>
                </div>
                <span
                  *ngIf="resizableColumns"
                  class="col-resizer"
                  role="separator"
                  [attr.aria-label]="resizeColumnLabel"
                  [matTooltip]="resizeColumnLabel"
                  matTooltipPosition="above"
                  (mousedown)="onResizeStart($event, actionsColumnKey)"
                ></span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              *ngFor="let row of pagedData"
              [attr.data-row-id]="row['id']"
              [class.selected]="isRowSelected(row.id)"
              [class.clickable]="rowClickable"
              (click)="onRowClick(row)"
            >
              <td *ngIf="selectable" class="select-col" (click)="$event.stopPropagation()">
                <input
                  type="checkbox"
                  [checked]="isRowSelected(row.id)"
                  (change)="toggleRowSelection(row.id)"
                />
              </td>
              <td
                *ngFor="let column of columns"
                [ngStyle]="columnStyle(column)"
                [ngSwitch]="column.type || 'text'"
              >
                <ng-container *ngSwitchCase="'avatar'">
                  <div class="avatar-cell">
                    <div class="avatar">{{ getInitial(row[column.key]) }}</div>
                    <div class="avatar-text">
                      <div class="avatar-name">{{ row[column.key] }}</div>
                      <div class="avatar-sub" *ngIf="column.subKey">{{ row[column.subKey] }}</div>
                    </div>
                  </div>
                </ng-container>
                <ng-container *ngSwitchCase="'badge'">
                  <span class="badge" [ngStyle]="getBadgeStyle(column, row[column.key])">
                    {{ column.format ? column.format(row[column.key]) : row[column.key] }}
                  </span>
                </ng-container>
                <ng-container *ngSwitchCase="'boolean'">
                  <span
                    class="badge"
                    [class.badge-true]="row[column.key]"
                    [class.badge-false]="!row[column.key]"
                  >
                    {{
                      row[column.key]
                        ? column.trueLabel || 'مفعّل'
                        : column.falseLabel || 'غير مفعّل'
                    }}
                  </span>
                </ng-container>
                <ng-container *ngSwitchCase="'date'">
                  {{ formatDate(row[column.key]) }}
                </ng-container>
                <ng-container *ngSwitchCase="'media'">
                  <app-stored-media-value
                    [value]="row[column.key]"
                    variant="table"
                  ></app-stored-media-value>
                </ng-container>
                <ng-container *ngSwitchCase="'confirmed-field'">
                  <div class="confirmed-field-cell">
                    <div class="confirmed-field-value">
                      <app-stored-media-value
                        [value]="row[column.key]"
                        variant="table"
                      ></app-stored-media-value>
                    </div>
                    <span
                      *ngIf="hasFieldValue(row, column)"
                      class="field-confirm-badge"
                      [class.field-confirm-badge--confirmed]="isFieldAccepted(row, column)"
                      [class.field-confirm-badge--rejected]="isFieldRejected(row, column)"
                      [class.field-confirm-badge--waiting]="isFieldWaiting(row, column)"
                      [matTooltip]="fieldStatusTooltip(row, column)"
                    >
                      <mat-icon>{{ fieldStatusIcon(row, column) }}</mat-icon>
                    </span>
                  </div>
                </ng-container>
                <ng-container *ngSwitchCase="'note'">
                  <span class="note-cell">{{ row[column.key] }}</span>
                </ng-container>
                <ng-container *ngSwitchCase="'commit-note'">
                  <span class="commit-note-cell">{{ row[column.key] }}</span>
                </ng-container>
                <ng-container *ngSwitchDefault>
                  {{ column.format ? column.format(row[column.key]) : row[column.key] }}
                </ng-container>
              </td>
              <td *ngIf="showActionsColumn" class="actions-col" (click)="$event.stopPropagation()">
                <div class="actions-group">
                  <div *ngIf="confirmStatusInActions" class="confirm-status-group">
                    <button
                      type="button"
                      class="confirm-status-icon confirm-status-icon--waiting"
                      [class.is-active]="row['_confirmStatus'] === 'waiting'"
                      [matTooltip]="confirmStatusWaitingLabel"
                      [disabled]="true"
                      tabindex="-1"
                    >
                      <mat-icon>schedule</mat-icon>
                    </button>
                    <button
                      type="button"
                      class="confirm-status-icon confirm-status-icon--reject"
                      [class.is-active]="row['_confirmStatus'] === 'rejected'"
                      [matTooltip]="confirmStatusRejectLabel"
                      [disabled]="!canConfirmStatusActions || row['_confirmStatus'] === 'rejected'"
                      (click)="onConfirmStatusAction('reject', row)"
                    >
                      <mat-icon>cancel</mat-icon>
                    </button>
                    <button
                      type="button"
                      class="confirm-status-icon confirm-status-icon--approve"
                      [class.is-active]="row['_confirmStatus'] === 'approved'"
                      [matTooltip]="confirmStatusApproveLabel"
                      [disabled]="!canConfirmStatusActions || row['_confirmStatus'] === 'approved'"
                      (click)="onConfirmStatusAction('approve', row)"
                    >
                      <mat-icon>check_circle</mat-icon>
                    </button>
                  </div>
                  <ng-container *ngFor="let action of actions">
                    <button
                      *ngIf="isActionVisible(action, row)"
                      type="button"
                      class="action-btn"
                      [ngClass]="'action-' + (action.color || 'default')"
                      [matTooltip]="action.label"
                      [disabled]="isActionDisabled(action, row)"
                      (click)="onAction(action.type, row, $event)"
                    >
                      <mat-icon>{{ action.icon }}</mat-icon>
                    </button>
                  </ng-container>
                </div>
              </td>
            </tr>
            <tr *ngIf="pagedData.length === 0">
              <td [attr.colspan]="totalColSpan" class="no-data">{{ emptyMessage }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination" *ngIf="paginator && data.length > 0">
        <div class="page-size">
          <label>Row Per Page</label>
          <select [(ngModel)]="pageSize" (change)="onPageSizeChange()">
            <option *ngFor="let opt of pageSizeOptions" [ngValue]="opt">{{ opt }}</option>
          </select>
          <span>Entries</span>
        </div>
        <div class="page-controls">
          <button
            type="button"
            class="page-btn"
            [disabled]="currentPage === 0"
            (click)="prevPage()"
          >
            <mat-icon>arrow_back</mat-icon>
          </button>
          <button
            type="button"
            class="page-btn"
            [disabled]="currentPage >= totalPages - 1"
            (click)="nextPage()"
          >
            <mat-icon>arrow_forward</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './table.component.scss',
})
export class TableComponent implements OnInit, OnChanges, AfterViewInit, OnDestroy {
  @ViewChild('scrollContainer', { static: true })
  scrollContainer?: ElementRef<HTMLElement>;

  @Input() data: TableRow[] = [];
  @Input() columns: TableColumn[] = [];
  @Input() actions: TableAction[] = [];
  @Input() paginator = true;
  @Input() pageSize = 10;
  @Input() pageSizeOptions = [5, 10, 25, 50];
  @Input() selectable = false;
  @Input() rowClickable = false;
  @Input() actionsLabel?: string;
  @Input() emptyMessage = 'No data available';
  @Input() scroll: TableScrollConfig = {};
  @Input() resizableColumns = true;
  @Input() autoFitColumns = true;
  @Input() minColumnWidth = 72;
  @Input() maxColumnWidth = 640;
  /** Enables approve/reject icons in confirm-status (column or actions cell). */
  @Input() canConfirmStatusActions = false;
  /** Render waiting/reject/approve controls inside the sticky actions column. */
  @Input() confirmStatusInActions = false;
  /** Show bulk approve/reject/note controls in the actions column header (not above the title). */
  @Input() bulkActionsInHeader = false;
  @Input() showBulkApproveAction = true;
  @Input() showBulkRejectAction = true;
  @Input() showBulkCommitNoteAction = true;

  readonly actionsColumnKey = ACTIONS_COLUMN_KEY;

  hScrollable = false;
  moreLeft = false;
  moreRight = false;
  actionsStickyWidthPx = 0;

  get showActionsColumn(): boolean {
    return this.actions.length > 0 || this.confirmStatusInActions || this.bulkActionsInHeader;
  }

  private translation = inject(TranslationService);
  private cdr = inject(ChangeDetectorRef);
  private columnWidthsPx: Record<string, number> = {};
  private userResizedKeys = new Set<string>();
  private resizing: { key: string; startX: number; startWidth: number } | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private hScrollRaf = 0;

  get scrollClasses(): Record<string, boolean> {
    return tableScrollClasses(this.scroll);
  }

  get scrollStyles(): Record<string, string> {
    return tableScrollStyle(this.scroll);
  }

  columnStyle(column: TableColumn): Record<string, string | undefined> {
    return columnSizingStyle(column, this.columnWidthsPx[column.key]);
  }

  actionsColumnStyle(): Record<string, string | undefined> {
    return columnSizingStyle({}, this.columnWidthsPx[ACTIONS_COLUMN_KEY]);
  }

  get tableMinWidthPx(): number {
    let total = this.selectable ? 48 : 0;
    for (const column of this.columns) {
      total += this.columnWidthsPx[column.key] ?? this.minColumnWidth;
    }
    if (this.showActionsColumn) {
      total += this.columnWidthsPx[ACTIONS_COLUMN_KEY] ?? 96;
    }
    return total;
  }

  get resolvedActionsLabel(): string {
    return this.actionsLabel ?? this.translation.t('table.actions');
  }

  get resizeColumnLabel(): string {
    return this.translation.t('table.resize-column');
  }

  get hScrollHintLabel(): string {
    return this.translation.t('table.scroll-columns-hint');
  }

  get confirmStatusWaitingLabel(): string {
    return this.translation.t('admin-report.status-waiting');
  }

  get confirmStatusApproveLabel(): string {
    return this.translation.t('info-report.approval');
  }

  get confirmStatusRejectLabel(): string {
    return this.translation.t('info-report.rejection');
  }

  get bulkCommitNoteLabel(): string {
    return this.translation.t('admin-report.commit-with-note-tooltip');
  }

  get fieldAcceptedLabel(): string {
    return this.translation.t('user-data.confirmed-true');
  }

  get fieldRejectedLabel(): string {
    return this.translation.t('user-data.confirmed-reject');
  }

  get fieldWaitingLabel(): string {
    return this.translation.t('admin-report.status-waiting');
  }

  /** Admin-report attr columns use keys like attr_12 → _attr_12_status. */
  fieldStatusKey(columnKey: string): string {
    if (columnKey.startsWith('attr_')) {
      return `_attr_${columnKey.slice('attr_'.length)}_status`;
    }
    return `_${columnKey}_status`;
  }

  hasFieldValue(row: TableRow, column: TableColumn): boolean {
    const value = row[column.key];
    return value != null && String(value).trim() !== '' && value !== '—';
  }

  fieldStatus(row: TableRow, column: TableColumn): string {
    return normalizeInfoConfirmStatus(row[this.fieldStatusKey(column.key)] as string);
  }

  isFieldAccepted(row: TableRow, column: TableColumn): boolean {
    return this.fieldStatus(row, column) === 'accept';
  }

  isFieldRejected(row: TableRow, column: TableColumn): boolean {
    return this.fieldStatus(row, column) === 'reject';
  }

  isFieldWaiting(row: TableRow, column: TableColumn): boolean {
    return this.fieldStatus(row, column) === 'waiting';
  }

  fieldStatusIcon(row: TableRow, column: TableColumn): string {
    if (this.isFieldAccepted(row, column)) return 'check_circle';
    if (this.isFieldRejected(row, column)) return 'close';
    return 'schedule';
  }

  fieldStatusTooltip(row: TableRow, column: TableColumn): string {
    if (this.isFieldAccepted(row, column)) return this.fieldAcceptedLabel;
    if (this.isFieldRejected(row, column)) return this.fieldRejectedLabel;
    return this.fieldWaitingLabel;
  }

  @Output() pageChange = new EventEmitter<{ pageIndex: number; pageSize: number }>();
  @Output() sortChange = new EventEmitter<{ key: string; direction: SortDirection }>();
  @Output() rowClicked = new EventEmitter<TableRow>();
  @Output() actionClicked = new EventEmitter<{
    type: string;
    row: TableRow;
    /** Bounding rect of the table row (for expand-into-dialog animations). */
    origin?: DOMRect;
  }>();
  @Output() confirmStatusClicked = new EventEmitter<{
    action: 'approve' | 'reject';
    row: TableRow;
  }>();
  @Output() bulkActionClicked = new EventEmitter<'approve' | 'reject' | 'commit-note'>();
  @Output() selectionChange = new EventEmitter<TableRow[]>();

  pagedData: TableRow[] = [];
  selectedRows = new Set<string | number>();
  currentPage = 0;
  sortKey = '';
  sortDir: SortDirection = '';

  ngOnInit(): void {
    this.updatePagedData();
    this.syncAutoColumnWidths();
  }

  ngAfterViewInit(): void {
    const el = this.scrollContainer?.nativeElement;
    if (el && typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => this.scheduleHScrollCueUpdate());
      this.resizeObserver.observe(el);
      const table = el.querySelector('table');
      if (table) {
        this.resizeObserver.observe(table);
      }
    }
    this.scheduleHScrollCueUpdate();
  }

  ngOnChanges(): void {
    this.updatePagedData();
    this.syncAutoColumnWidths();
    this.scheduleHScrollCueUpdate();
  }

  ngOnDestroy(): void {
    this.stopResizeListeners();
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
    if (this.hScrollRaf) {
      cancelAnimationFrame(this.hScrollRaf);
      this.hScrollRaf = 0;
    }
  }

  onTableScroll(): void {
    this.scheduleHScrollCueUpdate();
  }

  private scheduleHScrollCueUpdate(): void {
    if (this.hScrollRaf) {
      cancelAnimationFrame(this.hScrollRaf);
    }
    this.hScrollRaf = requestAnimationFrame(() => {
      this.hScrollRaf = 0;
      this.updateHScrollCues();
    });
  }

  private updateHScrollCues(): void {
    const el = this.scrollContainer?.nativeElement;
    if (!el) {
      return;
    }

    const table = el.querySelector('table');
    const epsilon = 2;
    let moreLeft = false;
    let moreRight = false;
    let hScrollable = el.scrollWidth > el.clientWidth + epsilon;

    if (hScrollable && table) {
      const containerRect = el.getBoundingClientRect();
      const tableRect = table.getBoundingClientRect();
      moreLeft = tableRect.left < containerRect.left - epsilon;
      moreRight = tableRect.right > containerRect.right + epsilon;
      // If geometry is inconclusive (some sticky layouts), fall back to scroll metrics.
      if (!moreLeft && !moreRight) {
        moreLeft = el.scrollLeft > epsilon;
        moreRight = el.scrollLeft + el.clientWidth < el.scrollWidth - epsilon;
      }
    }

    let actionsWidth = 0;
    if (this.showActionsColumn) {
      const actionsCell = el.querySelector('th.actions-col, td.actions-col') as HTMLElement | null;
      actionsWidth = actionsCell?.offsetWidth ?? this.columnWidthsPx[ACTIONS_COLUMN_KEY] ?? 0;
    }

    if (
      this.hScrollable !== hScrollable ||
      this.moreLeft !== moreLeft ||
      this.moreRight !== moreRight ||
      this.actionsStickyWidthPx !== actionsWidth
    ) {
      this.hScrollable = hScrollable;
      this.moreLeft = moreLeft;
      this.moreRight = moreRight;
      this.actionsStickyWidthPx = actionsWidth;
      this.cdr.markForCheck();
    }
  }

  onResizeStart(event: MouseEvent, columnKey: string): void {
    event.preventDefault();
    event.stopPropagation();

    const header = (event.target as HTMLElement).closest('th');
    const startWidth = header?.offsetWidth ?? this.columnWidthsPx[columnKey] ?? this.minColumnWidth;

    this.resizing = { key: columnKey, startX: event.clientX, startWidth };
    document.body.classList.add('table-col-resizing');
    document.addEventListener('mousemove', this.onResizeMove);
    document.addEventListener('mouseup', this.onResizeEnd);
  }

  private onResizeMove = (event: MouseEvent): void => {
    if (!this.resizing) {
      return;
    }

    const rawDelta = event.clientX - this.resizing.startX;
    const delta = document.documentElement.dir === 'rtl' ? -rawDelta : rawDelta;
    const nextWidth = this.clampColumnWidth(this.resizing.startWidth + delta);

    this.columnWidthsPx[this.resizing.key] = nextWidth;
    this.userResizedKeys.add(this.resizing.key);
    this.cdr.markForCheck();
  };

  private onResizeEnd = (): void => {
    this.resizing = null;
    this.stopResizeListeners();
    this.cdr.markForCheck();
  };

  private stopResizeListeners(): void {
    document.body.classList.remove('table-col-resizing');
    document.removeEventListener('mousemove', this.onResizeMove);
    document.removeEventListener('mouseup', this.onResizeEnd);
  }

  private clampColumnWidth(width: number): number {
    return Math.min(this.maxColumnWidth, Math.max(this.minColumnWidth, Math.round(width)));
  }

  private syncAutoColumnWidths(): void {
    if (!this.autoFitColumns) {
      return;
    }

    const computed = computeInitialColumnWidths(this.columns, this.data, {
      selectable: this.selectable,
      actionCount: this.actions.length,
      actionsLabel: this.resolvedActionsLabel,
      confirmStatusInActions: this.confirmStatusInActions,
    });

    for (const column of this.columns) {
      if (this.userResizedKeys.has(column.key)) {
        continue;
      }
      const explicit = parseColumnWidthPx(column.width);
      this.columnWidthsPx[column.key] = explicit ?? computed[column.key];
    }

    if (this.showActionsColumn && !this.userResizedKeys.has(ACTIONS_COLUMN_KEY)) {
      this.columnWidthsPx[ACTIONS_COLUMN_KEY] = computed[ACTIONS_COLUMN_KEY];
    }
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.data.length / this.pageSize));
  }

  get totalColSpan(): number {
    return this.columns.length + (this.selectable ? 1 : 0) + (this.showActionsColumn ? 1 : 0);
  }

  private updatePagedData(): void {
    if (!this.paginator) {
      this.pagedData = this.data;
      return;
    }
    const start = this.currentPage * this.pageSize;
    this.pagedData = this.data.slice(start, start + this.pageSize);
  }

  onSort(key: string): void {
    if (this.sortKey === key) {
      this.sortDir = this.sortDir === 'asc' ? 'desc' : this.sortDir === 'desc' ? '' : 'asc';
    } else {
      this.sortKey = key;
      this.sortDir = 'asc';
    }
    if (!this.sortDir) this.sortKey = '';
    this.sortChange.emit({ key: this.sortKey, direction: this.sortDir });
  }

  onPageSizeChange(): void {
    this.currentPage = 0;
    this.updatePagedData();
    this.pageChange.emit({ pageIndex: this.currentPage, pageSize: this.pageSize });
  }

  prevPage(): void {
    if (this.currentPage === 0) return;
    this.currentPage--;
    this.updatePagedData();
    this.pageChange.emit({ pageIndex: this.currentPage, pageSize: this.pageSize });
  }

  nextPage(): void {
    if (this.currentPage >= this.totalPages - 1) return;
    this.currentPage++;
    this.updatePagedData();
    this.pageChange.emit({ pageIndex: this.currentPage, pageSize: this.pageSize });
  }

  onRowClick(row: TableRow): void {
    if (this.rowClickable) this.rowClicked.emit(row);
  }

  isActionVisible(action: TableAction, row: TableRow): boolean {
    if (!action.show) return true;
    return action.show(row);
  }

  isActionDisabled(action: TableAction, row: TableRow): boolean {
    if (!action.disabled) return false;
    if (typeof action.disabled === 'function') {
      return action.disabled(row);
    }
    return action.disabled;
  }

  onAction(type: string, row: TableRow, event: MouseEvent): void {
    const tr = (event.currentTarget as HTMLElement).closest('tr');
    const origin = tr?.getBoundingClientRect();
    this.actionClicked.emit({ type, row, origin });
  }

  onConfirmStatusAction(action: 'approve' | 'reject', row: TableRow): void {
    if (!this.canConfirmStatusActions) return;
    this.confirmStatusClicked.emit({ action, row });
  }

  onBulkAction(action: 'approve' | 'reject' | 'commit-note'): void {
    if (!this.bulkActionsInHeader) return;
    this.bulkActionClicked.emit(action);
  }

  isRowSelected(id: string | number | undefined): boolean {
    return id != null && this.selectedRows.has(id);
  }

  toggleRowSelection(id: string | number | undefined): void {
    if (id == null) return;
    if (this.selectedRows.has(id)) {
      this.selectedRows.delete(id);
    } else {
      this.selectedRows.add(id);
    }
    this.emitSelection();
  }

  isAllSelected(): boolean {
    return this.pagedData.length > 0 && this.pagedData.every((row) => this.isRowSelected(row.id));
  }

  toggleSelectAll(): void {
    if (this.isAllSelected()) {
      this.pagedData.forEach((row) => row.id != null && this.selectedRows.delete(row.id));
    } else {
      this.pagedData.forEach((row) => row.id != null && this.selectedRows.add(row.id));
    }
    this.emitSelection();
  }

  getInitial(value: any): string {
    if (!value) return '?';
    return String(value).trim().charAt(0).toUpperCase();
  }

  getBadgeStyle(column: TableColumn, value: unknown): { [key: string]: string } {
    const key =
      column.badgeMap && 'accept' in column.badgeMap
        ? normalizeInfoConfirmStatus(value as string | boolean)
        : String(value ?? '');
    const map = column.badgeMap?.[key];
    if (map) return { 'background-color': map.bg, color: map.color };
    return { 'background-color': '#f3f4f6', color: '#374151' };
  }

  formatDate(value: any): string {
    if (!value) return '';
    const d = value instanceof Date ? value : new Date(value);
    if (isNaN(d.getTime())) return String(value);
    return d.toLocaleDateString('en-US');
  }

  private emitSelection(): void {
    const selectedData = this.data.filter((row) => this.isRowSelected(row.id));
    this.selectionChange.emit(selectedData);
  }
}
