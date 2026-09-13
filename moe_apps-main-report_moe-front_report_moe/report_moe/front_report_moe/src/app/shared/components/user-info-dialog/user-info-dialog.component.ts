import { Component, Inject, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { User } from '../../../core/models';
import { TranslationService } from '../../services/translation.service';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-user-info-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatIconModule],
  template: `
    <div class="dialog-wrapper" [attr.dir]="language.lang() === 'ar' ? 'rtl' : 'ltr'">
      <div class="dialog-header">
        <div class="header-text">
          <div class="icon-circle">
            <mat-icon>person</mat-icon>
          </div>
          <div class="titles-block">
            <h2>{{ data.full_name || data.username }}</h2>
            <p class="username-sub">&#64;{{ data.username }}</p>
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
        <div class="info-grid">
          <section class="card-section card-compact">
            <h3 class="section-heading">{{ t('users.email') }}</h3>
            <p class="section-value">{{ data.email || t('users.info-dialog.none') }}</p>
          </section>

          <section class="card-section card-compact">
            <h3 class="section-heading">{{ t('users.parent-name') }}</h3>
            <p class="section-value">{{ data.parent_name || t('users.info-dialog.none') }}</p>
          </section>

          <section class="card-section card-compact">
            <h3 class="section-heading">{{ t('users.status') }}</h3>
            <span
              class="pill"
              [class.pill-active]="data.is_active"
              [class.pill-inactive]="!data.is_active"
            >
              {{ data.is_active ? t('users.info-dialog.active') : t('users.info-dialog.inactive') }}
            </span>
          </section>

          <section class="card-section card-compact">
            <h3 class="section-heading">{{ t('users.info-dialog.joined') }}</h3>
            <p class="section-value">{{ data.date_joined | date: 'yyyy/MM/dd' }}</p>
          </section>

          <section class="card-section permissions-block card-span-full">
            <h3 class="section-heading">{{ t('users.info-dialog.permissions') }}</h3>
            <div class="badges-row">
              <span class="badge admin" *ngIf="data.is_admin">{{
                t('users.info-dialog.badge-admin')
              }}</span>
              <span class="badge write" *ngIf="data.can_write_info">{{
                t('users.can-write')
              }}</span>
              <span class="badge view" *ngIf="data.can_view_info">{{ t('users.can-view') }}</span>
              <span class="badge confirm" *ngIf="data.can_confirm_info">{{
                t('users.can-confirm')
              }}</span>
              <span class="badge export" *ngIf="data.can_export_reports">{{
                t('users.can-export')
              }}</span>
              <span class="badge adduser" *ngIf="data.can_add_user">{{
                t('users.can-add-user')
              }}</span>
              <span class="muted" *ngIf="noPermissionBadges()">{{
                t('users.info-dialog.none')
              }}</span>
            </div>
          </section>

          <section class="card-section card-span-full" *ngIf="data.title_categories.length">
            <h3 class="section-heading">{{ t('users.info-dialog.title-categories') }}</h3>
            <div class="chip-list">
              <span class="chip title-chip" *ngFor="let cat of data.title_categories">{{
                cat['category__name']
              }}</span>
            </div>
          </section>

          <section class="card-section card-span-full" *ngIf="groupedSubMains().length">
            <h3 class="section-heading">{{ t('users.info-dialog.sub-sections') }}</h3>
            <div class="sections-stack">
              <div class="section-card" *ngFor="let g of groupedSubMains()">
                <div class="section-card-main">{{ g.mainName }}</div>
                <div class="chip-list">
                  <span class="chip sub-chip" *ngFor="let s of g.subs">{{ s }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div class="dialog-footer">
        <button type="button" class="btn-close" (click)="close()">
          {{ t('users.info-dialog.close') }}
        </button>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './user-info-dialog.component.scss',
})
export class UserInfoDialogComponent {
  translation = inject(TranslationService);
  language = inject(LanguageService);

  t = (key: string) => this.translation.t(key);

  constructor(
    private dialogRef: MatDialogRef<UserInfoDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: User,
  ) {}

  noPermissionBadges(): boolean {
    return (
      !this.data.is_admin &&
      !this.data.can_write_info &&
      !this.data.can_view_info &&
      !this.data.can_confirm_info &&
      !this.data.can_export_reports &&
      !this.data.can_add_user
    );
  }

  groupedSubMains(): { mainName: string; subs: string[] }[] {
    const subs = this.data.sub_mains ?? [];
    const map = new Map<string, string[]>();
    for (const s of subs) {
      const main = s['sub_main__main_section__name'] || '—';
      if (!map.has(main)) map.set(main, []);
      map.get(main)!.push(s['sub_main__name']);
    }
    return Array.from(map.entries()).map(([mainName, subsArr]) => ({ mainName, subs: subsArr }));
  }

  close(): void {
    this.dialogRef.close();
  }
}
