import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-form-actions-bar',
  standalone: true,
  template: `<div class="form-actions-bar"><ng-content /></div>`,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-actions-bar.component.scss',
})
export class FormActionsBarComponent {}
