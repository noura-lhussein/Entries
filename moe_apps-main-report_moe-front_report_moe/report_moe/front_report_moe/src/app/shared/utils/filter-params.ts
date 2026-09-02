/** Normalize filter value to a list of non-empty string IDs. */
export function parseFilterIds(value: unknown): string[] {
  if (value === undefined || value === null || value === false) return [];
  if (Array.isArray(value)) {
    return value.map((v) => String(v).trim()).filter((v) => v !== '');
  }
  const s = String(value).trim();
  if (!s) return [];
  return s
    .split(',')
    .map((p) => p.trim())
    .filter((p) => p !== '');
}

export function serializeFilterIds(ids: string[]): string {
  return ids.join(',');
}

export function isEmptyFilterValue(value: unknown): boolean {
  if (value === undefined || value === null || value === false) return true;
  if (Array.isArray(value)) return value.length === 0;
  return String(value).trim() === '';
}
