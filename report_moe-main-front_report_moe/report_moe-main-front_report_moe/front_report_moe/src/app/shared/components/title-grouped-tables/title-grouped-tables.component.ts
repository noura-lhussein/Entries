import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import {
  TableComponent,
  type TableAction,
  type TableRow,
  type TableScrollConfig,
} from '../table/table.component';
import type { TitleGroupedBlock } from '../../models/title-grouped-table.model';
import { InfiniteScrollDirective } from '../../directives/infinite-scroll.directive';
import { INFO_TABLE_SCROLL } from '../../utils/info-table-scroll';

@Component({
  selector: 'app-title-grouped-tables',
  standalone: true,
  imports: [CommonModule, MatIconModule, TableComponent, InfiniteScrollDirective],
  templateUrl: './title-grouped-tables.component.html',
  styleUrl: './title-grouped-tables.component.scss',
})
export class TitleGroupedTablesComponent {
  @Input({ required: true }) groups: TitleGroupedBlock[] = [];
  @Input() actions: TableAction[] = [];
  @Input() emptyMessage = '';
  @Input() hasMore = false;
  @Input() loadingMore = false;
  /** Scrollport for infinite-scroll sentinel (default: main.content). */
  @Input() scrollRoot = 'main.content';
  /** Per-table scroll; defaults to shared info-table cap. */
  @Input() tableScroll: TableScrollConfig = INFO_TABLE_SCROLL;
  /** Hide the outer title heading (useful when parent already shows the title). */
  @Input() hideTitleHeaders = false;

  @Output() actionClicked = new EventEmitter<{
    type: string;
    row: TableRow;
    origin?: DOMRect;
  }>();
  @Output() loadMore = new EventEmitter<void>();

  trackByTitleId(_index: number, group: TitleGroupedBlock): string {
    return String(group.titleId ?? 'none');
  }

  trackBySubMainId(_index: number, slice: { subMainId: number | null }): string {
    return String(slice.subMainId ?? 'none');
  }

  onAction(event: { type: string; row: TableRow; origin?: DOMRect }): void {
    this.actionClicked.emit(event);
  }

  sliceRowCount(group: TitleGroupedBlock): number {
    return group.subMainSlices.reduce((n, s) => n + s.rows.length, 0);
  }
}
