import { Routes } from '@angular/router';
import { LoginComponent } from './features/login/login.component';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { manageUsersGuard } from './core/guards/manage-users.guard';
import { writeInfoGuard } from './core/guards/write-info.guard';
import { viewInfoGuard } from './core/guards/view-info.guard';
import { exportReportsGuard } from './core/guards/export-reports.guard';
import {
  budgetReadGuard,
  budgetWriteGuard,
  manageBudgetUsersGuard,
  referenceDataGuard,
  systemAdminGuard,
} from './core/guards/budget.guard';
import { masterDataGuard } from './core/guards/master-data.guard';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/layout/main-layout.component').then((m) => m.MainLayoutComponent),
    children: [
      { path: '', redirectTo: 'profile', pathMatch: 'full' },
      {
        path: 'dashboard',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./features/profile/profile.component').then((m) => m.ProfileComponent),
      },
      {
        path: 'access-denied',
        loadComponent: () =>
          import('./features/access-denied/access-denied.component').then(
            (m) => m.AccessDeniedComponent,
          ),
      },
      {
        path: 'builder',
        canActivate: [writeInfoGuard],
        loadComponent: () =>
          import('./features/builder/builder.component').then((m) => m.BuilderComponent),
      },
      {
        path: 'sections-manage',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/sections-manage/sections-manage.component').then(
            (m) => m.SectionsManageComponent,
          ),
      },
      {
        path: 'master-data',
        canActivate: [masterDataGuard],
        loadComponent: () =>
          import('./features/master-data/master-data.component').then(
            (m) => m.MasterDataComponent,
          ),
      },
      {
        path: 'master-data/:slug',
        canActivate: [masterDataGuard],
        loadComponent: () =>
          import('./features/master-data/master-data.component').then(
            (m) => m.MasterDataComponent,
          ),
      },
      {
        path: 'user-data',
        canActivate: [writeInfoGuard],
        loadComponent: () =>
          import('./features/user-data/user-data.component').then((m) => m.UserDataComponent),
      },
      {
        path: 'reports',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/reports/reports-list.component').then((m) => m.ReportsListComponent),
      },
      {
        path: 'users',
        canActivate: [manageUsersGuard],
        loadComponent: () =>
          import('./features/users/users-list.component').then((m) => m.UsersListComponent),
      },
      {
        path: 'users/new',
        canActivate: [manageUsersGuard],
        loadComponent: () =>
          import('./features/users/user-form.component').then((m) => m.UserFormComponent),
      },
      {
        path: 'users/:id/edit',
        canActivate: [manageUsersGuard],
        loadComponent: () =>
          import('./features/users/user-form.component').then((m) => m.UserFormComponent),
      },
      {
        path: 'users/:id/permissions',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/users/user-permissions.component').then(
            (m) => m.UserPermissionsComponent,
          ),
      },
      {
        path: 'admin-report',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/admin-report/admin-report.component').then(
            (m) => m.AdminReportComponent,
          ),
      },
      {
        path: 'export-reports',
        canActivate: [exportReportsGuard],
        loadComponent: () =>
          import('./features/admin-report/export-reports-page.component').then(
            (m) => m.ExportReportsPageComponent,
          ),
      },
      {
        path: 'infos-overview',
        canActivate: [viewInfoGuard],
        loadComponent: () =>
          import('./features/admin-report/infos-overview-page.component').then(
            (m) => m.InfosOverviewPageComponent,
          ),
      },
      {
        path: 'budget/reference-data',
        redirectTo: 'budget/reference-data/categories',
        pathMatch: 'full',
      },
      {
        path: 'budget/reference-data/:type',
        canActivate: [referenceDataGuard],
        loadComponent: () =>
          import('./features/project-budget/budget-reference-data.component').then(
            (m) => m.BudgetReferenceDataComponent,
          ),
      },
      {
        path: 'budget/annual-budgets',
        canActivate: [systemAdminGuard],
        loadComponent: () =>
          import('./features/project-budget/annual-budgets.component').then(
            (m) => m.AnnualBudgetsComponent,
          ),
      },
      {
        path: 'budget/projects/new',
        canActivate: [budgetWriteGuard],
        loadComponent: () =>
          import('./features/project-budget/project-form.component').then(
            (m) => m.ProjectFormComponent,
          ),
      },
      {
        path: 'budget/projects/:id/view',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/project-view.component').then(
            (m) => m.ProjectViewComponent,
          ),
      },
      {
        path: 'budget/projects/:id/edit',
        canActivate: [budgetWriteGuard],
        loadComponent: () =>
          import('./features/project-budget/project-form.component').then(
            (m) => m.ProjectFormComponent,
          ),
      },
      {
        path: 'budget/dashboard',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/project-dashboard.component').then(
            (m) => m.ProjectDashboardComponent,
          ),
      },
      {
        path: 'budget/projects',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/projects-list.component').then(
            (m) => m.ProjectsListComponent,
          ),
      },
      {
        path: 'budget/milestones/:id/view',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/milestone-view.component').then(
            (m) => m.MilestoneViewComponent,
          ),
      },
      {
        path: 'budget/milestones/new',
        canActivate: [budgetWriteGuard],
        loadComponent: () =>
          import('./features/project-budget/milestone-form.component').then(
            (m) => m.MilestoneFormComponent,
          ),
      },
      {
        path: 'budget/milestones/:id/edit',
        canActivate: [budgetWriteGuard],
        loadComponent: () =>
          import('./features/project-budget/milestone-form.component').then(
            (m) => m.MilestoneFormComponent,
          ),
      },
      {
        path: 'budget/milestones',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/milestones-list.component').then(
            (m) => m.MilestonesListComponent,
          ),
      },
      {
        path: 'budget/project-changes',
        canActivate: [budgetReadGuard],
        loadComponent: () =>
          import('./features/project-budget/project-change-log-list.component').then(
            (m) => m.ProjectChangeLogListComponent,
          ),
      },
      {
        path: 'budget/users/new',
        canActivate: [manageBudgetUsersGuard],
        loadComponent: () =>
          import('./features/project-budget/budget-user-form.component').then(
            (m) => m.BudgetUserFormComponent,
          ),
      },
      {
        path: 'budget/users/:id/edit',
        canActivate: [manageBudgetUsersGuard],
        loadComponent: () =>
          import('./features/project-budget/budget-user-form.component').then(
            (m) => m.BudgetUserFormComponent,
          ),
      },
      {
        path: 'budget/users',
        canActivate: [manageBudgetUsersGuard],
        loadComponent: () =>
          import('./features/project-budget/budget-users-list.component').then(
            (m) => m.BudgetUsersListComponent,
          ),
      },
    ],
  },
  { path: '**', redirectTo: 'login' },
];
