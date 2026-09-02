export interface SidebarNavItem {
  id: string;
  labelKey: string;
  icon: string;
  route?: string;
  labelForNonAdminKey?: string;
  adminOnly?: boolean;
  nonAdminOnly?: boolean;
  writeOnly?: boolean;
  viewOnly?: boolean;
  exportOnly?: boolean;
  canAddUserOnly?: boolean;
  budgetReadOnly?: boolean;
  budgetWriteOnly?: boolean;
  canManageBudgetUsersOnly?: boolean;
  /** Visible for is_admin or can_manage_reference_data (full reference data page). */
  canManageReferenceDataOnly?: boolean;
  /** Visible for is_admin or any sector write flag (moeds master catalogs). */
  canManageMasterDataOnly?: boolean;
  /** Visible for can_manage_budget when not system admin (responsibles only). */
  manageBudgetResponsiblesOnly?: boolean;
  /** Visible but not navigable until the page is implemented. */
  comingSoon?: boolean;
  children?: SidebarNavItem[];
}

export interface SidebarNavGroup {
  id: string;
  titleKey: string;
  items: SidebarNavItem[];
}

export const SIDEBAR_NAV: SidebarNavGroup[] = [
  {
    id: 'dashboards',
    titleKey: 'sidebar.dashboards',
    items: [
      {
        id: 'dashboard',
        labelKey: 'sidebar.dashboard',
        icon: 'dashboard',
        route: '/dashboard',
        adminOnly: true,
      },
    ],
  },
  {
    id: 'management',
    titleKey: 'sidebar.management',
    items: [
      {
        id: 'users',
        labelKey: 'sidebar.users',
        icon: 'group',
        route: '/users',
        canAddUserOnly: true,
      },
      {
        id: 'sections-manage',
        labelKey: 'sidebar.section-manage',
        icon: 'account_tree',
        route: '/sections-manage',
        adminOnly: true,
      },
      {
        id: 'master-data',
        labelKey: 'sidebar.master-data',
        icon: 'dataset',
        route: '/master-data',
        canManageMasterDataOnly: true,
      },
      {
        id: 'builder',
        labelKey: 'sidebar.field-settings',
        icon: 'build',
        route: '/builder',
        labelForNonAdminKey: 'sidebar.enter-new-data',
        writeOnly: true,
      },
      {
        id: 'user-data',
        labelKey: 'sidebar.my-data',
        icon: 'storage',
        route: '/user-data',
        writeOnly: true,
      },
      {
        id: 'reports',
        labelKey: 'sidebar.reports',
        icon: 'description',
        route: '/reports',
        adminOnly: true,
      },
      {
        id: 'admin-report',
        labelKey: 'sidebar.admin-report',
        icon: 'table_chart',
        route: '/admin-report',
        adminOnly: true,
      },
      {
        id: 'infos-overview',
        labelKey: 'sidebar.submitted-data',
        icon: 'table_rows',
        route: '/infos-overview',
        nonAdminOnly: true,
        viewOnly: true,
      },
      {
        id: 'export-reports',
        labelKey: 'sidebar.export-reports',
        icon: 'download',
        route: '/export-reports',
        exportOnly: true,
      },
    ],
  },
  {
    id: 'budget',
    titleKey: 'sidebar.budget-module',
    items: [
      {
        id: 'budget-operations',
        labelKey: 'sidebar.budget.operations',
        icon: 'account_balance_wallet',
        budgetReadOnly: true,
        children: [
          {
            id: 'budget-dashboard',
            labelKey: 'sidebar.budget.dashboard',
            icon: 'dashboard',
            route: '/budget/dashboard',
            budgetReadOnly: true,
          },
          {
            id: 'budget-projects',
            labelKey: 'sidebar.budget.projects',
            icon: 'folder',
            route: '/budget/projects',
            budgetReadOnly: true,
          },
          {
            id: 'budget-milestones',
            labelKey: 'sidebar.budget.milestones',
            icon: 'flag',
            route: '/budget/milestones',
            budgetReadOnly: true,
          },
          {
            id: 'budget-change-log',
            labelKey: 'sidebar.budget.change-log',
            icon: 'history',
            route: '/budget/project-changes',
            budgetReadOnly: true,
          },
          {
            id: 'budget-annual-budgets',
            labelKey: 'sidebar.budget.annual-budgets',
            icon: 'calendar_today',
            route: '/budget/annual-budgets',
            adminOnly: true,
          },
          {
            id: 'budget-transactions',
            labelKey: 'sidebar.budget.transactions',
            icon: 'payments',
            route: '/budget/transactions',
            budgetWriteOnly: true,
            comingSoon: true,
          },
        ],
      },
      {
        id: 'budget-users',
        labelKey: 'sidebar.budget.users',
        icon: 'group',
        route: '/budget/users',
        canManageBudgetUsersOnly: true,
      },
      {
        id: 'budget-reference-data',
        labelKey: 'sidebar.budget.reference-data',
        icon: 'tune',
        route: '/budget/reference-data/categories',
        canManageReferenceDataOnly: true,
      },
      {
        id: 'budget-responsibles',
        labelKey: 'sidebar.budget.responsibles',
        icon: 'person',
        route: '/budget/reference-data/responsibles',
        manageBudgetResponsiblesOnly: true,
      },
    ],
  },
  {
    id: 'account',
    titleKey: 'sidebar.account',
    items: [
      {
        id: 'profile',
        labelKey: 'sidebar.profile',
        icon: 'person',
        route: '/profile',
      },
    ],
  },
];
