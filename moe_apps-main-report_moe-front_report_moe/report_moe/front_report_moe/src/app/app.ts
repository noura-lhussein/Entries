import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToastComponent } from './shared/components/toast/toast.component';
import { GlobalLoaderComponent } from './shared/components/global-loader/global-loader.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ToastComponent, GlobalLoaderComponent],
  template: `
    <app-global-loader></app-global-loader>
    <app-toast-container></app-toast-container>
    <div class="app-shell">
      <router-outlet></router-outlet>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styles: [
    `
      :host {
        display: block;
        height: 100%;
      }

      .app-shell {
        height: 100%;
        display: flex;
        flex-direction: column;
        min-height: 0;
      }

      .app-shell > :not(router-outlet) {
        flex: 1 1 auto;
        min-height: 0;
      }
    `,
  ],
})
export class App {}
