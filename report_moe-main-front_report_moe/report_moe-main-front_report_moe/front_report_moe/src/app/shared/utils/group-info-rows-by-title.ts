import type { InfoRow } from '../../core/models/info-row';
import type { SubMainTableSlice, TitleGroupedBlock } from '../models/title-grouped-table.model';
import type { TableColumn, TableRow } from '../components/table/table.component';

export interface GroupInfoRowsByTitleOptions {
  rows: InfoRow[];
  mapRow: (row: InfoRow) => TableRow;
  buildFieldColumns: (fieldIds: string[]) => TableColumn[];
  resolveMainSectionName: (subMainId: number | null) => string;
  titleOrder: (titleId: number | null) => number;
  /** Extra columns after field columns (e.g. status badge). */
  trailingColumns?: TableColumn[];
}

function fieldIdsFromRows(rows: InfoRow[]): string[] {
  const ids = new Set<string>();
  for (const row of rows) {
    for (const id of Object.keys(row.fields || {})) ids.add(id);
  }
  return [...ids].sort((a, b) => a.localeCompare(b, 'ar', { numeric: true }));
}

/** Group logical info rows: Title → (main + sub section) → table rows. */
export function groupInfoRowsByTitle(options: GroupInfoRowsByTitleOptions): TitleGroupedBlock[] {
  const {
    rows,
    mapRow,
    buildFieldColumns,
    resolveMainSectionName,
    titleOrder,
    trailingColumns = [],
  } = options;

  const byTitle = new Map<number | null, Map<number | null, InfoRow[]>>();

  for (const row of rows) {
    const tid = row.title_id ?? null;
    const sid = row.sub_main_id ?? null;
    if (!byTitle.has(tid)) byTitle.set(tid, new Map());
    const bySub = byTitle.get(tid)!;
    if (!bySub.has(sid)) bySub.set(sid, []);
    bySub.get(sid)!.push(row);
  }

  const groups: TitleGroupedBlock[] = [];

  for (const [titleId, bySub] of byTitle) {
    const sample = [...bySub.values()].flat()[0];
    const titleName = sample?.title_name?.trim() || '—';
    const slices: SubMainTableSlice[] = [];

    for (const [subMainId, subRows] of bySub) {
      const fieldIds = fieldIdsFromRows(subRows);
      slices.push({
        subMainId,
        subMainName: subRows[0]?.sub_main_name?.trim() || '—',
        mainSectionName: resolveMainSectionName(subMainId),
        columns: [...buildFieldColumns(fieldIds), ...trailingColumns],
        rows: subRows.map(mapRow),
      });
    }

    slices.sort((a, b) => {
      const main = a.mainSectionName.localeCompare(b.mainSectionName, 'ar');
      if (main !== 0) return main;
      return a.subMainName.localeCompare(b.subMainName, 'ar');
    });

    groups.push({
      titleId,
      titleName,
      titleOrder: titleOrder(titleId),
      subMainSlices: slices,
    });
  }

  groups.sort(
    (a, b) => a.titleOrder - b.titleOrder || a.titleName.localeCompare(b.titleName, 'ar'),
  );
  return groups;
}
