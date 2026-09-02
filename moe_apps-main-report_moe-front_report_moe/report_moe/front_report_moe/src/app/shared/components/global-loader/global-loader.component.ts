import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoadingService } from '../../../core/services/loading.service';
import { PageLoaderComponent } from '../page-loader/page-loader.component';

@Component({
  selector: 'app-global-loader',
  standalone: true,
  imports: [CommonModule, PageLoaderComponent],
  template: `
    @if (loading.isLoading()) {
      <app-page-loader [overlay]="true" />
    }
  `,
})
export class GlobalLoaderComponent {
  loading = inject(LoadingService);
}
