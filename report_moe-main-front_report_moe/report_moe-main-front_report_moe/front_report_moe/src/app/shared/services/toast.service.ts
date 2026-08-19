import { Injectable, inject, signal } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
}

@Injectable({
  providedIn: 'root',
})
export class ToastService {
  private snackBar = inject(MatSnackBar);
  toasts = signal<Toast[]>([]);

  show(message: string, type: ToastType = 'info', duration: number = 3500): string {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const toast: Toast = { id, message, type, duration };

    this.toasts.update((toasts) => [...toasts, toast]);

    // Auto-remove after duration
    setTimeout(() => {
      this.remove(id);
    }, duration);

    return id;
  }

  remove(id: string): void {
    this.toasts.update((toasts) => toasts.filter((t) => t.id !== id));
  }

  success(message: string, duration = 3500): string {
    return this.show(message, 'success', duration);
  }

  error(message: string, duration = 4500): string {
    return this.show(message, 'error', duration);
  }

  warning(message: string, duration = 4000): string {
    return this.show(message, 'warning', duration);
  }

  info(message: string, duration = 3500): string {
    return this.show(message, 'info', duration);
  }

  clear(): void {
    this.toasts.set([]);
  }
}
