import type { TableScrollConfig } from '../components/table/table-scroll.config';

/** Shared vertical scroll cap for title-grouped info tables (user-data + admin-report). */
export const INFO_TABLE_SCROLL: TableScrollConfig = {
  vertical: 'auto',
  maxHeight: 'min(40vh, 22rem)',
};
