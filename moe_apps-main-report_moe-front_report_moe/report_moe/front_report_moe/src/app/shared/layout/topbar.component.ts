import { Component, EventEmitter, Output, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { LanguageService } from '../services/language.service';
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
        aria-label="Toggle sidebar"
      >
        <mat-icon>menu</mat-icon>
      </button>

      <div class="actions">
        <button type="button" class="lang-btn" (click)="lang.toggle()">
          <mat-icon>language</mat-icon>
          <span>{{ lang.lang() === 'en' ? 'EN' : 'AR' }}</span>
        </button>

        <button type="button" class="icon-btn notif" aria-label="Notifications">
          <mat-icon>notifications</mat-icon>
          <span class="badge">0</span>
        </button>

        <div class="user-menu">
          <button
            type="button"
            class="avatar-btn"
            (click)="menuOpen = !menuOpen"
            aria-haspopup="true"
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
              <span>Profile</span>
            </a>
            <button type="button" class="dropdown-item danger" (click)="onLogout()">
              <mat-icon>logout</mat-icon>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  `,
  styleUrl: './topbar.component.scss',
})
export class TopbarComponent {
  @Output() toggleSidebar = new EventEmitter<void>();

  auth = inject(AuthService);
  lang = inject(LanguageService);

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

  async onLogout(): Promise<void> {
    this.menuOpen = false;
    const confirmed = await this.dialog.confirm({
      title: 'تسجيل الخروج',
      message: 'هل أنت متأكد أنك تريد تسجيل الخروج؟',
    });
    if (confirmed) {
      this.auth.logout();
    }
  }
}
