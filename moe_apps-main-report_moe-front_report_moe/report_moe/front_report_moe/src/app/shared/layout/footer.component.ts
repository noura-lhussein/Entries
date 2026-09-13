import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { AppBrandingService } from '../../core/services/app-branding.service';

@Component({
  selector: 'app-footer',
  standalone: true,
  template: `
    <footer class="footer">
      <span
        >&copy; <strong>{{ branding.footerText() }}</strong
        >, All Rights Reserved</span
      >
      <span class="version">Version : 1.4.0</span>
    </footer>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './footer.component.scss',
})
export class FooterComponent {
  branding = inject(AppBrandingService);
}
