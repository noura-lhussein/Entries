/** How the shared admin-report shell is presented per route. */
export type AdminReportPageMode = 'admin' | 'export' | 'overview';

export const ADMIN_REPORT_PAGE_META: Record<
  AdminReportPageMode,
  { pageTitleKey: string | null; pageDescriptionKey: string | null; exportMode: boolean }
> = {
  admin: {
    pageTitleKey: null,
    pageDescriptionKey: null,
    exportMode: false,
  },
  export: {
    pageTitleKey: 'export-reports.title',
    pageDescriptionKey: 'export-reports.description',
    exportMode: true,
  },
  overview: {
    pageTitleKey: 'admin-report.user-overview-title',
    pageDescriptionKey: null,
    exportMode: false,
  },
};
