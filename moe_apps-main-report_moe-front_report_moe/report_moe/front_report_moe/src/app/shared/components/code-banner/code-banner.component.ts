import { CommonModule } from '@angular/common';
import { Component, Input, computed, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-code-banner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="code-banner"
      [class.size-large]="size === 'large'"
      [class.size-compact]="size === 'compact'"
    >
      <div class="code-banner-label">{{ label }}</div>
      @if (segments().length > 1) {
        <div class="code-banner-segments" [class.is-preview]="preview">
          @for (segment of segments(); track $index) {
            <span class="code-segment">{{ segment }}</span>
          }
        </div>
      } @else {
        <div class="code-banner-value" [class.is-preview]="preview">{{ code }}</div>
      }
      <p *ngIf="hint" class="code-banner-hint">{{ hint }}</p>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './code-banner.component.scss',
})
export class CodeBannerComponent {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) code!: string;
  @Input() hint = '';
  @Input() preview = false;
  @Input() size: 'large' | 'compact' = 'large';

  segments = computed(() => {
    const raw = (this.code || '').trim();
    if (!raw.includes('-')) return [raw];
    return raw.split('-').filter(Boolean);
  });
}
