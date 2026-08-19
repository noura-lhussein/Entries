import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { ButtonComponent } from '../button/button.component';
import { TranslationService } from '../../services/translation.service';

export type ExportFileFormat = 'excel' | 'word' | 'pdf';

export interface ExportFormatDialogData {
  fullReport?: boolean;
}

export interface ExportFormatDialogResult {
  format: ExportFileFormat;
  from?: string;
  to?: string;
}

@Component({
  selector: 'app-export-format-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatIconModule, ButtonComponent],
  template: `
    <div class="dialog-wrapper" dir="rtl">
      <div class="dialog-header">
        <span class="header-icon"><mat-icon>download</mat-icon></span>
        <div class="header-text">
          <h2>{{ dialogTitle() }}</h2>
          <p class="hint">{{ dialogHint() }}</p>
        </div>
      </div>

      <div class="date-card">
        <div class="date-card-title">
          <mat-icon>event</mat-icon>
          <span>{{ t('reports.date-range') }}</span>
        </div>
        <div class="date-range">
          <label class="date-field">
            <span>
              {{ t('reports.from-date') }}
              <span class="req">*</span>
            </span>
            <input
              type="date"
              [ngModel]="from()"
              (ngModelChange)="from.set($event)"
              [max]="to() || null"
            />
          </label>
          <label class="date-field">
            <span>
              {{ t('reports.to-date') }}
              <span class="req">*</span>
            </span>
            <input
              type="date"
              [ngModel]="to()"
              (ngModelChange)="to.set($event)"
              [min]="from() || null"
            />
          </label>
        </div>
        @if (dateError()) {
          <p class="date-error"><mat-icon>error_outline</mat-icon> {{ dateError() }}</p>
        }
      </div>

      <p class="format-label">{{ t('export-reports.choose-format-label') }}</p>
      <div class="format-actions" [class.is-locked]="!canPick()">
        <button
          type="button"
          class="format-card excel"
          [disabled]="!canPick()"
          (click)="pick('excel')"
        >
          <span class="card-icon"><mat-icon>table_chart</mat-icon></span>
          <span class="card-label">{{ t('export-reports.format-excel') }}</span>
        </button>
        <button
          type="button"
          class="format-card word"
          [disabled]="!canPick()"
          (click)="pick('word')"
        >
          <span class="card-icon"><mat-icon>description</mat-icon></span>
          <span class="card-label">{{ t('export-reports.format-word') }}</span>
        </button>
        <button type="button" class="format-card pdf" [disabled]="!canPick()" (click)="pick('pdf')">
          <span class="card-icon"><mat-icon>picture_as_pdf</mat-icon></span>
          <span class="card-label">{{ t('export-reports.format-pdf') }}</span>
        </button>
      </div>
      @if (!canPick()) {
        <p class="lock-hint"><mat-icon>lock</mat-icon> {{ t('export-reports.pick-date-first') }}</p>
      }

      <div class="footer">
        <app-button variant="ghost" [label]="t('user-data.cancel-button')" (clicked)="cancel()" />
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        --gold: #054239;
        --gold-soft: #b9a779;
        --gold-bg: #f5f0e8;
        --line: #d8d3c9;
        --text: #353233;
        --muted: #6d6768;
        --danger: #c0392b;
      }
      .dialog-wrapper {
        padding: 22px 24px 18px;
        min-width: min(460px, 94vw);
        font-family: inherit;
        color: var(--text);
      }
      .dialog-header {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 18px;
      }
      .header-icon {
        flex: none;
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-soft) 100%);
        box-shadow: 0 6px 14px rgba(5, 66, 57, 0.28);
      }
      .header-icon mat-icon {
        color: #fff;
        font-size: 24px;
        width: 24px;
        height: 24px;
      }
      .header-text {
        flex: 1;
      }
      h2 {
        margin: 0 0 4px;
        font-size: 1.18rem;
        font-weight: 700;
        color: var(--gold);
      }
      .hint {
        margin: 0;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.55;
      }
      .date-card {
        border: 1px solid var(--line);
        background: var(--gold-bg);
        border-radius: 14px;
        padding: 14px 16px 16px;
        margin-bottom: 18px;
      }
      .date-card-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--gold);
        margin-bottom: 12px;
      }
      .date-card-title mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
      .date-range {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      .date-field {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 0.82rem;
        color: #555;
      }
      .date-field .req {
        color: var(--danger);
      }
      .date-field input {
        padding: 9px 11px;
        border: 1px solid var(--line);
        border-radius: 9px;
        font: inherit;
        background: #fff;
        transition:
          border-color 0.15s,
          box-shadow 0.15s;
      }
      .date-field input:focus {
        outline: none;
        border-color: var(--gold-soft);
        box-shadow: 0 0 0 3px rgba(185, 167, 121, 0.25);
      }
      .date-error {
        display: flex;
        align-items: center;
        gap: 5px;
        margin: 10px 0 0;
        color: var(--danger);
        font-size: 0.78rem;
      }
      .date-error mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
      .format-label {
        margin: 0 0 10px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text);
      }
      .format-actions {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
      }
      .format-actions.is-locked {
        opacity: 0.55;
      }
      .format-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding: 18px 12px;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: #fff;
        cursor: pointer;
        transition:
          transform 0.14s ease,
          border-color 0.14s,
          box-shadow 0.14s;
      }
      .format-card:hover:not(:disabled) {
        transform: translateY(-3px);
        border-color: var(--gold-soft);
        box-shadow: 0 8px 18px rgba(5, 66, 57, 0.16);
      }
      .format-card:active:not(:disabled) {
        transform: translateY(-1px);
      }
      .format-card:disabled {
        cursor: not-allowed;
      }
      .card-icon {
        width: 52px;
        height: 52px;
        border-radius: 50%;
        display: grid;
        place-items: center;
      }
      .card-icon mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
      }
      .excel .card-icon {
        background: #e6f4ea;
      }
      .excel .card-icon mat-icon {
        color: #1e7d44;
      }
      .word .card-icon {
        background: #e7eefb;
      }
      .word .card-icon mat-icon {
        color: #2b579a;
      }
      .pdf .card-icon {
        background: #fdeaea;
      }
      .pdf .card-icon mat-icon {
        color: #c0392b;
      }
      .card-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text);
      }
      .lock-hint {
        display: flex;
        align-items: center;
        gap: 5px;
        margin: 12px 0 0;
        color: var(--muted);
        font-size: 0.78rem;
      }
      .lock-hint mat-icon {
        font-size: 15px;
        width: 15px;
        height: 15px;
      }
      .footer {
        display: flex;
        justify-content: flex-end;
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid var(--line);
      }
    `,
  ],
})
export class ExportFormatDialogComponent {
  private dialogRef = inject(
    MatDialogRef<ExportFormatDialogComponent, ExportFormatDialogResult | null>,
  );
  private translation = inject(TranslationService);
  data = inject<ExportFormatDialogData>(MAT_DIALOG_DATA, { optional: true });

  t = (key: string) => this.translation.t(key);

  from = signal('');
  to = signal('');

  /** Both dates required; reversed range is never allowed (all export modes). */
  canPick = computed(() => {
    const from = this.from();
    const to = this.to();
    return !!from && !!to && from <= to;
  });

  dateError = computed(() => {
    const from = this.from();
    const to = this.to();
    if (from && to && from > to) {
      return this.t('export-reports.date-range-invalid');
    }
    return '';
  });

  dialogTitle = () =>
    this.t(
      this.data?.fullReport ? 'export-reports.choose-format-full' : 'export-reports.choose-format',
    );

  dialogHint = () =>
    this.t(
      this.data?.fullReport
        ? 'export-reports.choose-format-full-hint'
        : 'export-reports.choose-format-hint',
    );

  pick(format: ExportFileFormat): void {
    if (!this.canPick()) return;
    this.dialogRef.close({
      format,
      from: this.from(),
      to: this.to(),
    });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
