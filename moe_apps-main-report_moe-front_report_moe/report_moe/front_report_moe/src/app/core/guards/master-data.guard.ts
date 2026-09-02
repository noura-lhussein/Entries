import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { denyAccess, isUserResult, resolveAuthUser } from './access-denied.utils';

function canAccessMasterData(user: {
  is_admin?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}): boolean {
  return !!(user.is_admin || user.is_staff || user.is_superuser);
}

/** Master data: system admin only — matches backend user_can_access_master_data. */
export const masterDataGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const result = await resolveAuthUser(auth, router);
  if (!isUserResult(result)) return result;
  if (!canAccessMasterData(result)) return denyAccess(router);
  return true;
};
