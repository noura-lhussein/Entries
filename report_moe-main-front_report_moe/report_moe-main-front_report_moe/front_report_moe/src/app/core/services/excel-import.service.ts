import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ExcelValidationIssue {
  kind: string;
  column: string;
  message: string;
}

export interface ExcelImportValidation {
  blocking: boolean;
  expected_columns: string[];
  found_columns: string[];
  missing_columns: string[];
  unknown_columns: string[];
  issues: ExcelValidationIssue[];
}

export interface ExcelImportResult {
  imported_rows: number;
  skipped_rows: number;
  errors: { row: number; message: string }[];
  dry_run?: boolean;
  validation?: ExcelImportValidation;
}

@Injectable({ providedIn: 'root' })
export class ExcelImportService {
  private http = inject(HttpClient);
  private base = environment.apiUrl.replace(/\/$/, '');

  private titleUrl(titleId: number, suffix: string): string {
    return `${this.base}/titles/${titleId}/${suffix}/`;
  }

  downloadTemplate(titleId: number): Observable<Blob> {
    return this.http.get(this.titleUrl(titleId, 'excel-template'), {
      responseType: 'blob',
    });
  }

  importFile(titleId: number, file: File, dryRun = false): Observable<ExcelImportResult> {
    const form = new FormData();
    form.append('file', file, file.name);
    let params = new HttpParams();
    if (dryRun) {
      params = params.set('dry_run', 'true');
    }
    return this.http.post<ExcelImportResult>(this.titleUrl(titleId, 'excel-import'), form, {
      params,
    });
  }

  saveBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}
