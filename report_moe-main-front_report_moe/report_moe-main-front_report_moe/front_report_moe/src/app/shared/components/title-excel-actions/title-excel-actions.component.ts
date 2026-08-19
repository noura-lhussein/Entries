import {
  Component,
  Input,
  Output,
  EventEmitter,
  inject,
  signal,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
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
  imports: [CommonModule, MatIconModule, MatTooltipModule, ModalComponent],
  template: `
    @if (titleId) {
      <div class="excel-actions">
        <button
          type="button"
          class="excel-icon-btn"
          [matTooltip]="t('builder.import-excel')"
          [disabled]="importing()"
          (click)="openImportModal()"
        >
          <mat-icon>file_download</mat-icon>
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
        [visible]="importModalVisible()"
        [title]="t('builder.import-excel')"
        size="medium"
        (close)="closeImportModal()"
      >
        <p class="import-hint">{{ t('builder.import-excel-hint-dynamic') }}</p>

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
  @Output() imported = new EventEmitter<ExcelImportResult>();

  importing = signal(false);
  importModalVisible = signal(false);
  lastResult = signal<ExcelImportResult | null>(null);
  pendingFile = signal<File | null>(null);
  validatedOk = signal(false);

  validationIssues = signal<ExcelValidationIssue[]>([]);

  canConfirmImport(): boolean {
    const r = this.lastResult();
    const blocking = r?.validation?.blocking ?? false;
    return this.validatedOk() && !!r && !blocking && r.errors.length === 0;
  }

  isBlockingIssue(issue: ExcelValidationIssue): boolean {
    return issue.kind === 'missing_column';
  }

  issueKindLabel(kind: string): string {
    const map: Record<string, string> = {
      missing_column: this.t('builder.import-kind-missing'),
      unknown_column: this.t('builder.import-kind-unknown'),
      skipped_attribute: this.t('builder.import-kind-skipped'),
    };
    return map[kind] ?? kind;
  }

  openImportModal(): void {
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
    if (!file || !this.titleId) return;
    this.importing.set(true);
    this.excel.importFile(this.titleId, file, dryRun).subscribe({
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
