import type { InfoConfirmStatus } from '../../core/models/info-confirm-status';
import type { SubMainSection } from '../../core/services/builder.service';
import type { TableRow } from '../../shared/components/table/table.component';

export type { InfoConfirmStatus };

export interface BulkConfirmResponse {
  confirmed: number;
  updated_rows?: number;
}

export interface BulkRejectResponse {
  rejected: number;
  updated_rows?: number;
}

/** Row confirmation display state (three icons in confirm column). */
export type ConfirmStatus = 'waiting' | 'approved' | 'rejected';

/** Row status: all fields must share the same state (set together via row confirm). */
export function confirmStatusFromRow(row: {
  _allAccepted: boolean;
  _allRejected: boolean;
}): ConfirmStatus {
  if (row._allAccepted) return 'approved';
  if (row._allRejected) return 'rejected';
  return 'waiting';
}

/** Pivot row for one user’s attributes in admin-report / export tables. */
export interface AdminReportRow extends TableRow {
  id: string | number;
  user_name: string;
  _infoIds: number[];
  _commit_note: string;
  _confirm_note: string;
  _allAccepted: boolean;
  _allRejected: boolean;
  _confirmStatus: ConfirmStatus;
}

/** Mutable row while grouping Info records by user. */
export interface AdminReportRowDraft {
  id: string | number;
  user_name: string;
  _infoIds: number[];
  _acceptedCount: number;
  _waitingCount: number;
  _rejectedCount: number;
  _commitSet: Set<string>;
  _noteSet: Set<string>;
  [key: string]: unknown;
}

export interface InfoRecord {
  id: number;
  attribute: number;
  attribute_label: string;
  title_id: number | null;
  title_name: string | null;
  main_section_name?: string | null;
  district_name?: string | null;
  city_name?: string | null;
  user: number;
  user_name: string;
  value: string;
  confirmed: InfoConfirmStatus;
  confirm_note?: string;
  commit_note?: string;
}

export interface AdminReportColumn {
  key: string;
  label: string;
  width?: string;
  minWidth?: string;
  maxWidth?: string;
}

/** Default column sizing for admin-report tables; override per column as needed. */
export function withAdminReportColumnSizing(columns: AdminReportColumn[]): AdminReportColumn[] {
  return columns.map((col) => ({ ...col }));
}

export interface TitleTable {
  titleId: number | null;
  titleName: string;
  columns: AdminReportColumn[];
  rows: AdminReportRow[];
  allInfoIds: number[];
  /** Number of logical table rows for this title (prefetched or after load). */
  rowCount?: number | null;
  /** Total matching rows from API (for infinite scroll). */
  totalCount?: number | null;
  loadedPage?: number;
  isLoading?: boolean;
  isLoadingMore?: boolean;
  isLoaded?: boolean;
  isExpanded?: boolean;
}

export interface SubSectionBlock {
  subSection: SubMainSection;
  titleTables: TitleTable[];
  isLoading: boolean;
}

export const MAX_SUB_SECTIONS_LOAD = 20;
