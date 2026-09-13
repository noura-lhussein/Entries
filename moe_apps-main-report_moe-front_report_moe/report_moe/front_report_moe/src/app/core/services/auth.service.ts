import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom, timeout } from 'rxjs';
import { ApiService } from './api.service';
import { User } from '../models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);
  private router = inject(Router);

  currentUser = signal<User | null>(null);
  isLoading = signal(false);
  /** True while logout is in progress — guards should send anonymous users to login. */
  isLoggingOut = signal(false);
  isAuthenticated = computed(() => !!this.currentUser());
  isAdmin = computed(() => !!this.currentUser()?.is_admin);
  canAddUser = computed(() => !!this.currentUser()?.is_admin || !!this.currentUser()?.can_add_user);
  canExportReports = computed(
    () => !!this.currentUser()?.is_admin || !!this.currentUser()?.can_export_reports,
  );
  canViewBudget = computed(
    () =>
      !!this.currentUser()?.is_admin ||
      !!this.currentUser()?.can_manage_budget ||
      !!this.currentUser()?.can_view_budget,
  );
  canWriteBudget = computed(
    () =>
      !!this.currentUser()?.is_admin ||
      !!this.currentUser()?.can_manage_budget ||
      !!this.currentUser()?.can_write_budget,
  );
  canManageBudgetUsers = computed(
    () =>
      !!this.currentUser()?.is_admin ||
      !!this.currentUser()?.can_manage_budget ||
      !!this.currentUser()?.can_manage_budget_users,
  );
  canManageBudget = computed(
    () => !!this.currentUser()?.is_admin || !!this.currentUser()?.can_manage_budget,
  );
  canManageReferenceData = computed(
    () => !!this.currentUser()?.is_admin || !!this.currentUser()?.can_manage_reference_data,
  );
  // Admin only, exclusively — matches the backend's user_can_access_master_data
  // (master_data/permissions.py). Master-data reference tables are not gated by
  // sector write flags, unlike the operational data they feed into.
  canManageMasterData = computed(() => {
    const u = this.currentUser();
    if (!u) return false;
    return !!(u.is_admin || u.is_staff || u.is_superuser);
  });

  isBudgetOnlyUser = computed(() => {
    const user = this.currentUser();
    if (!user || user.is_admin) return false;
    const hasBudget =
      user.can_view_budget ||
      user.can_write_budget ||
      user.can_manage_budget ||
      user.can_manage_budget_users ||
      user.can_manage_reference_data;
    const hasReporting =
      user.can_write_info || user.can_view_info || user.can_confirm_info || user.can_export_reports;
    return hasBudget && !hasReporting;
  });

  async login(username: string, password: string): Promise<User> {
    this.isLoading.set(true);
    try {
      const user = await firstValueFrom(this.api.post<User>('auth/login/', { username, password }));
      this.currentUser.set(user);
      this.isLoggingOut.set(false);
      return user;
    } finally {
      this.isLoading.set(false);
    }
  }

  async fetchMe(): Promise<User | null> {
    try {
      const user = await firstValueFrom(this.api.get<User>('auth/me/').pipe(timeout(8000)));
      this.currentUser.set(user);
      return user;
    } catch {
      this.currentUser.set(null);
      return null;
    }
  }

  /**
   * App-start bootstrap: prime the CSRF cookie (so a returning user with a live
   * session but no csrftoken can still make writes) and resolve the session.
   * Never throws — an anonymous or unreachable backend just leaves currentUser null.
   */
  async initSession(): Promise<User | null> {
    try {
      await firstValueFrom(this.api.get('auth/csrf/').pipe(timeout(8000)));
    } catch {
      // non-fatal — /auth/me/ also refreshes the cookie (ensure_csrf_cookie)
    }
    return this.fetchMe();
  }

  clearSession(): void {
    this.currentUser.set(null);
  }

  async logout(): Promise<void> {
    this.isLoggingOut.set(true);
    try {
      await firstValueFrom(this.api.post('auth/logout/', {}));
    } catch {
      // ignore — session may already be gone
    }
    this.clearSession();
    await this.router.navigateByUrl('/login', { replaceUrl: true });
    this.isLoggingOut.set(false);
  }
}
