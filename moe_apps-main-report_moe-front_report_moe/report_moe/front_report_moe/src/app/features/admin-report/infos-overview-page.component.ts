import { Component, ChangeDetectionStrategy } from '@angular/core';
import { AdminReportComponent } from './admin-report.component';

/** Submitted data overview route — thin wrapper around the shared report shell. */
@Component({
  selector: 'app-infos-overview-page',
  standalone: true,
  imports: [AdminReportComponent],
  changeDetection: ChangeDetectionStrategy.Eager,
  template: `<app-admin-report pageMode="overview" />`,
})
export class InfosOverviewPageComponent {}
