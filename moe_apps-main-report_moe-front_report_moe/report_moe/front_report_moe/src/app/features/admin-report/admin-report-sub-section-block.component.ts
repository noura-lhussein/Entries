import {
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { TranslationService } from '../../shared/services/translation.service';
import { AdminReportTitleBlockComponent } from './admin-report-title-block.component';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';
import type { AdminReportRow, SubSectionBlock, TitleTable } from './admin-report.models';

export interface TitleRowActionEvent {
  titleTable: TitleTable;
  row: AdminReportRow;
  approve: boolean;
}

export interface TitleRowNoteEvent {
  titleTable: TitleTable;
  row: AdminReportRow;
}

export interface TitleBulkConfirmEvent {
  titleTable: TitleTable;
  approve: boolean;
}

@Component({
  selector: 'app-admin-report-sub-section-block',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    ButtonComponent,
    AdminReportTitleBlockComponent,
    EmptyStateComponent,
  ],
  templateUrl: './admin-report-sub-section-block.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './admin-report-sub-section-block.component.scss',
})
export class AdminReportSubSectionBlockComponent {
  @Input({ required: true }) block!: SubSectionBlock;
  @Input() canConfirm = false;
  @Input() emptyMessage = '';

  @Output() titleToggle = new EventEmitter<TitleTable>();
  @Output() blockBulkConfirm = new EventEmitter<void>();
  @Output() blockBulkReject = new EventEmitter<void>();
  @Output() blockBulkCommitNote = new EventEmitter<void>();
  @Output() titleBulkConfirm = new EventEmitter<TitleBulkConfirmEvent>();
  @Output() titleBulkCommitNote = new EventEmitter<TitleTable>();
  @Output() rowConfirm = new EventEmitter<TitleRowActionEvent>();
  @Output() rowCommitNote = new EventEmitter<TitleRowNoteEvent>();
  @Output() titleLoadMore = new EventEmitter<TitleTable>();

  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  onRowConfirm(tt: TitleTable, event: { row: AdminReportRow; approve: boolean }): void {
    this.rowConfirm.emit({ titleTable: tt, row: event.row, approve: event.approve });
  }

  onRowCommitNote(tt: TitleTable, row: AdminReportRow): void {
    this.rowCommitNote.emit({ titleTable: tt, row });
  }

  trackByTitleId(_index: number, table: TitleTable): string | number {
    return table.titleId ?? _index;
  }
}
