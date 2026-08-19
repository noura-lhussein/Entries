import 'zone.js';
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { App } from './app/app';

bootstrapApplication(App, appConfig).catch((err: unknown) => {
  console.error(err);
  const message = err instanceof Error ? err.message : String(err);
  const bootError = document.getElementById('boot-error');
  if (bootError) {
    bootError.hidden = false;
    bootError.textContent = 'Bootstrap failed: ' + message;
  }
});
