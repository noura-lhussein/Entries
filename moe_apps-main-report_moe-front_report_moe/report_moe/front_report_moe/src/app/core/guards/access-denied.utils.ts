import { Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import type { User } from '../models';

export const ACCESS_DENIED_ROUTE = '/access-denied';
export const LOGIN_ROUTE = '/login';

export function denyAccess(router: Router): UrlTree {
  return router.createUrlTree([ACCESS_DENIED_ROUTE]);
}

export function redirectToLogin(router: Router): UrlTree {
  return router.createUrlTree([LOGIN_ROUTE]);
}

/**
 * Resolve the signed-in user for route guards.
 * Unauthenticated → login (not access-denied).
 */
export async function resolveAuthUser(auth: AuthService, router: Router): Promise<User | UrlTree> {
  let user = auth.currentUser();
  if (!user) {
    user = await auth.fetchMe();
  }
  if (!user) {
    return redirectToLogin(router);
  }
  return user;
}

export function isUserResult(value: User | UrlTree): value is User {
  return !(value instanceof UrlTree);
}
