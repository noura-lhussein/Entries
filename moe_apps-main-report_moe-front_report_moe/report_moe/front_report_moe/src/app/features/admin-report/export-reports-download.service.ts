import { Injectable, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ApiService, type ApiParams } from '../../core/services/api.service';
import { ExcelImportService } from '../../core/services/excel-import.service';
import {
  ExportFormatDialogComponent,
  type ExportFileFormat,
  type ExportFormatDialogResult,
} from '../../shared/components/export-format-dialog/export-format-dialog.component';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { parseFilterIds, serializeFilterIds } from '../../shared/utils/filter-params';
import type { ExportDownloadContext } from './export-reports-download.types';

/**
 * Export-reports route only: format dialog + blob download against /export-reports/.
 * Provided by ExportReportsPageComponent; not used on admin or overview routes.
 */
@Injectable()
export class ExportReportsDownloadService {
  private api = inject(ApiService);
  private dialog = inject(MatDialog);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private excelImport = inject(ExcelImportService);

  readonly downloading = signal(false);

  t = (key: string) => this.translation.t(key);

  prompt(ctx: ExportDownloadContext, fullReport = false): void {
    if (!fullReport && !ctx.hasScope) {
      this.toast.error(this.t('export-reports.select-scope-first'));
      return;
    }
    if (this.downloading()) return;

    const ref = this.dialog.open(ExportFormatDialogComponent, {
      width: 'min(460px, 94vw)',
      disableClose: false,
      hasBackdrop: true,
      backdropClass: 'export-dialog-backdrop',
      panelClass: 'export-dialog-panel',
      data: { fullReport },
    });

    ref.afterClosed().subscribe((res: ExportFormatDialogResult | null | undefined) => {
      if (res?.format) {
        this.download(res.format, ctx, fullReport, res.from, res.to);
      }
    });
  }

  private buildParams(
    format: ExportFileFormat,
    ctx: ExportDownloadContext,
    fullReport: boolean,
    dateFrom?: string,
    dateTo?: string,
  ): ApiParams {
    if (fullReport) {
      const result: ApiParams = {
        export_format: format,
        export_scope: 'full',
      };
      const af = ctx.scope.activeFilters;
      const userIds = parseFilterIds(af['user']);
      const cityIds = parseFilterIds(af['city_id']);
      const districtIds = parseFilterIds(af['district_id']);
      const from = dateFrom ?? af['from'];
      const to = dateTo ?? af['to'];
      if (userIds.length) result['user'] = serializeFilterIds(userIds);
      if (districtIds.length) {
        result['district_id'] = serializeFilterIds(districtIds);
      } else if (cityIds.length) {
        result['city_id'] = serializeFilterIds(cityIds);
      }
      if (from) result['from'] = String(from);
      if (to) result['to'] = String(to);
      return result;
    }

    const params = new URLSearchParams(ctx.scope.scopedInfoQuery);
    const result: ApiParams = { export_format: format };
    params.forEach((value, key) => {
      if (key === 'page_size' || key === 'page') return;
      result[key] = value;
    });
    if (dateFrom) result['from'] = dateFrom;
    if (dateTo) result['to'] = dateTo;
    return result;
  }

  private download(
    format: ExportFileFormat,
    ctx: ExportDownloadContext,
    fullReport: boolean,
    dateFrom?: string,
    dateTo?: string,
  ): void {
    this.downloading.set(true);
    this.api
      .getBlob('/export-reports/', this.buildParams(format, ctx, fullReport, dateFrom, dateTo))
      .subscribe({
        next: (blob) => {
          if (blob.type.includes('application/json')) {
            void this.handleError(blob);
            return;
          }
          const ext = format === 'excel' ? 'xlsx' : format === 'word' ? 'docx' : 'pdf';
          const stamp = new Date().toISOString().slice(0, 10);
          const prefix = fullReport ? 'full-report' : 'export-reports';
          this.excelImport.saveBlob(blob, `${prefix}-${stamp}.${ext}`);
          this.toast.success(this.t('export-reports.download-success'));
          this.downloading.set(false);
        },
        error: (err) => {
          void this.handleError(err?.error);
        },
      });
  }

  private async handleError(body: unknown): Promise<void> {
    let message = this.t('export-reports.download-error');
    if (body instanceof Blob) {
      try {
        const text = await body.text();
        if (text.trim().startsWith('{')) {
          const parsed = JSON.parse(text) as { detail?: string };
          if (parsed.detail) message = parsed.detail;
        } else if (text.trim()) {
          message = text.trim().slice(0, 200);
        }
      } catch {
        /* keep default message */
      }
    } else if (typeof body === 'string' && body.trim()) {
      message = body.trim().slice(0, 200);
    } else if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail?: string }).detail;
      if (detail) message = detail;
    }
    this.toast.error(message);
    this.downloading.set(false);
  }
}
