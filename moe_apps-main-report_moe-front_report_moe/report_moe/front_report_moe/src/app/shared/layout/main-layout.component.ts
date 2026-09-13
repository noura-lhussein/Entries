import { Component, ViewChild, inject, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './sidebar.component';
import { TopbarComponent } from './topbar.component';
import { FooterComponent } from './footer.component';
import { AuthService } from '../../core/services/auth.service';
import { AppBrandingService } from '../../core/services/app-branding.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, TopbarComponent, FooterComponent],
  template: `
    <div class="layout">
      <app-topbar (toggleSidebar)="onToggle()"></app-topbar>
      <div class="body">
        <app-sidebar #sidebar></app-sidebar>
        <main class="content">
          <router-outlet></router-outlet>
        </main>
      </div>
      <app-footer></app-footer>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './main-layout.component.scss',
})
export class MainLayoutComponent implements OnInit {
  @ViewChild('sidebar') sidebar!: SidebarComponent;

  private auth = inject(AuthService);
  private branding = inject(AppBrandingService);

  async ngOnInit(): Promise<void> {
    if (!this.auth.currentUser()) {
      await this.auth.fetchMe();
    }
    this.branding.apply();
  }

  onToggle(): void {
    if (this.sidebar) {
      this.sidebar.setCollapsed(!this.sidebar.collapsed);
    }
  }
}
