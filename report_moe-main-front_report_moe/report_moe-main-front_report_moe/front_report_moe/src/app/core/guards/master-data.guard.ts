import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

function denyAccess(router: Router) {
  return router.createUrlTree(['/access-denied']);
}

function canAccessMasterData(user: {
  is_admin?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}): boolean {
  return !!(user.is_admin || user.is_staff || user.is_superuser);
}

/** Master data: system admin only, exclusively — matches the backend's
 * user_can_access_master_data (master_data/permissions.py). */
export const masterDataGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (!user) return denyAccess(router);
  if (!canAccessMasterData(user)) return denyAccess(router);
  return true;
};
