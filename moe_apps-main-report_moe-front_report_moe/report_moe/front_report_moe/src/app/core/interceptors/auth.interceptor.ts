import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { LanguageService } from '../../shared/services/language.service';

const isAuthEndpoint = (url: string) =>
  url.includes('/auth/login') || url.includes('/auth/logout') || url.includes('/auth/me');

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const language = inject(LanguageService);

  req = req.clone({
    withCredentials: true,
    setHeaders: { 'Accept-Language': language.lang() },
  });

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !isAuthEndpoint(req.url)) {
        auth.clearSession();
        router.navigate(['/login']);
      }
      return throwError(() => error);
    }),
  );
};
