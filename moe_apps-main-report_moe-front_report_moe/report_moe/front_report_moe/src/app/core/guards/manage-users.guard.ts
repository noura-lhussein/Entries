import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { denyAccess, isUserResult, resolveAuthUser } from './access-denied.utils';

export const manageUsersGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const result = await resolveAuthUser(auth, router);
  if (!isUserResult(result)) return result;
  if (result.is_admin || result.can_add_user) return true;
  return denyAccess(router);
};
