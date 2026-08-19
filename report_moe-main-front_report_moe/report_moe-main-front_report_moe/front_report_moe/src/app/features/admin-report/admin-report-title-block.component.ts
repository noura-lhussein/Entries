import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { TranslationService } from '../../shared/services/translation.service';
import { InfiniteScrollDirective } from '../../shared/directives/infinite-scroll.directive';
import { AdminReportTableComponent } from './admin-report-table.component';
import type { AdminReportRow, TitleTable } from './admin-report.models';

@Component({
  selector: 'app-admin-report-title-block',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    AdminReportTableComponent,
    InfiniteScrollDirective,
  ],
  templateUrl: './admin-report-title-block.component.html',
  styleUrl: './admin-report-title-block.component.scss',
})
export class AdminReportTitleBlockComponent {
  @Input({ required: true }) titleTable!: TitleTable;
  @Input() canConfirm = false;
  @Input() emptyMessage = '';
  @Input() loadHint = '';
  /** When true, title name header is omitted (parent shows title + section path). */
  @Input() hideTitleHeader = false;

  @Output() headerToggle = new EventEmitter<void>();
  @Output() bulkConfirm = new EventEmitter<boolean>();
  @Output() bulkCommitNote = new EventEmitter<void>();
  @Output() rowConfirm = new EventEmitter<{ row: AdminReportRow; approve: boolean }>();
  @Output() rowCommitNote = new EventEmitter<AdminReportRow>();
  @Output() loadMore = new EventEmitter<void>();

  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  get titleRowCount(): number | null {
    if (this.titleTable.isLoaded) {
      return this.titleTable.totalCount ?? this.titleTable.rows.length;
    }
    return this.titleTable.rowCount ?? null;
  }

  get hasMoreRows(): boolean {
    const total = this.titleTable.totalCount;
    if (total == null) return false;
    return this.titleTable.rows.length < total;
  }

  get isTitleDisabled(): boolean {
    return this.titleRowCount === 0;
  }

  /** Show bulk confirm when at least one row is not fully approved. */
  get showBulkConfirm(): boolean {
    if (!this.titleTable.isLoaded || !this.titleTable.rows.length) return false;
    return this.titleTable.rows.some((row) => row['_confirmStatus'] !== 'approved');
  }

  /** Show bulk reject when at least one row is approved. */
  get showBulkReject(): boolean {
    if (!this.titleTable.isLoaded || !this.titleTable.rows.length) return false;
    return this.titleTable.rows.some((row) => row['_confirmStatus'] === 'approved');
  }

  onHeaderClick(): void {
    if (this.isTitleDisabled) return;
    this.headerToggle.emit();
  }
}
