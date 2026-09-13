import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { ButtonComponent } from '../button/button.component';

export interface PageHeaderAction {
  label: string;
  icon?: string | null;
  routerLink?: string;
  click?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost' | 'link' | 'warning';
  /** Icon-only control; label is used as tooltip. */
  iconOnly?: boolean;
}

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule, RouterLink, MatIconModule, ButtonComponent],
  template: `
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">{{ title }}</h1>
        <p *ngIf="description" class="page-description">{{ description }}</p>
      </div>
      <div *ngIf="action || actions.length" class="header-action">
        <app-button
          *ngIf="action"
          [label]="action.label"
          [icon]="action.icon"
          [variant]="action.variant || 'primary'"
          [routerLink]="action.routerLink"
          (clicked)="action.click ? action.click() : null"
        ></app-button>
        <ng-container *ngFor="let a of actions">
          <app-button
            *ngIf="a.iconOnly && a.icon"
            [iconOnly]="true"
            [icon]="a.icon"
            [label]="a.label"
            [title]="a.label"
            [variant]="a.variant || 'primary'"
            size="sm"
            (clicked)="a.click?.()"
          ></app-button>
          <app-button
            *ngIf="!a.iconOnly"
            [label]="a.label"
            [icon]="a.icon"
            [variant]="a.variant || 'primary'"
            [routerLink]="a.routerLink"
            (clicked)="a.click ? a.click() : null"
          ></app-button>
        </ng-container>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './page-header.component.scss',
})
export class PageHeaderComponent {
  @Input() title!: string;
  @Input() description: string | null | undefined = undefined;
  @Input() action: PageHeaderAction | null | undefined = undefined;
  @Input() actions: PageHeaderAction[] = [];
}
