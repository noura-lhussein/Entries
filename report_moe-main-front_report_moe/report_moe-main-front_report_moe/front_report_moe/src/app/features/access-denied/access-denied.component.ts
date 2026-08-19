import { Component, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { TranslationService } from '../../shared/services/translation.service';

@Component({
  selector: 'app-access-denied',
  standalone: true,
  imports: [CommonModule, MatIconModule, ButtonComponent],
  template: `
    <div class="page-container">
      <div class="access-denied-card">
        <div class="icon-wrap" aria-hidden="true">
          <mat-icon>lock</mat-icon>
        </div>
        <h1>{{ t('access-denied.title') }}</h1>
        <p class="message">{{ t('access-denied.message') }}</p>
        <p class="hint">{{ t('access-denied.hint') }}</p>
        <div class="actions">
          <app-button
            variant="primary"
            icon="home"
            [label]="t('access-denied.go-profile')"
            (clicked)="goProfile()"
          />
          <app-button
            variant="ghost"
            icon="arrow_back"
            [label]="t('access-denied.go-back')"
            (clicked)="goBack()"
          />
        </div>
      </div>
    </div>
  `,
  styles: `
    .page-container {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 60vh;
      padding: 24px;
    }

    .access-denied-card {
      max-width: 480px;
      width: 100%;
      text-align: center;
      padding: 32px 28px;
      border: 1px solid var(--border-color, #e5e7eb);
      border-radius: 12px;
      background: var(--surface-card, #fff);
    }

    .icon-wrap {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 72px;
      height: 72px;
      margin-bottom: 16px;
      border-radius: 50%;
      background: #fef2f2;
      color: #b91c1c;
    }

    .icon-wrap mat-icon {
      font-size: 36px;
      width: 36px;
      height: 36px;
    }

    h1 {
      margin: 0 0 12px;
      font-size: 1.5rem;
      font-weight: 700;
    }

    .message {
      margin: 0 0 8px;
      color: var(--text-primary, #111827);
      line-height: 1.6;
    }

    .hint {
      margin: 0 0 24px;
      color: var(--text-muted, #6b7280);
      font-size: 0.95rem;
      line-height: 1.5;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: center;
    }
  `,
})
export class AccessDeniedComponent {
  private location = inject(Location);
  private router = inject(Router);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  goProfile(): void {
    this.router.navigate(['/profile']);
  }

  goBack(): void {
    this.location.back();
  }
}
