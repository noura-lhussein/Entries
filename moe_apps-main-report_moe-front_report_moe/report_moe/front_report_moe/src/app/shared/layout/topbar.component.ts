import {
  Component,
  EventEmitter,
  HostListener,
  Output,
  computed,
  inject,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { LanguageService } from '../services/language.service';
import { TranslationService } from '../services/translation.service';
import { DialogService } from '../services/dialog.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, MatIconModule],
  template: `
    <header class="topbar">
      <button
        type="button"
        class="icon-btn"
        (click)="toggleSidebar.emit()"
        [attr.aria-label]="t('topbar.toggle-sidebar')"
      >
        <mat-icon>menu</mat-icon>
      </button>

      <div class="actions">
        <button type="button" class="lang-btn" (click)="lang.toggle()">
          <mat-icon>language</mat-icon>
          <span>{{ lang.lang() === 'en' ? 'EN' : 'AR' }}</span>
        </button>

        <button type="button" class="icon-btn notif" [attr.aria-label]="t('topbar.notifications')">
          <mat-icon>notifications</mat-icon>
          <span class="badge">0</span>
        </button>

        <div class="user-menu" (click)="$event.stopPropagation()">
          <button
            type="button"
            class="avatar-btn"
            (click)="menuOpen = !menuOpen"
            aria-haspopup="true"
            [attr.aria-expanded]="menuOpen"
          >
            <span class="avatar">{{ initials() }}</span>
          </button>
          <div class="dropdown" *ngIf="menuOpen">
            <div class="user-info">
              <div class="user-name">{{ auth.currentUser()?.full_name }}</div>
              <div class="user-email">{{ auth.currentUser()?.email }}</div>
            </div>
            <div class="dropdown-divider"></div>
            <a routerLink="/profile" class="dropdown-item" (click)="menuOpen = false">
              <mat-icon>person</mat-icon>
              <span>{{ t('sidebar.profile') }}</span>
            </a>
            <button type="button" class="dropdown-item danger" (click)="onLogout()">
              <mat-icon>logout</mat-icon>
              <span>{{ t('sidebar.logout') }}</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './topbar.component.scss',
})
export class TopbarComponent {
  @Output() toggleSidebar = new EventEmitter<void>();

  auth = inject(AuthService);
  lang = inject(LanguageService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  query = '';
  menuOpen = false;

  initials = computed(() => {
    const u = this.auth.currentUser();
    if (!u) return '?';
    const source = (u.full_name || u.username || '').trim();
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return source.slice(0, 2).toUpperCase();
  });

  private dialog = inject(DialogService);

  @HostListener('document:click')
  onDocumentClick(): void {
    if (this.menuOpen) {
      this.menuOpen = false;
    }
  }

  async onLogout(): Promise<void> {
    this.menuOpen = false;
    const confirmed = await this.dialog.confirm({
      title: this.t('topbar.logout-title'),
      message: this.t('topbar.logout-message'),
      confirmLabel: this.t('topbar.logout-confirm'),
      cancelLabel: this.t('topbar.logout-cancel'),
    });
    if (confirmed) {
      this.auth.logout();
    }
  }
}
