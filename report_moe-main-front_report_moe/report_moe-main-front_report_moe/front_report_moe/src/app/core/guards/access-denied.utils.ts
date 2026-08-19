import { Router, UrlTree } from '@angular/router';

export const ACCESS_DENIED_ROUTE = '/access-denied';

export function denyAccess(router: Router): UrlTree {
  return router.createUrlTree([ACCESS_DENIED_ROUTE]);
}
