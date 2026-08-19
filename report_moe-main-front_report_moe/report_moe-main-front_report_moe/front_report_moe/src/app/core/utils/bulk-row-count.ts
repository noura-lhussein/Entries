/** Row count from bulk confirm/reject API — never use field counts (confirmed/rejected). */
export function bulkToastRowCount(res: { updated_rows?: number | null }): number {
  return typeof res.updated_rows === 'number' ? res.updated_rows : 0;
}
