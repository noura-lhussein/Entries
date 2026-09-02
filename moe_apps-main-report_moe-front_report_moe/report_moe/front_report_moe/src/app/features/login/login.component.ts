import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { AppBrandingService } from '../../core/services/app-branding.service';
import { TranslationService } from '../../shared/services/translation.service';
import { LanguageService, Language } from '../../shared/services/language.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <main
      class="auth-shell"
      [class.lang-ar]="lang.lang() === 'ar'"
      [class.lang-en]="lang.lang() === 'en'"
      [attr.dir]="lang.lang() === 'ar' ? 'rtl' : 'ltr'"
    >
      <div class="auth-lang" role="group" [attr.aria-label]="translation.t('login.lang-switch')">
        <button
          type="button"
          class="auth-lang__btn"
          [class.is-active]="lang.lang() === 'ar'"
          (click)="setLang('ar')"
        >
          AR
        </button>
        <button
          type="button"
          class="auth-lang__btn"
          [class.is-active]="lang.lang() === 'en'"
          (click)="setLang('en')"
        >
          EN
        </button>
      </div>

      <section class="auth-layout" aria-labelledby="auth-page-title">
        <section class="auth-panel">
          <header class="auth-header">
            <img
              src="/assets/brand/logo-horizontal-green.svg"
              alt="Ministry of Energy Logo"
              class="auth-logo auth-logo--header"
            />
            <h2 id="auth-page-title">{{ translation.t('login.title') }}</h2>
          </header>

          <article class="auth-card">
            <div class="auth-card__header">
              <h3>{{ translation.t('login.heading') }}</h3>
              <p>{{ translation.t('login.description') }}</p>
            </div>

            <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="auth-form" novalidate>
              <label class="auth-field">
                <span>{{ translation.t('login.username') }}</span>
                <div class="auth-input">
                  <input
                    type="text"
                    formControlName="username"
                    autocomplete="username"
                    [placeholder]="translation.t('login.username-placeholder')"
                  />
                </div>
                <div *ngIf="showError('username')" class="error-text">
                  {{ translation.t('login.required') }}
                </div>
              </label>

              <label class="auth-field">
                <span>{{ translation.t('login.password') }}</span>
                <div class="auth-input">
                  <input
                    [type]="showPassword() ? 'text' : 'password'"
                    formControlName="password"
                    autocomplete="current-password"
                    [placeholder]="translation.t('login.password-placeholder')"
                  />
                  <button
                    type="button"
                    class="auth-eye-btn"
                    (click)="togglePassword()"
                    tabindex="-1"
                    [attr.aria-label]="
                      showPassword()
                        ? translation.t('login.hide-password')
                        : translation.t('login.show-password')
                    "
                  >
                    <mat-icon>{{ showPassword() ? 'visibility_off' : 'visibility' }}</mat-icon>
                  </button>
                </div>
                <div *ngIf="showError('password')" class="error-text">
                  {{ translation.t('login.required') }}
                </div>
              </label>

              <p *ngIf="error()" class="auth-error" role="alert">{{ error() }}</p>

              <button
                type="submit"
                class="auth-submit"
                [disabled]="loginForm.invalid || isLoading()"
              >
                {{ isLoading() ? translation.t('login.loading') : translation.t('login.submit') }}
              </button>
            </form>
          </article>
        </section>
      </section>
    </main>
  `,
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {
  private authService = inject(AuthService);
  private router = inject(Router);
  private fb = inject(FormBuilder);
  branding = inject(AppBrandingService);
  translation = inject(TranslationService);
  lang = inject(LanguageService);

  loginForm: FormGroup;
  error = signal('');
  showPassword = signal(false);
  isLoading = this.authService.isLoading;

  constructor() {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]],
    });
  }

  async ngOnInit(): Promise<void> {
    // Already signed in → leave login. Do not call fetchMe here when anonymous:
    // DRF returns 403 for /auth/me without a session and used to spam a permission toast.
    if (this.authService.currentUser()) {
      const user = this.authService.currentUser();
      if (user?.is_admin) {
        void this.router.navigate(['/dashboard']);
      } else {
        void this.router.navigate(['/profile']);
      }
      return;
    }
    this.branding.apply();
  }

  setLang(next: Language): void {
    this.lang.set(next);
  }

  togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  showError(field: string): boolean {
    const control = this.loginForm.get(field);
    return !!(control && control.touched && control.invalid);
  }

  async onSubmit() {
    if (this.loginForm.invalid) return;

    try {
      this.error.set('');
      const { username, password } = this.loginForm.value;
      await this.authService.login(username, password);
      this.branding.apply();
      const user = this.authService.currentUser();
      if (user?.is_admin) {
        this.router.navigate(['/dashboard']);
      } else {
        this.router.navigate(['/profile']);
      }
    } catch (err: any) {
      this.error.set(err.error?.detail || this.translation.t('login.title'));
    }
  }
}
