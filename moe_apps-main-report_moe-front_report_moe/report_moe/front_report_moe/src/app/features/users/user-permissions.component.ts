import { Component, OnInit, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { ToastService } from '../../shared/services/toast.service';
import {
  BuilderService,
  MainSection,
  SubMainSection,
  TitleCategory,
} from '../../core/services/builder.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { TranslationService } from '../../shared/services/translation.service';

interface UserPermissions {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  sub_main_ids: number[];
  title_category_ids: number[];
}

@Component({
  selector: 'app-user-permissions',
  standalone: true,
  imports: [CommonModule, PageHeaderComponent],
  template: `
    <div class="page-container">
      <app-page-header
        [title]="t('user-permissions.title')"
        [action]="backAction"
      ></app-page-header>

      <div class="content" *ngIf="user()">
        <div class="header-section">
          <h2>{{ user()!.first_name }} {{ user()!.last_name }}</h2>
          <p>{{ user()!.username }}</p>
        </div>

        <div class="sections-grid">
          <!-- Main Sections -->
          <div class="section">
            <div class="section-header">
              <div class="section-title-block">
                <h3>{{ t('user-permissions.main-section') }}</h3>
                <p class="section-hint">{{ t('user-permissions.main-section-hint') }}</p>
              </div>
              <button
                class="btn-toggle"
                (click)="toggleMainSection()"
                [class.active]="showMainSection()"
              >
                {{
                  showMainSection()
                    ? t('user-permissions.select-field')
                    : t('user-permissions.clear-field')
                }}
              </button>
            </div>
            <div class="items-container" *ngIf="showMainSection()">
              <div *ngIf="mainSections().length === 0" class="empty">
                {{ t('user-permissions.no-main-sections') }}
              </div>
              <div class="items-list">
                <div
                  *ngFor="let main of mainSections()"
                  class="item-badge"
                  [class.selected]="isMainSectionSelected(main.id)"
                  (click)="toggleMainSection(main.id)"
                >
                  <span>{{ main.name }}</span>
                  <button
                    type="button"
                    class="remove-btn"
                    *ngIf="isMainSectionSelected(main.id)"
                    (click)="removeMainSection(main.id); $event.stopPropagation()"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Sub Main Sections -->
          <div class="section">
            <div class="section-header">
              <div class="section-title-block">
                <h3>{{ t('user-permissions.sub-section') }}</h3>
                <p class="section-hint">{{ t('user-permissions.sub-section-hint') }}</p>
              </div>
              <button
                class="btn-toggle"
                (click)="toggleSubSection()"
                [class.active]="showSubSection()"
              >
                {{
                  showSubSection()
                    ? t('user-permissions.select-field')
                    : t('user-permissions.clear-field')
                }}
              </button>
            </div>
            <div class="items-container" *ngIf="showSubSection()">
              <div *ngIf="subSections().length === 0" class="empty">
                {{ t('user-permissions.no-sub-sections') }}
              </div>
              <div class="items-list">
                <div
                  *ngFor="let sub of subSections()"
                  class="item-badge"
                  [class.selected]="isSubSectionSelected(sub.id)"
                  (click)="toggleSubSection(sub.id)"
                >
                  <span>{{ sub.name }}</span>
                  <button
                    type="button"
                    class="remove-btn"
                    *ngIf="isSubSectionSelected(sub.id)"
                    (click)="removeSubSection(sub.id); $event.stopPropagation()"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Title categories -->
          <div class="section">
            <div class="section-header">
              <h3>{{ t('user-permissions.title-categories-label') }}</h3>
              <button class="btn-toggle" (click)="toggleCategory()" [class.active]="showCategory()">
                {{
                  showCategory()
                    ? t('user-permissions.select-field')
                    : t('user-permissions.clear-field')
                }}
              </button>
            </div>
            <div class="items-container" *ngIf="showCategory()">
              <div *ngIf="titleCategories().length === 0" class="empty">
                {{ t('user-permissions.no-categories') }}
              </div>
              <div class="items-list">
                <div
                  *ngFor="let category of titleCategories()"
                  class="item-badge"
                  [class.selected]="isCategorySelected(category.id)"
                  (click)="toggleCategory(category.id)"
                >
                  <span>{{ category.name }}</span>
                  <button
                    type="button"
                    class="remove-btn"
                    *ngIf="isCategorySelected(category.id)"
                    (click)="removeCategory(category.id); $event.stopPropagation()"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="btn btn-secondary" (click)="goBack()">{{ t('form.back') }}</button>
          <button class="btn btn-primary" (click)="savePermissions()" [disabled]="loading()">
            {{ loading() ? t('user-permissions.saving') : t('user-permissions.save') }}
          </button>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './user-permissions.component.scss',
})
export class UserPermissionsComponent implements OnInit {
  private api = inject(ApiService);
  private builder = inject(BuilderService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  user = signal<UserPermissions | null>(null);
  mainSections = signal<MainSection[]>([]);
  subSections = signal<SubMainSection[]>([]);
  titleCategories = signal<TitleCategory[]>([]);
  loading = signal(false);

  selectedMainIds = signal<number[]>([]);
  selectedSubIds = signal<number[]>([]);
  selectedCategoryIds = signal<number[]>([]);

  showMainSection = signal(false);
  showSubSection = signal(false);
  showCategory = signal(false);

  userId: number | null = null;

  backAction = {
    label: this.t('form.back'),
    icon: 'arrow_back',
    routerLink: '/users',
    variant: 'ghost' as const,
  };

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      if (params['id']) {
        this.userId = params['id'];
        this.loadData();
      }
    });
  }

  private loadData(): void {
    if (!this.userId) return;

    this.api.get<UserPermissions>(`/users/${this.userId}/`).subscribe({
      next: (user) => {
        this.user.set(user);
        this.selectedMainIds.set([]);
        this.selectedSubIds.set(user.sub_main_ids || []);
        this.selectedCategoryIds.set(user.title_category_ids || []);
      },
      error: () => this.toast.error(this.t('user-permissions.load-user-error')),
    });

    this.builder.getMainSections().subscribe({
      next: (data) => this.mainSections.set(data.results || []),
      error: () => this.toast.error(this.t('user-permissions.load-main-error')),
    });

    this.builder.getSubMainSections({ leaves: true }).subscribe({
      next: (data) => {
        const leaves = (data.results || []).filter((s) => s.is_leaf !== false);
        this.subSections.set(leaves);
      },
      error: () => this.toast.error(this.t('user-permissions.load-sub-error')),
    });

    this.builder.getTitleCategories().subscribe({
      next: (data) => this.titleCategories.set(data.results || []),
      error: () => this.toast.error(this.t('user-permissions.load-categories-error')),
    });
  }

  private leafIdsUnderMain(mainId: number): number[] {
    return this.subSections()
      .filter((s: any) => (s.main_section ?? s.main_section_id) === mainId)
      .map((s) => s.id);
  }

  isMainSectionSelected(id: number): boolean {
    return this.selectedMainIds().includes(id);
  }

  isSubSectionSelected(id: number): boolean {
    return this.selectedSubIds().includes(id);
  }

  isCategorySelected(id: number): boolean {
    return this.selectedCategoryIds().includes(id);
  }

  toggleMainSection(id?: number): void {
    if (id === undefined) {
      this.showMainSection.update((v) => !v);
    } else {
      if (this.isMainSectionSelected(id)) {
        this.removeMainSection(id);
      } else {
        this.selectedMainIds.update((ids) => [...ids, id]);
        // Shortcut: selecting a main assigns all its leaf sub-sections.
        const leafIds = this.leafIdsUnderMain(id);
        this.selectedSubIds.update((ids) => [...new Set([...ids, ...leafIds])]);
      }
    }
  }

  toggleSubSection(id?: number): void {
    if (id === undefined) {
      this.showSubSection.update((v) => !v);
    } else {
      if (this.isSubSectionSelected(id)) {
        this.removeSubSection(id);
      } else {
        this.selectedSubIds.update((ids) => [...ids, id]);
      }
    }
  }

  toggleCategory(id?: number): void {
    if (id === undefined) {
      this.showCategory.update((v) => !v);
    } else {
      if (this.isCategorySelected(id)) {
        this.removeCategory(id);
      } else {
        this.selectedCategoryIds.update((ids) => [...ids, id]);
      }
    }
  }

  removeMainSection(id: number): void {
    this.selectedMainIds.update((ids) => ids.filter((i) => i !== id));
    const leafIds = new Set(this.leafIdsUnderMain(id));
    this.selectedSubIds.update((ids) => ids.filter((i) => !leafIds.has(i)));
  }

  removeSubSection(id: number): void {
    this.selectedSubIds.update((ids) => ids.filter((i) => i !== id));
  }

  removeCategory(id: number): void {
    this.selectedCategoryIds.update((ids) => ids.filter((i) => i !== id));
  }

  savePermissions(): void {
    if (!this.userId) return;

    this.loading.set(true);
    const payload = {
      sub_main_ids: this.selectedSubIds(),
      title_category_ids: this.selectedCategoryIds(),
    };

    this.api.patch(`/users/${this.userId}/`, payload).subscribe({
      next: () => {
        this.toast.success(this.t('user-permissions.save-success'));
        this.router.navigate(['/users']);
      },
      error: () => {
        this.toast.error(this.t('user-permissions.save-error'));
        this.loading.set(false);
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/users']);
  }
}
