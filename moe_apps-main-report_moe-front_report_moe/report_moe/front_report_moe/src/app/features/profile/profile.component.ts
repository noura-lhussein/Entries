import { Component, OnInit, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { UserUpdate } from '../../core/models';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  template: `
    <div class="page-container">
      <h1 class="page-title">{{ translation.t('profile.title') }}</h1>

      <div class="profile-grid">
        <!-- Avatar Section -->
        <div class="card avatar-card">
          <div class="avatar-container">
            <div class="avatar-large">{{ initials() }}</div>
            <button type="button" class="upload-btn" (click)="fileInput.click()">
              <mat-icon>camera_alt</mat-icon>
              <span>{{ translation.t('profile.update-photo') }}</span>
            </button>
            <input #fileInput hidden type="file" accept="image/*" />
          </div>
          <div class="user-details">
            <h2 class="user-name">{{ currentUser()?.full_name }}</h2>
            <p class="user-email">{{ currentUser()?.email }}</p>
            <div class="user-role">
              <span class="badge" [class.admin]="currentUser()?.is_superuser">
                {{
                  currentUser()?.is_superuser
                    ? translation.t('profile.admin')
                    : translation.t('profile.regular-user')
                }}
              </span>
            </div>
          </div>
        </div>

        <!-- Info Section -->
        <div class="card info-card">
          <h3 class="card-title">{{ translation.t('profile.account-info') }}</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">{{ translation.t('profile.username') }}</span>
              <span class="value">{{ currentUser()?.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ translation.t('profile.email') }}</span>
              <span class="value">{{ currentUser()?.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ translation.t('profile.join-date') }}</span>
              <span class="value">{{ currentUser()?.date_joined | date: 'short' }}</span>
            </div>
            <div class="info-item">
              <span class="label">{{ translation.t('profile.status') }}</span>
              <span class="badge" [class.active]="currentUser()?.is_active">
                {{
                  currentUser()?.is_active
                    ? translation.t('profile.active')
                    : translation.t('profile.inactive')
                }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit Profile Form -->
      <div class="card">
        <h3 class="card-title">{{ translation.t('profile.edit-personal-data') }}</h3>
        <form [formGroup]="profileForm" (ngSubmit)="onUpdateProfile()" class="form">
          <div class="form-row">
            <div class="form-group">
              <label>{{ translation.t('profile.first-name') }}</label>
              <input
                type="text"
                formControlName="first_name"
                [placeholder]="translation.t('profile.first-name-placeholder')"
                class="input"
              />
            </div>
            <div class="form-group">
              <label>{{ translation.t('profile.last-name') }}</label>
              <input
                type="text"
                formControlName="last_name"
                [placeholder]="translation.t('profile.last-name-placeholder')"
                class="input"
              />
            </div>
          </div>

          <div class="form-group">
            <label>{{ translation.t('profile.email') }}</label>
            <input
              type="email"
              formControlName="email"
              [placeholder]="translation.t('profile.email-placeholder')"
              class="input"
            />
            <div *ngIf="showError('email')" class="error-text">
              {{ getErrorMessage('email') }}
            </div>
          </div>

          <div *ngIf="updateError()" class="error-message">
            <mat-icon>error</mat-icon>
            <span>{{ updateError() }}</span>
          </div>

          <div class="form-actions">
            <button
              type="submit"
              [disabled]="profileForm.invalid || updating()"
              class="btn btn-primary"
            >
              <span *ngIf="!updating()">{{ translation.t('profile.save') }}</span>
              <span *ngIf="updating()">{{ translation.t('profile.save') }}...</span>
            </button>
          </div>
        </form>
      </div>

      <!-- Password Change Form -->
      <div class="card">
        <h3 class="card-title">{{ translation.t('profile.change-password') }}</h3>
        <form [formGroup]="passwordForm" (ngSubmit)="onChangePassword()" class="form">
          <div class="form-group">
            <label>{{ translation.t('profile.current-password') }}</label>
            <input
              type="password"
              formControlName="current_password"
              [placeholder]="translation.t('profile.current-password')"
              class="input"
            />
            <div *ngIf="showPasswordError('current_password')" class="error-text">
              {{ getErrorMessage('current_password') }}
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>{{ translation.t('profile.new-password') }}</label>
              <input
                type="password"
                formControlName="new_password"
                [placeholder]="translation.t('profile.new-password')"
                class="input"
              />
              <div *ngIf="showPasswordError('new_password')" class="error-text">
                {{ getErrorMessage('new_password') }}
              </div>
            </div>
            <div class="form-group">
              <label>{{ translation.t('profile.confirm-password') }}</label>
              <input
                type="password"
                formControlName="confirm_password"
                [placeholder]="translation.t('profile.confirm-password')"
                class="input"
              />
              <div *ngIf="showPasswordError('confirm_password')" class="error-text">
                {{ getErrorMessage('confirm_password') }}
              </div>
            </div>
          </div>

          <div *ngIf="passwordError()" class="error-message">
            <mat-icon>error</mat-icon>
            <span>{{ passwordError() }}</span>
          </div>

          <div class="form-actions">
            <button
              type="submit"
              [disabled]="passwordForm.invalid || changingPassword()"
              class="btn btn-primary"
            >
              <span *ngIf="!changingPassword()">{{ translation.t('profile.save') }}</span>
              <span *ngIf="changingPassword()">{{ translation.t('profile.save') }}...</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './profile.component.scss',
})
export class ProfileComponent implements OnInit {
  private auth = inject(AuthService);
  private api = inject(ApiService);
  private toast = inject(ToastService);
  private fb = inject(FormBuilder);
  translation = inject(TranslationService);

  currentUser = this.auth.currentUser;

  profileForm: FormGroup;
  passwordForm: FormGroup;

  updating = signal(false);
  updateError = signal('');
  changingPassword = signal(false);
  passwordError = signal('');

  constructor() {
    this.profileForm = this.fb.group({
      first_name: [''],
      last_name: [''],
      email: ['', [Validators.required, Validators.email]],
    });

    this.passwordForm = this.fb.group({
      current_password: ['', [Validators.required]],
      new_password: ['', [Validators.required, Validators.minLength(6)]],
      confirm_password: ['', [Validators.required]],
    });
  }

  ngOnInit(): void {
    const user = this.currentUser();
    if (user) {
      this.profileForm.patchValue({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
      });
    }
  }

  initials(): string {
    const u = this.currentUser();
    if (!u) return '?';
    const source = (u.full_name || u.username || '').trim();
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return source.slice(0, 2).toUpperCase();
  }

  showError(field: string): boolean {
    const control = this.profileForm.get(field);
    return !!(control && control.touched && control.invalid);
  }

  showPasswordError(field: string): boolean {
    const control = this.passwordForm.get(field);
    return !!(control && control.touched && control.invalid);
  }

  getErrorMessage(field: string): string {
    const control = this.profileForm.get(field) || this.passwordForm.get(field);
    if (!control?.errors) return '';
    if (control.errors['required']) return this.translation.t('profile.required');
    if (control.errors['email']) return this.translation.t('profile.invalid-email');
    if (control.errors['minlength']) return this.translation.t('profile.required');
    return this.translation.t('profile.required');
  }

  onUpdateProfile(): void {
    if (this.profileForm.invalid) return;

    this.updating.set(true);
    this.updateError.set('');

    const updateData: UserUpdate = this.profileForm.value;
    const userId = this.currentUser()?.id;

    if (!userId) return;

    this.api.patch(`/users/${userId}/`, updateData).subscribe({
      next: () => {
        this.toast.success(this.translation.t('profile.save-success'));
        this.auth.fetchMe();
        this.updating.set(false);
      },
      error: (err) => {
        this.updating.set(false);
        this.updateError.set(err.error?.detail || this.translation.t('profile.save-error'));
      },
    });
  }

  onChangePassword(): void {
    if (this.passwordForm.invalid) return;

    const pwd = this.passwordForm.value;
    if (pwd.new_password !== pwd.confirm_password) {
      this.passwordError.set(this.translation.t('profile.password-mismatch'));
      return;
    }

    this.changingPassword.set(true);
    this.passwordError.set('');

    const userId = this.currentUser()?.id;
    if (!userId) return;

    this.api
      .patch(`/users/${userId}/`, {
        password: pwd.new_password,
      })
      .subscribe({
        next: () => {
          this.toast.success(this.translation.t('profile.save-success'));
          this.passwordForm.reset();
          this.changingPassword.set(false);
        },
        error: (err) => {
          this.changingPassword.set(false);
          this.passwordError.set(err.error?.detail || this.translation.t('profile.save-error'));
        },
      });
  }
}
