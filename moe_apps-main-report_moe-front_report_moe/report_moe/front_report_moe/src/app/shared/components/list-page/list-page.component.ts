import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PageHeaderComponent } from '../page-header/page-header.component';
import { FilterPanelComponent } from '../filter-panel/filter-panel.component';
import { DataTableComponent } from '../data-table/data-table.component';
import { PaginationComponent } from '../pagination/pagination.component';
import { EmptyStateComponent } from '../empty-state/empty-state.component';
import { PageLoaderComponent } from '../page-loader/page-loader.component';
import { PageHeaderAction } from '../page-header/page-header.component';
import { FilterGroup } from '../filter-panel/filter-panel.component';
import {
  TableColumn,
  TableAction,
  type TableScrollConfig,
} from '../data-table/data-table.component';

export interface ListPageConfig {
  title: string;
  description?: string;
  headerAction?: PageHeaderAction;
  headerActions?: PageHeaderAction[];
  searchPlaceholder?: string;
  filterGroups?: FilterGroup[];
  activeFilters?: Record<string, any>;
  columns: TableColumn[];
  data: any[];
  actions: TableAction[];
  loading: boolean;
  currentPage: number;
  totalPages: number;
  totalItems?: number;
  pageSize?: number;
  emptyMessage?: string;
  tableScroll?: TableScrollConfig;
}

@Component({
  selector: 'app-list-page',
  standalone: true,
  imports: [
    CommonModule,
    PageHeaderComponent,
    FilterPanelComponent,
    DataTableComponent,
    PaginationComponent,
    EmptyStateComponent,
    PageLoaderComponent,
  ],
  template: `
    <div class="page-container">
      <div class="list-chrome">
        <app-page-header
          [title]="config.title"
          [description]="config.description"
          [action]="config.headerAction"
          [actions]="config.headerActions || []"
        ></app-page-header>

        <app-filter-panel
          *ngIf="config.searchPlaceholder || config.filterGroups?.length"
          [searchPlaceholder]="config.searchPlaceholder || ''"
          [filterGroups]="config.filterGroups || []"
          [activeFilters]="config.activeFilters || {}"
          (search)="onSearch.emit($event)"
          (filterChange)="onFilterChange.emit($event)"
          (clearFilter)="onClearFilter.emit($event)"
          (clearFilters)="onClearFilters.emit()"
        ></app-filter-panel>
      </div>

      <div class="list-body">
        <app-page-loader *ngIf="config.loading" />

        <app-empty-state
          *ngIf="!config.loading && config.data.length === 0"
          icon="inbox"
          [message]="config.emptyMessage || 'لا توجد بيانات'"
        />

        <app-data-table
          *ngIf="!config.loading && config.data.length > 0"
          [columns]="config.columns"
          [data]="config.data"
          [actions]="config.actions"
          [scroll]="config.tableScroll || defaultTableScroll"
        ></app-data-table>
      </div>

      <app-pagination
        [currentPage]="config.currentPage"
        [totalPages]="config.totalPages"
        [totalItems]="config.totalItems || 0"
        [pageSize]="config.pageSize || 0"
        (previous)="onPrevious.emit()"
        (next)="onNext.emit()"
        (goToPage)="onGoToPage.emit($event)"
      ></app-pagination>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './list-page.component.scss',
})
export class ListPageComponent {
  /** Table fills the available page height; scrolls only when rows overflow. */
  readonly defaultTableScroll: TableScrollConfig = {
    vertical: 'auto',
    maxHeight: '100%',
  };

  @Input() config!: ListPageConfig;
  @Output() onSearch = new EventEmitter<string>();
  @Output() onFilterChange = new EventEmitter<{ key: string; value: any }>();
  @Output() onClearFilter = new EventEmitter<string>();
  @Output() onClearFilters = new EventEmitter<void>();
  @Output() onPrevious = new EventEmitter<void>();
  @Output() onNext = new EventEmitter<void>();
  @Output() onGoToPage = new EventEmitter<number>();
}
