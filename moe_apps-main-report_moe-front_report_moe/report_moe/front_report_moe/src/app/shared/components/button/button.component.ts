import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success' | 'ghost' | 'link' | 'warning';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <button
      [type]="type"
      [disabled]="disabled || loading"
      [title]="title || null"
      [class]="buttonClasses"
      (click)="onClick()"
    >
      <span *ngIf="loading" class="spinner" aria-hidden="true"></span>
      <mat-icon *ngIf="icon && !loading" class="btn-icon">{{ icon }}</mat-icon>
      <span class="label" *ngIf="!iconOnly || !icon">{{ label }}</span>
    </button>
  `,
  styleUrl: './button.component.scss',
})
export class ButtonComponent {
  @Input() label = 'Button';
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() icon: string | null | undefined = undefined;
  @Input() iconOnly = false;
  @Input() title = '';
  @Input() active = false;
  @Input() disabled = false;
  @Input() loading = false;
  @Input() type: 'button' | 'submit' | 'reset' = 'button';
  @Output() clicked = new EventEmitter<void>();

  get buttonClasses(): string {
    const parts = ['btn', `btn-${this.variant}`, `size-${this.size}`];
    if (this.iconOnly && this.icon) parts.push('icon-only');
    if (this.active && this.variant === 'ghost') parts.push('active');
    return parts.join(' ');
  }

  onClick(): void {
    if (!this.disabled && !this.loading) {
      this.clicked.emit();
    }
  }
}
