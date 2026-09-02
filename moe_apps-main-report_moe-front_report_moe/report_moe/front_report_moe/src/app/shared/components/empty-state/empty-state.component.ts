import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="empty-state" [class.compact]="size === 'compact'">
      <mat-icon *ngIf="icon" [class.spin]="spinning">{{ icon }}</mat-icon>
      <p *ngIf="message" class="message">{{ message }}</p>
    </div>
  `,
  styleUrl: './empty-state.component.scss',
})
export class EmptyStateComponent {
  @Input() icon = '';
  @Input() message = '';
  @Input() size: 'normal' | 'compact' = 'normal';
  @Input() spinning = false;
}
