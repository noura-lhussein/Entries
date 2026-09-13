import { Component, Input, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-form-section-title',
  standalone: true,
  template: `
    <div class="form-section-heading">
      <span class="form-section-accent" aria-hidden="true"></span>
      <h2 class="form-section-title">{{ title }}</h2>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-section-title.component.scss',
})
export class FormSectionTitleComponent {
  @Input({ required: true }) title!: string;
}
