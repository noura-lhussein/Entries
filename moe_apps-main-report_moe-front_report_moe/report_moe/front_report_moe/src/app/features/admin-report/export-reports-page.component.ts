import { Component } from '@angular/core';
import { AdminReportComponent } from './admin-report.component';
import { ExportReportsDownloadService } from './export-reports-download.service';

/** Export reports route — shell + scoped download service (dialog / blob). */
@Component({
  selector: 'app-export-reports-page',
  standalone: true,
  imports: [AdminReportComponent],
  providers: [ExportReportsDownloadService],
  template: `<app-admin-report pageMode="export" />`,
})
export class ExportReportsPageComponent {}
