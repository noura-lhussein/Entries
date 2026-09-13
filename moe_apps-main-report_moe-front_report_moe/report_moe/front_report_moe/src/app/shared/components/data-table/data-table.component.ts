import { Component, Input, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { TranslationService } from '../../services/translation.service';
import {
  type TableScrollConfig,
  columnSizingStyle,
  tableScrollClasses,
  tableScrollStyle,
} from '../table/table-scroll.config';

export type { TableScrollConfig } from '../table/table-scroll.config';

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  minWidth?: string;
  maxWidth?: string;
  type?:
    | 'text'
    | 'boolean'
    | 'boolean-icon'
    | 'status'
    | 'badge'
    | 'code'
    | 'stacked'
    | 'project-status'
    | 'progress-percent';
  /** Secondary line for `stacked` rows (e.g. project code under name). */
  subtitleKey?: string;
  /** Display field for `project-status` when different from `key`. */
  labelKey?: string;
  align?: 'start' | 'center';
  trueLabel?: string;
  falseLabel?: string;
}

export interface TableAction {
  icon: string;
  label: string;
  action: (id: number) => void;
  show?: (item: any) => boolean;
}

@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatMenuModule],
  template: `
    <div class="table-wrapper">
      <div class="table-scroll" [ngClass]="scrollClasses" [ngStyle]="scrollStyles">
        <table class="table">
          <thead>
            <tr>
              <th
                *ngFor="let col of columns"
                [ngStyle]="columnStyle(col)"
                [class.sortable]="col.sortable"
                [class.align-start]="col.align === 'start'"
              >
                <div class="th-content" *ngIf="col.sortable">
                  <span>{{ col.label }}</span>
                  <mat-icon class="sort-icon">unfold_more</mat-icon>
                </div>
                <span *ngIf="!col.sortable">{{ col.label }}</span>
              </th>
              <th *ngIf="actions.length > 0">{{ translation.t('table.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let item of data">
              <td
                *ngFor="let col of columns"
                [ngStyle]="columnStyle(col)"
                [class.align-start]="col.align === 'start'"
              >
                <ng-container [ngSwitch]="col.type">
                  <!-- boolean badge -->
                  <span
                    *ngSwitchCase="'boolean'"
                    class="badge"
                    [class.badge-true]="item[col.key]"
                    [class.badge-false]="!item[col.key]"
                  >
                    {{ item[col.key] ? col.trueLabel || 'مفعّل' : col.falseLabel || 'غير مفعّل' }}
                  </span>

                  <!-- status badge (submitted/draft/approved/rejected) -->
                  <span
                    *ngSwitchCase="'status'"
                    class="badge"
                    [ngClass]="'badge-status-' + item[col.key]"
                  >
                    {{ getStatusLabel(item[col.key]) }}
                  </span>

                  <!-- boolean as icon -->
                  <mat-icon
                    *ngSwitchCase="'boolean-icon'"
                    class="bool-icon"
                    [class.bool-true]="item[col.key]"
                    [class.bool-false]="!item[col.key]"
                    [title]="
                      item[col.key] ? col.trueLabel || 'مفعّل' : col.falseLabel || 'غير مفعّل'
                    "
                  >
                    {{ item[col.key] ? 'check_circle' : 'cancel' }}
                  </mat-icon>

                  <!-- monospace code badge -->
                  <span *ngSwitchCase="'code'" class="code-badge code-badge--wrap">
                    {{ item[col.key] || '—' }}
                  </span>

                  <!-- primary title + monospace subtitle (e.g. project name + code) -->
                  <div
                    *ngSwitchCase="'stacked'"
                    class="cell-stacked"
                    [class.cell-stacked--start]="col.align === 'start'"
                  >
                    <span class="cell-primary">{{ item[col.key] || '—' }}</span>
                    <code *ngIf="col.subtitleKey && item[col.subtitleKey]" class="cell-code">{{
                      item[col.subtitleKey]
                    }}</code>
                  </div>

                  <!-- project lifecycle status -->
                  <span
                    *ngSwitchCase="'project-status'"
                    class="badge project-status-badge"
                    [ngClass]="'project-status-' + item[col.key]"
                  >
                    {{ (col.labelKey ? item[col.labelKey] : item[col.key]) || '—' }}
                  </span>

                  <!-- numeric percent with mini progress bar -->
                  <div
                    *ngSwitchCase="'progress-percent'"
                    class="cell-progress"
                    [class.cell-progress--over]="progressPercentOver(item[col.key])"
                  >
                    <span class="cell-progress-value">{{
                      progressPercentLabel(item[col.key])
                    }}</span>
                    <div class="cell-progress-track">
                      <div
                        class="cell-progress-fill"
                        [style.width.%]="progressPercentWidth(item[col.key])"
                      ></div>
                    </div>
                  </div>

                  <!-- default text -->
                  <span *ngSwitchDefault>{{ item[col.key] ?? '-' }}</span>
                </ng-container>
              </td>
              <td *ngIf="actions.length > 0" class="actions">
                <button
                  *ngFor="let action of getVisibleActions(item)"
                  class="action-icon-btn"
                  [title]="action.label"
                  (click)="action.action(item.id)"
                >
                  <mat-icon>{{ action.icon }}</mat-icon>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent {
  translation = inject(TranslationService);

  @Input() columns: TableColumn[] = [];
  @Input() data: any[] = [];
  @Input() actions: TableAction[] = [];
  @Input() scroll: TableScrollConfig = {};

  get scrollClasses(): Record<string, boolean> {
    return tableScrollClasses(this.scroll);
  }

  get scrollStyles(): Record<string, string> {
    return tableScrollStyle(this.scroll);
  }

  columnStyle(column: TableColumn): Record<string, string | undefined> {
    return columnSizingStyle(column);
  }

  getVisibleActions(item: any): TableAction[] {
    return this.actions.filter((action) => !action.show || action.show(item));
  }

  getStatusLabel(status: string | undefined): string {
    const labels: Record<string, string> = {
      submitted: 'مقدم',
      draft: 'مسودة',
      approved: 'موافق عليه',
      rejected: 'مرفوض',
    };
    return labels[status ?? ''] ?? status ?? '-';
  }

  progressPercentLabel(value: unknown): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return '—';
    const rounded = Math.round(parsed * 10) / 10;
    return `${rounded}%`;
  }

  progressPercentWidth(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return 0;
    return Math.min(100, Math.max(0, parsed));
  }

  progressPercentOver(value: unknown): boolean {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 100;
  }
}
