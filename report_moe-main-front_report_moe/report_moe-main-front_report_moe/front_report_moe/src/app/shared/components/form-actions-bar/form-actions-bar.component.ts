import { Component } from '@angular/core';

@Component({
  selector: 'app-form-actions-bar',
  standalone: true,
  template: `<div class="form-actions-bar"><ng-content /></div>`,
  styleUrl: './form-actions-bar.component.scss',
})
export class FormActionsBarComponent {}
