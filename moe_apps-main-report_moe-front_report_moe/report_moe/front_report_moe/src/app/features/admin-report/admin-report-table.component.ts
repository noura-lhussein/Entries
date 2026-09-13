import {
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import {
  TableComponent,
  type TableAction,
  type TableColumn,
  type TableRow,
  type TableScrollConfig,
} from '../../shared/components/table/table.component';
import { TranslationService } from '../../shared/services/translation.service';

import { INFO_TABLE_SCROLL } from '../../shared/utils/info-table-scroll';
import type { AdminReportColumn, AdminReportRow } from './admin-report.models';

@Component({
  selector: 'app-admin-report-table',
  standalone: true,
  imports: [TableComponent],
  changeDetection: ChangeDetectionStrategy.Eager,
  template: `
    <app-table
      [data]="rows"
      [columns]="mappedColumns"
      [actions]="tableActions"
      [paginator]="false"
      [selectable]="false"
      [scroll]="scroll"
      [resizableColumns]="true"
      [autoFitColumns]="true"
      [canConfirmStatusActions]="canConfirm"
      [confirmStatusInActions]="true"
      [bulkActionsInHeader]="canConfirm"
      [showBulkApproveAction]="showBulkConfirm"
      [showBulkRejectAction]="showBulkReject"
      [showBulkCommitNoteAction]="true"
      [actionsLabel]="t('table.actions')"
      (actionClicked)="handleAction($event)"
      (confirmStatusClicked)="handleConfirmStatus($event)"
      (bulkActionClicked)="handleBulkAction($event)"
    />
  `,
})
export class AdminReportTableComponent {
  @Input({ required: true }) columns!: AdminReportColumn[];
  @Input({ required: true }) rows!: TableRow[];
  @Input() canConfirm = false;
  @Input() showBulkConfirm = true;
  @Input() showBulkReject = true;
  /** Cap each title table with its own vertical scroller. */
  @Input() scroll: TableScrollConfig = INFO_TABLE_SCROLL;

  @Output() rowConfirm = new EventEmitter<{ row: AdminReportRow; approve: boolean }>();
  @Output() rowCommitNote = new EventEmitter<AdminReportRow>();
  @Output() bulkConfirm = new EventEmitter<boolean>();
  @Output() bulkCommitNote = new EventEmitter<void>();

  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  get mappedColumns(): TableColumn[] {
    return this.columns
      .filter((col) => col.key !== '_confirm_status')
      .map((col) => {
        const sizing = {
          width: col.width,
          minWidth: col.minWidth,
          maxWidth: col.maxWidth,
        };
        if (col.key === '_confirm_note') {
          return { ...col, ...sizing, type: 'note' as const };
        }
        if (col.key === '_commit_note') {
          return { ...col, ...sizing, type: 'commit-note' as const };
        }
        if (col.key.startsWith('attr_')) {
          return { ...col, ...sizing, type: 'media' as const };
        }
        return { ...col, ...sizing, type: 'text' as const };
      });
  }

  get tableActions(): TableAction[] {
    if (!this.canConfirm) {
      return [];
    }
    return [
      {
        type: 'commit-note',
        label: this.t('admin-report.commit-with-note-tooltip'),
        icon: 'comment',
        color: 'warning',
      },
    ];
  }

  handleAction(event: { type: string; row: TableRow }): void {
    const row = event.row as AdminReportRow;
    if (event.type === 'commit-note') {
      this.rowCommitNote.emit(row);
    }
  }

  handleConfirmStatus(event: { action: 'approve' | 'reject'; row: TableRow }): void {
    const row = event.row as AdminReportRow;
    this.rowConfirm.emit({ row, approve: event.action === 'approve' });
  }

  handleBulkAction(action: 'approve' | 'reject' | 'commit-note'): void {
    if (action === 'commit-note') {
      this.bulkCommitNote.emit();
      return;
    }
    this.bulkConfirm.emit(action === 'approve');
  }
}
