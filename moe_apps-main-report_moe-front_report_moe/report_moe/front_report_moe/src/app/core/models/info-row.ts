import type { InfoConfirmStatus } from './info-confirm-status';

/** Logical row from GET /api/v1/info-rows/ (one title submission line). */
export interface InfoRow {
  row_key: string | null;
  row_id: string;
  user: number | null;
  user_name: string;
  title_id: number | null;
  title_name: string | null;
  sub_main_id: number | null;
  sub_main_name: string | null;
  fields: Record<string, string>;
  info_ids: number[];
  confirmed: InfoConfirmStatus;
  confirm_note: string;
  commit_note: string;
  created_at: string | null;
}

export interface PaginatedInfoRows {
  /** Total logical rows when counted; may be null when include_count was omitted. */
  count: number | null;
  count_is_exact?: boolean;
  page: number;
  page_size: number;
  /** Keyset token for the next page (preferred over offset ``page``). */
  next_cursor?: string | null;
  is_truncated?: boolean;
  results: InfoRow[];
}

export function infoRowValuesPreview(row: InfoRow, maxParts = 3): string {
  const parts = Object.values(row.fields || {})
    .map((v) => String(v).trim())
    .filter((v) => v && v !== '—');
  if (!parts.length) return '—';
  const shown = parts.slice(0, maxParts).join(' · ');
  return parts.length > maxParts ? `${shown} …` : shown;
}
