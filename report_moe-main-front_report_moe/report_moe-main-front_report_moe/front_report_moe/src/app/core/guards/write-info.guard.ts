import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { denyAccess } from './access-denied.utils';

export const writeInfoGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const user = await auth.fetchMe();

  if (user && (user.is_admin || user.can_write_info)) {
    return true;
  }

  return denyAccess(router);
};
