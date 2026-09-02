import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ButtonComponent } from '../button/button.component';

export interface DialogConfig {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  icon?: string;
  type?: 'info' | 'warning' | 'error' | 'success';
  size?: 'sm' | 'md' | 'lg';
  showCancel?: boolean;
  closeButton?: boolean;
}

@Component({
  selector: 'app-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule, ButtonComponent],
  template: `
    <div class="dialog-wrapper" [class]="'dialog-' + config.type" dir="rtl">
      <div class="dialog-header">
        <div class="header-content">
          <div class="icon-circle" *ngIf="config.icon">
            <mat-icon>{{ config.icon }}</mat-icon>
          </div>
          <h2>{{ config.title }}</h2>
        </div>
        <button
          *ngIf="config.closeButton !== false"
          type="button"
          class="close-button"
          (click)="onCancel()"
          aria-label="إغلاق"
        >
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-body">
        <p>{{ config.message }}</p>
        <ng-content></ng-content>
      </div>

      <div class="dialog-footer">
        <app-button
          *ngIf="config.showCancel !== false"
          [label]="config.cancelLabel || 'إلغاء'"
          variant="ghost"
          (clicked)="onCancel()"
        ></app-button>
        <app-button
          [label]="config.confirmLabel || 'تأكيد'"
          [variant]="getButtonVariant()"
          (clicked)="onConfirm()"
        ></app-button>
      </div>
    </div>
  `,
  styleUrl: './dialog.component.scss',
})
export class DialogComponent {
  constructor(
    public dialogRef: MatDialogRef<DialogComponent>,
    @Inject(MAT_DIALOG_DATA) public config: DialogConfig,
  ) {}

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  getButtonVariant(): 'primary' | 'danger' | 'success' {
    switch (this.config.type) {
      case 'error':
        return 'danger';
      case 'success':
        return 'success';
      default:
        return 'primary';
    }
  }
}
