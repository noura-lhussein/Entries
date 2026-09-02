import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ApiService } from '../../core/services/api.service';
import { TranslationService } from '../../shared/services/translation.service';
import { DashboardActivity, DashboardStats } from '../../core/models';

interface StatCard {
  label: string;
  value: number;
  icon: string;
  color: string;
  suffix?: string;
}

interface ActivityView {
  title: string;
  icon: string;
  timestamp: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">{{ translation.t('dashboard.title') }}</h1>
        <p class="page-subtitle">{{ translation.t('dashboard.subtitle') }}</p>
      </div>

      <div *ngIf="loading()" class="loading">
        <p>{{ translation.t('dashboard.loading') }}</p>
      </div>

      <div *ngIf="!loading()" class="dashboard-grid">
        <div class="stats-grid">
          <div *ngFor="let stat of stats()" class="stat-card">
            <div class="stat-icon" [ngClass]="'stat-icon--' + stat.color">
              <mat-icon>{{ stat.icon }}</mat-icon>
            </div>
            <div class="stat-content">
              <span class="stat-label">{{ stat.label }}</span>
              <span class="stat-value"> {{ stat.value }}{{ stat.suffix || '' }} </span>
            </div>
          </div>
        </div>

        <div class="card activity-card">
          <h2 class="card-title">{{ translation.t('dashboard.recent-activities') }}</h2>
          <p *ngIf="recentActivities().length === 0" class="empty-activities">
            {{ translation.t('dashboard.no-activities') }}
          </p>
          <div class="activity-list" *ngIf="recentActivities().length">
            <div class="activity-item" *ngFor="let activity of recentActivities()">
              <div class="activity-icon">
                <mat-icon>{{ activity.icon }}</mat-icon>
              </div>
              <div class="activity-content">
                <p class="activity-title">{{ activity.title }}</p>
                <p class="activity-time">{{ activity.timestamp | date: 'short' }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="card quick-stats">
          <h2 class="card-title">{{ translation.t('dashboard.quick-stats') }}</h2>
          <div class="quick-stat-item">
            <span class="label">{{ translation.t('dashboard.completion') }}</span>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="confirmationRate()"></div>
            </div>
            <span class="value">{{ confirmationRate() }}%</span>
          </div>
          <div class="quick-stat-item">
            <span class="label">{{ translation.t('dashboard.pending-rate') }}</span>
            <div class="progress-bar">
              <div class="progress-fill pending" [style.width.%]="pendingRate()"></div>
            </div>
            <span class="value">{{ pendingCount() }}</span>
          </div>
          <div class="quick-stat-item">
            <span class="label">{{ translation.t('dashboard.weekly-activity') }}</span>
            <div class="progress-bar">
              <div class="progress-fill activity" [style.width.%]="activityRate7d()"></div>
            </div>
            <span class="value">{{ activityRate7d() }}%</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);
  translation = inject(TranslationService);

  loading = signal(true);
  stats = signal<StatCard[]>([]);
  recentActivities = signal<ActivityView[]>([]);
  confirmationRate = signal(0);
  pendingRate = signal(0);
  pendingCount = signal(0);
  activityRate7d = signal(0);

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.api.get<DashboardStats>('/dashboard/stats/').subscribe({
      next: (data) => this.applyStats(data),
      error: () => this.loading.set(false),
    });
  }

  private applyStats(data: DashboardStats): void {
    const t = (key: string) => this.translation.t(key);
    const cards: StatCard[] = [
      {
        label: t('dashboard.total-users'),
        value: data.users_count ?? 0,
        icon: 'group',
        color: 'primary',
      },
      {
        label: t('dashboard.main-sections'),
        value: data.main_sections_count ?? 0,
        icon: 'account_tree',
        color: 'blue',
      },
      {
        label: t('dashboard.sub-sections'),
        value: data.sub_sections_count ?? 0,
        icon: 'folder_open',
        color: 'blue',
      },
      {
        label: t('dashboard.reports'),
        value: data.reports_count ?? 0,
        icon: 'description',
        color: 'indigo',
      },
      {
        label: t('dashboard.titles'),
        value: data.titles_count ?? 0,
        icon: 'label',
        color: 'green',
      },
      {
        label: t('dashboard.attributes'),
        value: data.attributes_count ?? 0,
        icon: 'tune',
        color: 'amber',
      },
      {
        label: t('dashboard.infos'),
        value: data.rows_count ?? data.infos_count,
        icon: 'table_rows',
        color: 'slate',
      },
      {
        label: t('dashboard.confirmed'),
        value: data.rows_confirmed_count ?? data.infos_confirmed_count,
        icon: 'check_circle',
        color: 'green',
      },
      {
        label: t('dashboard.pending'),
        value: data.rows_pending_count ?? data.infos_pending_count,
        icon: 'pending_actions',
        color: 'amber',
      },
    ];
    this.stats.set(cards);
    this.confirmationRate.set(data.rows_confirmation_rate ?? data.confirmation_rate);
    const rowsTotal = data.rows_count ?? data.infos_count;
    const rowsPending = data.rows_pending_count ?? data.infos_pending_count;
    const pendingPct = rowsTotal > 0 ? Math.round((100 * rowsPending) / rowsTotal) : 0;
    this.pendingRate.set(pendingPct);
    this.pendingCount.set(rowsPending);
    this.activityRate7d.set(data.activity_rate_7d);
    this.recentActivities.set((data.recent_activities || []).map((a) => this.mapActivity(a)));
    this.loading.set(false);
  }

  private mapActivity(a: DashboardActivity): ActivityView {
    const t = (key: string) => this.translation.t(key);
    const user = a.user_name || '—';
    let verb = a.action;
    let icon = 'info';

    switch (a.action) {
      case 'LOGIN':
        verb = t('dashboard.activity-login');
        icon = 'login';
        break;
      case 'LOGOUT':
        verb = t('dashboard.activity-logout');
        icon = 'logout';
        break;
      case 'CREATE':
        verb = t('dashboard.activity-create');
        icon = 'add_circle';
        if (a.model_name === 'Info' && a.details && 'imported_rows' in a.details) {
          verb = t('dashboard.activity-excel');
          icon = 'upload_file';
        }
        break;
      case 'UPDATE':
        verb = t('dashboard.activity-update');
        icon = 'edit';
        break;
      case 'DELETE':
        verb = t('dashboard.activity-delete');
        icon = 'delete';
        break;
      case 'CONFIRM':
        verb = t('dashboard.activity-confirm');
        icon = 'verified';
        break;
    }

    const target = a.model_name ? ` ${a.model_name}` : '';
    return {
      title: `${user} — ${verb}${target}`,
      icon,
      timestamp: a.timestamp,
    };
  }
}
