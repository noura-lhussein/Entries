import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { LoadingService } from '../services/loading.service';
import { FORCE_GLOBAL_LOADING, SKIP_GLOBAL_LOADING } from '../http/loading.context';

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

/**
 * Global overlay loader:
 * - On by default for mutating requests (save / delete / upload).
 * - Off by default for GET — pages use local loaders (list spinner, form loading).
 * Override per request with SKIP_GLOBAL_LOADING / FORCE_GLOBAL_LOADING.
 */
export const loadingInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
): Observable<HttpEvent<unknown>> => {
  const skip = req.context.get(SKIP_GLOBAL_LOADING);
  const force = req.context.get(FORCE_GLOBAL_LOADING);
  const showOverlay = force || (!skip && MUTATING_METHODS.has(req.method.toUpperCase()));

  if (!showOverlay) {
    return next(req);
  }

  const loading = inject(LoadingService);
  loading.show();
  return next(req).pipe(finalize(() => loading.hide()));
};
