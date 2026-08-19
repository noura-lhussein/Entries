import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { filter, Subscription } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { AppBrandingService } from '../../core/services/app-branding.service';
import { TranslationService } from '../../shared/services/translation.service';
import { SIDEBAR_NAV, type SidebarNavItem } from './sidebar.config';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, MatIconModule],
  template: `
    <aside class="sidebar" [class.collapsed]="collapsed">
      <div class="brand">
        <div class="logo">
          <img src="/assets/brand/logo-icon-gold.svg" alt="Logo" class="logo-image" />
        </div>
        <div class="brand-text" *ngIf="!collapsed">
          <div class="brand-ar" *ngIf="branding.showBrandAr()">{{ branding.brandAr() }}</div>
          <div class="brand-en">{{ branding.brandEn() }}</div>
        </div>
      </div>

      <nav class="nav">
        <ng-container *ngFor="let group of visibleGroups()">
          <div class="nav-group">
            <div class="group-title" *ngIf="!collapsed">{{ t(group.titleKey) }}</div>
            <ul class="nav-list">
              <ng-container *ngFor="let item of group.items">
                <li class="nav-item" *ngIf="item.children?.length; else leafItem">
                  <button
                    type="button"
                    class="nav-link nav-parent"
                    [class.expanded]="isExpanded(item.id)"
                    [class.active]="isParentActive(item)"
                    [title]="getItemLabel(item)"
                    (click)="toggleExpand(item.id)"
                  >
                    <mat-icon class="nav-icon">{{ item.icon }}</mat-icon>
                    <span class="nav-label" *ngIf="!collapsed">{{ getItemLabel(item) }}</span>
                    <mat-icon class="nav-chevron" *ngIf="!collapsed">
                      {{ isExpanded(item.id) ? 'expand_less' : 'expand_more' }}
                    </mat-icon>
                  </button>

                  <ul class="nav-sublist" *ngIf="isExpanded(item.id) && !collapsed">
                    <li class="nav-item" *ngFor="let child of item.children">
                      <a
                        *ngIf="child.route && !child.comingSoon"
                        [routerLink]="child.route"
                        routerLinkActive="active"
                        [routerLinkActiveOptions]="{ exact: false }"
                        class="nav-link nav-sublink"
                        [title]="getItemLabel(child)"
                      >
                        <mat-icon class="nav-icon">{{ child.icon }}</mat-icon>
                        <span class="nav-label">{{ getItemLabel(child) }}</span>
                      </a>
                      <span
                        *ngIf="child.comingSoon"
                        class="nav-link nav-sublink nav-disabled"
                        [title]="getItemLabel(child)"
                      >
                        <mat-icon class="nav-icon">{{ child.icon }}</mat-icon>
                        <span class="nav-label">{{ getItemLabel(child) }}</span>
                        <span class="nav-badge">{{ t('sidebar.coming-soon') }}</span>
                      </span>
                    </li>
                  </ul>
                </li>

                <ng-template #leafItem>
                  <li class="nav-item">
                    <a
                      *ngIf="item.route"
                      [routerLink]="item.route"
                      routerLinkActive="active"
                      [routerLinkActiveOptions]="{ exact: false }"
                      class="nav-link"
                      [title]="getItemLabel(item)"
                    >
                      <mat-icon class="nav-icon">{{ item.icon }}</mat-icon>
                      <span class="nav-label" *ngIf="!collapsed">{{ getItemLabel(item) }}</span>
                    </a>
                  </li>
                </ng-template>
              </ng-container>
            </ul>
          </div>
        </ng-container>
      </nav>
    </aside>
  `,
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit, OnDestroy {
  collapsed = false;
  private auth = inject(AuthService);
  branding = inject(AppBrandingService);
  private translation = inject(TranslationService);
  private router = inject(Router);
  private navSub?: Subscription;

  private expandedIds = signal<Set<string>>(new Set());
  private currentUrl = signal(this.router.url);

  t = (key: string) => this.translation.t(key);

  visibleGroups = computed(() => {
    const isAdmin = this.auth.isAdmin();
    const canAddUser = this.auth.canAddUser();
    const u = this.auth.currentUser();
    const canWrite = u ? u.is_admin || u.can_write_info : false;
    const canView = u
      ? u.is_admin || u.can_view_info || u.can_write_info || u.can_confirm_info
      : false;
    const canExport = u ? u.is_admin || u.can_export_reports : false;
    const canViewBudget = u ? u.is_admin || u.can_manage_budget || u.can_view_budget : false;
    const canWriteBudget = u ? u.is_admin || u.can_manage_budget || u.can_write_budget : false;
    const canManageBudgetUsers = u
      ? u.is_admin || u.can_manage_budget || u.can_manage_budget_users
      : false;
    const canManageBudgetResponsibles = u ? !u.is_admin && u.can_manage_budget : false;
    const canManageReferenceData = u ? u.is_admin || u.can_manage_reference_data : false;
    const canManageMasterData = this.auth.canManageMasterData();

    const visible = (item: SidebarNavItem): boolean => {
      if (item.adminOnly) return isAdmin;
      if (item.nonAdminOnly) return !isAdmin;
      if (item.canAddUserOnly) return canAddUser;
      if (item.writeOnly) return canWrite;
      if (item.viewOnly) return canView;
      if (item.exportOnly) return canExport;
      if (item.budgetReadOnly) return canViewBudget;
      if (item.budgetWriteOnly) return canWriteBudget;
      if (item.canManageBudgetUsersOnly) return canManageBudgetUsers;
      if (item.canManageReferenceDataOnly) return canManageReferenceData;
      if (item.canManageMasterDataOnly) return canManageMasterData;
      if (item.manageBudgetResponsiblesOnly) return canManageBudgetResponsibles;
      return true;
    };

    const mapItems = (items: SidebarNavItem[]): SidebarNavItem[] =>
      items
        .map((item) => {
          if (item.children?.length) {
            const children = item.children.filter(visible);
            if (!children.length || !visible(item)) return null;
            return { ...item, children };
          }
          return visible(item) ? item : null;
        })
        .filter((item): item is SidebarNavItem => item !== null);

    return SIDEBAR_NAV.map((group) => ({
      ...group,
      items: mapItems(group.items),
    })).filter((group) => group.items.length > 0);
  });

  ngOnInit(): void {
    this.syncExpandedFromUrl(this.router.url);
    this.navSub = this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe((event) => {
        const url = (event as NavigationEnd).urlAfterRedirects;
        this.currentUrl.set(url);
        this.syncExpandedFromUrl(url);
      });
  }

  ngOnDestroy(): void {
    this.navSub?.unsubscribe();
  }

  setCollapsed(value: boolean): void {
    this.collapsed = value;
  }

  isExpanded(id: string): boolean {
    return this.expandedIds().has(id);
  }

  toggleExpand(id: string): void {
    const next = new Set(this.expandedIds());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.expandedIds.set(next);
  }

  isParentActive(item: SidebarNavItem): boolean {
    const url = this.currentUrl();
    return !!item.children?.some(
      (child) => child.route && !child.comingSoon && url.startsWith(child.route),
    );
  }

  getItemLabel(item: SidebarNavItem): string {
    const isAdmin = this.auth.isAdmin();
    if (!isAdmin && item.labelForNonAdminKey) {
      return this.t(item.labelForNonAdminKey);
    }
    return this.t(item.labelKey);
  }

  private syncExpandedFromUrl(url: string): void {
    const next = new Set(this.expandedIds());
    for (const group of SIDEBAR_NAV) {
      for (const item of group.items) {
        if (!item.children?.length) continue;
        const active = item.children.some(
          (child) => child.route && !child.comingSoon && url.startsWith(child.route),
        );
        if (active) {
          next.add(item.id);
        }
      }
    }
    this.expandedIds.set(next);
  }
}
