import { Component, Inject, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { TranslationService } from '../../services/translation.service';
import { LanguageService } from '../../services/language.service';

export interface AssignedUserRow {
  id: number;
  full_name: string;
  username: string;
  email: string;
  is_active: boolean;
  parent_name?: string | null;
}

export interface AssignedUsersDialogData {
  contextLabel: string;
  users: AssignedUserRow[];
}

@Component({
  selector: 'app-assigned-users-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatIconModule],
  template: `
    <div class="dialog-wrapper" [attr.dir]="language.lang() === 'ar' ? 'rtl' : 'ltr'">
      <div class="dialog-header">
        <div class="header-text">
          <div class="icon-circle">
            <mat-icon>group</mat-icon>
          </div>
          <div class="titles-block">
            <h2>{{ t('assigned-users.title') }}</h2>
            <p class="context-sub">{{ data.contextLabel }}</p>
          </div>
        </div>
        <button
          type="button"
          class="close-btn"
          (click)="close()"
          [attr.aria-label]="t('users.info-dialog.close')"
        >
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-body-scroll">
        <p class="count-line" *ngIf="data.users.length">
          {{ t('assigned-users.count') }}: {{ data.users.length }}
        </p>

        <div *ngIf="data.users.length === 0" class="empty">
          {{ t('assigned-users.empty') }}
        </div>

        <ul *ngIf="data.users.length" class="user-list">
          <li *ngFor="let user of data.users" class="user-row">
            <div class="user-main">
              <span class="name">{{ user.full_name || user.username }}</span>
              <span class="email">{{ user.email || user.username }}</span>
            </div>
            <div class="user-meta">
              <span
                class="pill"
                [class.pill-active]="user.is_active"
                [class.pill-inactive]="!user.is_active"
              >
                {{
                  user.is_active
                    ? t('users.info-dialog.active')
                    : t('users.info-dialog.inactive')
                }}
              </span>
              <span class="parent" *ngIf="user.parent_name">
                {{ t('users.parent-name') }}: {{ user.parent_name }}
              </span>
            </div>
          </li>
        </ul>
      </div>

      <div class="dialog-footer">
        <button type="button" class="close-action" (click)="close()">
          {{ t('users.info-dialog.close') }}
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      .dialog-wrapper {
        display: flex;
        flex-direction: column;
        max-height: min(80vh, 640px);
        background: #fff;
        font-family: inherit;
      }
      .dialog-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 18px 20px 12px;
        border-bottom: 1px solid #e5e7eb;
      }
      .header-text {
        display: flex;
        gap: 12px;
        align-items: center;
        min-width: 0;
      }
      .icon-circle {
        width: 40px;
        height: 40px;
        border-radius: 999px;
        background: rgba(146, 118, 46, 0.12);
        color: #054239;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      .titles-block h2 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
      }
      .context-sub {
        margin: 2px 0 0;
        font-size: 0.85rem;
        color: #6b7280;
        word-break: break-word;
      }
      .close-btn {
        border: none;
        background: transparent;
        color: #6b7280;
        cursor: pointer;
        padding: 4px;
        border-radius: 8px;
      }
      .close-btn:hover {
        background: #f3f4f6;
        color: #111827;
      }
      .dialog-body-scroll {
        padding: 14px 20px;
        overflow: auto;
        flex: 1;
      }
      .count-line {
        margin: 0 0 10px;
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 600;
      }
      .empty {
        padding: 28px 12px;
        text-align: center;
        color: #9ca3af;
        font-size: 0.9rem;
      }
      .user-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .user-row {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 10px 12px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        background: #fafafa;
      }
      .user-main {
        display: flex;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
      }
      .name {
        font-weight: 600;
        color: #111827;
        font-size: 0.95rem;
      }
      .email {
        font-size: 0.8rem;
        color: #6b7280;
        word-break: break-all;
      }
      .user-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 12px;
        align-items: center;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
      }
      .pill-active {
        background: #dcfce7;
        color: #166534;
      }
      .pill-inactive {
        background: #f3f4f6;
        color: #6b7280;
      }
      .parent {
        font-size: 0.78rem;
        color: #6b7280;
      }
      .dialog-footer {
        padding: 12px 20px 16px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        justify-content: flex-end;
      }
      .close-action {
        border: 1px solid #d1d5db;
        background: #fff;
        color: #374151;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
        cursor: pointer;
      }
      .close-action:hover {
        background: #f9fafb;
      }
    `,
  ],
})
export class AssignedUsersDialogComponent {
  private dialogRef = inject(MatDialogRef<AssignedUsersDialogComponent>);
  private translation = inject(TranslationService);
  language = inject(LanguageService);

  constructor(@Inject(MAT_DIALOG_DATA) public data: AssignedUsersDialogData) {}

  t = (key: string) => this.translation.t(key);

  close(): void {
    this.dialogRef.close();
  }
}
