import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { denyAccess, isUserResult, resolveAuthUser } from './access-denied.utils';

export const viewInfoGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const result = await resolveAuthUser(auth, router);
  if (!isUserResult(result)) return result;
  if (result.is_admin || result.can_view_info || result.can_write_info || result.can_confirm_info) {
    return true;
  }
  return denyAccess(router);
};
