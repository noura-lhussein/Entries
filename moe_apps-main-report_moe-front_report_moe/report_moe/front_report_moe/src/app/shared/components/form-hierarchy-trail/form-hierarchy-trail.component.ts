import { CommonModule } from '@angular/common';
import { Component, Input, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-form-hierarchy-trail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="hierarchy-trail" *ngIf="segments.length">
      <span *ngIf="label" class="hierarchy-label">{{ label }}</span>
      <ol class="hierarchy-list" [attr.aria-label]="label || null">
        <li
          *ngFor="let segment of segments; let last = last"
          class="hierarchy-item"
          [class.is-leaf]="last"
        >
          <span class="hierarchy-segment">{{ segment }}</span>
          <span *ngIf="!last" class="hierarchy-separator" aria-hidden="true">›</span>
        </li>
      </ol>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './form-hierarchy-trail.component.scss',
})
export class FormHierarchyTrailComponent {
  @Input() label = '';
  @Input() segments: string[] = [];
}
