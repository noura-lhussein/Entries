import type { InfoRow } from '../../core/models/info-row';
import type { AdminReportRow, ConfirmStatus } from './admin-report.models';

function rowConfirmStatus(confirmed: string): ConfirmStatus {
  if (confirmed === 'accept') return 'approved';
  if (confirmed === 'reject') return 'rejected';
  return 'waiting';
}

/** Map API info-rows into admin-report pivot rows (columns built separately). */
export function mapInfoRowsToAdminRows(apiRows: InfoRow[]): AdminReportRow[] {
  return apiRows.map((r) => {
    const attrCells: Record<string, string> = {};
    for (const [attrId, val] of Object.entries(r.fields || {})) {
      attrCells[`attr_${attrId}`] = val ?? '—';
    }
    return {
      id: r.row_id,
      user_name: r.user_name ?? '—',
      ...attrCells,
      _infoIds: r.info_ids,
      _commit_note: r.commit_note?.trim() || '—',
      _confirm_note: r.confirm_note?.trim() || '—',
      _allAccepted: r.confirmed === 'accept',
      _allRejected: r.confirmed === 'reject',
      _confirmStatus: rowConfirmStatus(r.confirmed),
    } as AdminReportRow;
  });
}
