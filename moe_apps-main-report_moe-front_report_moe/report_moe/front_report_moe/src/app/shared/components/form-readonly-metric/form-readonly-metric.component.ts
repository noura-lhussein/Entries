import { CommonModule } from '@angular/common';
import { Component, Input, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-form-readonly-metric',
  standalone: true,
  imports: [CommonModule],
  template: `
    <p class="readonly-metric" [class.span-full]="spanFull">
      <span class="readonly-metric-label">{{ label }}:</span>
      <span class="readonly-metric-value">{{ value }}</span>
      <span *ngIf="hint" class="readonly-metric-hint">{{ hint }}</span>
    </p>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-readonly-metric.component.scss',
})
export class FormReadonlyMetricComponent {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) value!: string;
  @Input() hint = '';
  @Input() spanFull = true;
}
