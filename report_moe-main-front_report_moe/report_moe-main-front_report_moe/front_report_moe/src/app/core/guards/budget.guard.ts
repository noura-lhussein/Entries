import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { denyAccess } from './access-denied.utils';

function canReadBudget(user: {
  is_admin: boolean;
  can_manage_budget: boolean;
  can_view_budget: boolean;
}): boolean {
  return user.is_admin || user.can_manage_budget || user.can_view_budget;
}

function canWriteBudget(user: {
  is_admin: boolean;
  can_manage_budget: boolean;
  can_write_budget: boolean;
}): boolean {
  return user.is_admin || user.can_manage_budget || user.can_write_budget;
}

function canManageBudgetUsers(user: {
  is_admin: boolean;
  can_manage_budget: boolean;
  can_manage_budget_users: boolean;
}): boolean {
  return user.is_admin || user.can_manage_budget || user.can_manage_budget_users;
}

export const budgetReadGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (user && canReadBudget(user)) {
    return true;
  }
  return denyAccess(router);
};

export const budgetWriteGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (user && canWriteBudget(user)) {
    return true;
  }
  return denyAccess(router);
};

export const manageBudgetUsersGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (user && canManageBudgetUsers(user)) {
    return true;
  }
  return denyAccess(router);
};

/** System admin only (Django staff). */
export const systemAdminGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (user?.is_admin) {
    return true;
  }
  return denyAccess(router);
};

/** Reference data: system admin or can_manage_reference_data for all tabs; can_manage_budget for responsibles only. */
export const referenceDataGuard: CanActivateFn = async (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = await auth.fetchMe();
  if (!user) {
    return denyAccess(router);
  }
  const type = route.paramMap.get('type') || 'categories';
  if (user.is_admin || user.can_manage_reference_data) {
    return true;
  }
  if (type === 'responsibles' && user.can_manage_budget) {
    return true;
  }
  return denyAccess(router);
};
