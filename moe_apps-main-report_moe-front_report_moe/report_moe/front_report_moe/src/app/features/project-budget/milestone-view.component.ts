import { CommonModule } from '@angular/common';
import {
  Component,
  OnInit,
  computed,
  inject,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { UntypedFormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';
import { PageLoaderComponent } from '../../shared/components/page-loader/page-loader.component';
import { FormMapPickerComponent } from '../../shared/components/form-map-picker/form-map-picker.component';
import { TranslationService } from '../../shared/services/translation.service';
import { ToastService } from '../../shared/services/toast.service';
import type { Milestone, MilestoneStatus } from './project-budget.models';
import { ProjectBudgetService } from './project-budget.service';

@Component({
  selector: 'app-milestone-view',
  standalone: true,
  imports: [
    CommonModule,
    PageHeaderComponent,
    EmptyStateComponent,
    PageLoaderComponent,
    FormMapPickerComponent,
  ],
  template: `
    <div class="page-container">
      <app-page-header [title]="t('budget.milestones.view-title')" [action]="backAction" />

      @if (loading()) {
        <app-page-loader />
      } @else if (!milestone()) {
        <app-empty-state icon="inbox" [message]="t('budget.milestones.empty')" />
      } @else {
        <section class="hero">
          <div>
            <p class="project">{{ milestone()!.project_name || emptyValue() }}</p>
            <h2>{{ milestone()!.name_ar || emptyValue() }}</h2>
            <p class="name-en">{{ milestone()!.name_en || emptyValue() }}</p>
          </div>
          <span class="status-badge" [ngClass]="statusClass(milestone()!.status)">
            {{ statusLabel(milestone()!.status) }}
          </span>
        </section>

        <section class="cards">
          <article class="card">
            <p>{{ t('budget.milestones.percentage') }}</p>
            <strong>{{ percentDisplay(milestone()!.percentage_completion) }}</strong>
          </article>
          <article class="card">
            <p>{{ t('budget.milestones.order') }}</p>
            <strong>{{ milestone()!.order }}</strong>
          </article>
          <article class="card">
            <p>{{ t('budget.milestones.due-date') }}</p>
            <strong>{{ dateDisplay(milestone()!.due_date) }}</strong>
          </article>
        </section>

        <section class="details">
          <div class="panel">
            <h3>{{ t('budget.milestones.details') }}</h3>
            <div class="kv">
              <span>{{ t('budget.milestones.project') }}</span
              ><strong>{{ milestone()!.project_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.milestones.parent') }}</span
              ><strong>{{ milestone()!.parent_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.milestones.responsible') }}</span
              ><strong>{{ milestone()!.responsible_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.milestones.category') }}</span
              ><strong>{{ milestone()!.category_name || emptyValue() }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.start-date') }}</span
              ><strong>{{ dateDisplay(milestone()!.start_date) }}</strong>
            </div>
            <div class="kv">
              <span>{{ t('budget.projects.end-date') }}</span
              ><strong>{{ dateDisplay(milestone()!.end_date) }}</strong>
            </div>
          </div>
        </section>

        <section class="map-panel">
          <h3>{{ t('budget.projects.map-location') }}</h3>
          <app-form-map-picker
            [form]="mapForm"
            [readOnly]="true"
            [mapHeight]="460"
            [minMapHeight]="300"
            [label]="t('budget.projects.map-location')"
            [latitudeLabel]="t('budget.projects.latitude')"
            [longitudeLabel]="t('budget.projects.longitude')"
            [clearLabel]="t('budget.projects.map-clear')"
            [searchPlaceholder]="t('budget.projects.map-search-placeholder')"
            [searchNoResultsLabel]="t('budget.projects.map-search-no-results')"
            [searchLoadingLabel]="t('budget.projects.map-search-loading')"
            [resetViewLabel]="t('budget.projects.map-reset-view')"
            [focusMarkerLabel]="t('budget.projects.map-focus-location')"
            [zoomLockHintLabel]="t('budget.projects.map-enable-zoom')"
            [fullscreenLabel]="t('budget.projects.map-fullscreen')"
            [exitFullscreenLabel]="t('budget.projects.map-exit-fullscreen')"
            [emptyCoordinatesLabel]="t('budget.projects.map-no-coordinates')"
          />
        </section>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './milestone-view.component.scss',
})
export class MilestoneViewComponent implements OnInit {
  private budget = inject(ProjectBudgetService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private translation = inject(TranslationService);
  private fb = inject(UntypedFormBuilder);

  t = (key: string) => this.translation.t(key);
  loading = signal(true);
  milestone = signal<Milestone | null>(null);

  mapForm = this.fb.group({
    latitude: [''],
    longitude: [''],
  });

  backAction = {
    label: this.t('budget.milestones.back-to-list'),
    icon: 'arrow_back',
    routerLink: '/budget/milestones',
  };

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const id = Number(idParam);
    if (!idParam || Number.isNaN(id)) {
      this.loading.set(false);
      this.router.navigate(['/budget/milestones']);
      return;
    }

    this.budget.getMilestone(id).subscribe({
      next: (milestone) => {
        this.milestone.set(milestone);
        this.mapForm.patchValue({
          latitude: milestone.latitude ?? '',
          longitude: milestone.longitude ?? '',
        });
        this.loading.set(false);
      },
      error: () => {
        this.toast.error(this.t('budget.milestones.load-error'));
        this.loading.set(false);
        this.router.navigate(['/budget/milestones']);
      },
    });
  }

  statusLabel(status: MilestoneStatus): string {
    return this.t(`budget.milestones.status.${status}`);
  }

  statusClass(status: MilestoneStatus): string {
    return `status-${status}`;
  }

  percentDisplay(value: string | number): string {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return this.emptyValue();
    return `${parsed.toFixed(0)}%`;
  }

  dateDisplay(value: string | null): string {
    if (!value) return this.emptyValue();
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return this.emptyValue();
    return parsed.toLocaleDateString();
  }

  emptyValue(): string {
    return this.t('budget.projects.value-empty');
  }
}
