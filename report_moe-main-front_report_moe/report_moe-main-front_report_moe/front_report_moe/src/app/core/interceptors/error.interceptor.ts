import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';

const isAuthEndpoint = (url: string) =>
  url.includes('/auth/login') || url.includes('/auth/refresh');

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  const translation = inject(TranslationService);
  const t = (key: string) => translation.t(key);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (isAuthEndpoint(req.url)) {
        return throwError(() => error);
      }

      // Export download errors are handled in the page component.
      if (req.url.includes('export_format=')) {
        return throwError(() => error);
      }

      if (error.status === 0) {
        toast.error(t('http-errors.network'));
      } else if (error.status >= 500) {
        toast.error(t('http-errors.server').replace('{status}', String(error.status)));
      } else if (error.status === 403) {
        toast.error(t('http-errors.forbidden'));
      } else if (error.status === 404) {
        toast.error(t('http-errors.not-found'));
      } else if (error.status === 400 && typeof error.error === 'object') {
        const first = Object.values(error.error || {})[0];
        const msg = Array.isArray(first) ? first[0] : first;
        if (msg) toast.error(String(msg));
      }

      return throwError(() => error);
    }),
  );
};
