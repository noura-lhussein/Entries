import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Shared loading UI (same spinner as the former global-only design).
 * Use overlay=true for full-screen; default is inline for page/list content.
 */
@Component({
  selector: 'app-page-loader',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-loader" [class.page-loader--overlay]="overlay" role="status" aria-live="polite">
      <div class="loader-container">
        <div class="spinner" aria-hidden="true"></div>
        <p class="loader-text">{{ message }}</p>
      </div>
    </div>
  `,
  styleUrl: './page-loader.component.scss',
})
export class PageLoaderComponent {
  @Input() message = 'جاري التحميل...';
  /** Full-screen dimmed overlay (mutations / global interceptor). */
  @Input() overlay = false;
}
