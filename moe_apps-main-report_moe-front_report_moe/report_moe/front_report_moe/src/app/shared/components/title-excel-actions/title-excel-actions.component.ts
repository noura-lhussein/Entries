import {
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  signal,
  ViewChild,
  ElementRef,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import {
  ExcelImportService,
  type ExcelImportResult,
  type ExcelValidationIssue,
} from '../../../core/services/excel-import.service';
import { TranslationService } from '../../services/translation.service';
import { ToastService } from '../../services/toast.service';
import { ModalComponent } from '../modal/modal.component';

@Component({
  selector: 'app-title-excel-actions',
  standalone: true,
  imports: [CommonModule, MatIconModule, ModalComponent],
  template: `
    @if (titleId && canUseExcel()) {
      <div class="excel-actions">
        <button
          type="button"
          class="excel-btn"
          [disabled]="downloading() || importing() || exporting()"
          (click)="downloadTemplate()"
        >
          <mat-icon aria-hidden="true">download</mat-icon>
          <span>{{ t('builder.download-template') }}</span>
        </button>
        <button
          type="button"
          class="excel-btn"
          [disabled]="downloading() || importing() || exporting()"
          (click)="openExportModal()"
        >
          <mat-icon aria-hidden="true">ios_share</mat-icon>
          <span>{{ t('builder.export-data') }}</span>
        </button>
        <button
          type="button"
          class="excel-btn"
          [disabled]="downloading() || importing() || exporting()"
          (click)="openImportModal()"
        >
          <mat-icon aria-hidden="true">upload_file</mat-icon>
          <span>{{ t('builder.upload-file') }}</span>
        </button>
        <input
          #fileInput
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          class="file-input"
          (change)="onFileSelected($event)"
        />
      </div>

      <app-modal
        [visible]="exportModalVisible()"
        [title]="t('builder.export-data')"
        size="small"
        (close)="closeExportModal()"
      >
        <label class="export-date-label" [attr.for]="'excel-export-date-' + titleId">
          {{ t('builder.export-data-pick-date') }}
        </label>
        <input
          class="export-date-input"
          [id]="'excel-export-date-' + titleId"
          type="date"
          [value]="exportDate()"
          (input)="onExportDateInput($event)"
        />
        <div footer class="modal-footer">
          <button type="button" class="modal-btn ghost" (click)="closeExportModal()">
            {{ t('user-data.cancel-button') }}
          </button>
          <button
            type="button"
            class="modal-btn primary"
            [disabled]="!exportDate() || exporting()"
            (click)="runExport()"
          >
            {{ t('builder.export-data') }}
          </button>
        </div>
      </app-modal>

      <app-modal
        [visible]="importModalVisible()"
        [title]="t('builder.import-excel')"
        size="medium"
        (close)="closeImportModal()"
      >
        <p class="import-hint">
          {{
            requireSubMain
              ? t('builder.import-excel-hint-scoped')
              : t('builder.import-excel-hint-dynamic')
          }}
        </p>

        @if (validationIssues().length) {
          <div class="validation-block">
            <h4 class="validation-title">{{ t('builder.import-schema-title') }}</h4>
            <table class="validation-table">
              <thead>
                <tr>
                  <th>{{ t('builder.import-schema-type') }}</th>
                  <th>{{ t('builder.import-schema-column') }}</th>
                  <th>{{ t('builder.import-schema-message') }}</th>
                </tr>
              </thead>
              <tbody>
                @for (issue of validationIssues(); track issue.kind + issue.column) {
                  <tr [class.row-blocking]="isBlockingIssue(issue)">
                    <td>{{ issueKindLabel(issue.kind) }}</td>
                    <td>{{ issue.column || '—' }}</td>
                    <td>{{ issue.message }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }

        @if (lastResult()) {
          <div class="import-summary">
            <p>
              {{
                t('builder.import-summary')
                  .replace('{imported}', '' + lastResult()!.imported_rows)
                  .replace('{skipped}', '' + lastResult()!.skipped_rows)
              }}
            </p>
            @if (lastResult()!.errors.length) {
              <table class="validation-table row-errors-table">
                <thead>
                  <tr>
                    <th>{{ t('builder.import-error-row').replace('{row}', '#') }}</th>
                    <th>{{ t('builder.import-schema-message') }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (err of lastResult()!.errors; track err.row + err.message) {
                    <tr>
                      <td>{{ err.row }}</td>
                      <td>{{ err.message }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            }
          </div>
        }

        <div footer class="modal-footer">
          <button type="button" class="modal-btn ghost" (click)="closeImportModal()">
            {{ t('user-data.cancel-button') }}
          </button>
          <button
            type="button"
            class="modal-btn secondary"
            [disabled]="!pendingFile() || importing()"
            (click)="runImport(true)"
          >
            {{ t('builder.import-validate') }}
          </button>
          <button
            type="button"
            class="modal-btn primary"
            [disabled]="!pendingFile() || importing() || !canConfirmImport()"
            (click)="runImport(false)"
          >
            {{ t('builder.import-confirm') }}
          </button>
        </div>
      </app-modal>
    }
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './title-excel-actions.component.scss',
})
export class TitleExcelActionsComponent {
  @ViewChild('fileInput') fileInputRef?: ElementRef<HTMLInputElement>;

  private excel = inject(ExcelImportService);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  @Input({ required: true }) titleId!: number;
  @Input({ required: true }) titleName!: string;
  /** When set (data-entry flow), section columns are omitted and this sub is used on import. */
  @Input() subMainId: number | null = null;
  /** Require a selected sub-main before showing download/upload (user data-entry). */
  @Input() requireSubMain = false;
  @Output() imported = new EventEmitter<ExcelImportResult>();

  importing = signal(false);
  downloading = signal(false);
  exporting = signal(false);
  importModalVisible = signal(false);
  exportModalVisible = signal(false);
  exportDate = signal('');
  lastResult = signal<ExcelImportResult | null>(null);
  pendingFile = signal<File | null>(null);
  validatedOk = signal(false);

  validationIssues = signal<ExcelValidationIssue[]>([]);

  canUseExcel(): boolean {
    if (this.requireSubMain) {
      return this.subMainId != null && Number.isFinite(this.subMainId);
    }
    return true;
  }

  downloadTemplate(): void {
    if (!this.titleId || !this.canUseExcel()) return;
    this.downloading.set(true);
    this.excel.downloadTemplate(this.titleId, this.subMainId).subscribe({
      next: (blob) => {
        const safe = (this.titleName || 'template')
          .replace(/[^\w\u0600-\u06FF\-]+/g, '_')
          .slice(0, 40);
        this.excel.saveBlob(blob, `${safe}-template.xlsx`);
        this.toast.success(this.t('builder.export-template-success'));
        this.downloading.set(false);
      },
      error: () => {
        this.toast.error(this.t('builder.export-template-error'));
        this.downloading.set(false);
      },
    });
  }

  openExportModal(): void {
    if (!this.canUseExcel()) {
      this.toast.error(this.t('builder.excel-need-sub-main'));
      return;
    }
    if (!this.exportDate()) {
      this.exportDate.set(new Date().toISOString().slice(0, 10));
    }
    this.exportModalVisible.set(true);
  }

  closeExportModal(): void {
    this.exportModalVisible.set(false);
  }

  onExportDateInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value || '';
    this.exportDate.set(value);
  }

  runExport(): void {
    const date = this.exportDate().trim();
    if (!date || !this.titleId || !this.canUseExcel()) return;
    this.exporting.set(true);
    this.excel.exportData(this.titleId, date, this.subMainId).subscribe({
      next: (blob) => {
        const safe = (this.titleName || 'export')
          .replace(/[^\w\u0600-\u06FF\-]+/g, '_')
          .slice(0, 40);
        this.excel.saveBlob(blob, `${safe}-${date}.xlsx`);
        this.toast.success(this.t('builder.export-data-success'));
        this.exporting.set(false);
        this.closeExportModal();
      },
      error: () => {
        this.toast.error(this.t('builder.export-data-error'));
        this.exporting.set(false);
      },
    });
  }

  canConfirmImport(): boolean {
    const r = this.lastResult();
    const blocking = r?.validation?.blocking ?? false;
    return this.validatedOk() && !!r && !blocking && r.errors.length === 0;
  }

  isBlockingIssue(issue: ExcelValidationIssue): boolean {
    return (
      issue.kind === 'missing_column' ||
      issue.kind === 'wrong_workbook_shape' ||
      issue.kind === 'report_date_confirmed' ||
      issue.kind === 'sheet_unreadable'
    );
  }

  issueKindLabel(kind: string): string {
    const map: Record<string, string> = {
      missing_column: this.t('builder.import-kind-missing'),
      unknown_column: this.t('builder.import-kind-unknown'),
      skipped_attribute: this.t('builder.import-kind-skipped'),
      wrong_workbook_shape: this.t('builder.import-kind-wrong-shape'),
      report_date_confirmed: this.t('builder.import-kind-date-confirmed'),
      report_date_exists: this.t('builder.import-kind-date-exists'),
      entity_unmatched: this.t('builder.import-kind-entity-unmatched'),
      entity_row_incomplete: this.t('builder.import-kind-entity-incomplete'),
      sheet_unreadable: this.t('builder.import-kind-unreadable'),
    };
    return map[kind] ?? kind;
  }

  openImportModal(): void {
    if (!this.canUseExcel()) {
      this.toast.error(this.t('builder.excel-need-sub-main'));
      return;
    }
    this.lastResult.set(null);
    this.pendingFile.set(null);
    this.validatedOk.set(false);
    this.validationIssues.set([]);
    this.fileInputRef?.nativeElement.click();
  }

  closeImportModal(): void {
    this.importModalVisible.set(false);
    this.pendingFile.set(null);
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    this.pendingFile.set(file);
    this.lastResult.set(null);
    this.validatedOk.set(false);
    this.validationIssues.set([]);
    this.importModalVisible.set(true);
  }

  private applyResult(result: ExcelImportResult, dryRun: boolean): void {
    this.lastResult.set(result);
    const issues = result.validation?.issues ?? [];
    this.validationIssues.set(issues);
    if (dryRun) {
      const blocking = result.validation?.blocking ?? false;
      const ok = !blocking && result.errors.length === 0;
      this.validatedOk.set(ok);
    }
  }

  runImport(dryRun: boolean): void {
    const file = this.pendingFile();
    if (!file || !this.titleId || !this.canUseExcel()) return;
    this.importing.set(true);
    this.excel.importFile(this.titleId, file, dryRun, this.subMainId).subscribe({
      next: (result) => {
        this.applyResult(result, dryRun);
        this.importing.set(false);
        if (dryRun) {
          const blocking = result.validation?.blocking ?? false;
          if (blocking || result.errors.length) {
            this.toast.error(this.t('builder.import-validation-failed'));
          } else {
            this.toast.success(this.t('builder.import-validation-ok'));
          }
          return;
        }
        if (result.errors.length) {
          this.toast.error(this.t('builder.import-partial-error'));
        } else {
          this.toast.success(this.t('builder.import-success'));
          this.imported.emit(result);
          this.closeImportModal();
        }
      },
      error: () => {
        this.toast.error(this.t('builder.import-error'));
        this.importing.set(false);
      },
    });
  }
}
