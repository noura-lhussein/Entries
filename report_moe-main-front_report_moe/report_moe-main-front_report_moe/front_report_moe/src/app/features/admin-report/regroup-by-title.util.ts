import type { SubSectionBlock, TitleTable } from './admin-report.models';

export interface AdminTitleSlice {
  subMainId: number;
  subMainName: string;
  mainSectionName: string;
  titleTable: TitleTable;
}

export interface AdminTitleGroup {
  titleId: number | null;
  titleName: string;
  titleOrder: number;
  slices: AdminTitleSlice[];
}

/** Regroup show-all blocks: Title → main/sub section → lazy title table. */
export function regroupSubSectionBlocksByTitle(
  blocks: SubSectionBlock[],
  resolveMainSectionName: (subMainId: number) => string,
  titleOrder: (titleId: number | null) => number,
): AdminTitleGroup[] {
  const byTitle = new Map<number | null, AdminTitleGroup>();

  for (const block of blocks) {
    const subMainId = block.subSection.id;
    const subMainName = block.subSection.name;
    const mainSectionName = resolveMainSectionName(subMainId);

    for (const tt of block.titleTables) {
      const tid = tt.titleId ?? null;
      let group = byTitle.get(tid);
      if (!group) {
        group = {
          titleId: tid,
          titleName: tt.titleName,
          titleOrder: titleOrder(tid),
          slices: [],
        };
        byTitle.set(tid, group);
      }
      group.slices.push({
        subMainId,
        subMainName,
        mainSectionName,
        titleTable: tt,
      });
    }
  }

  const groups = [...byTitle.values()];
  for (const g of groups) {
    g.slices.sort((a, b) => {
      const main = a.mainSectionName.localeCompare(b.mainSectionName, 'ar');
      if (main !== 0) return main;
      return a.subMainName.localeCompare(b.subMainName, 'ar');
    });
  }
  groups.sort(
    (a, b) => a.titleOrder - b.titleOrder || a.titleName.localeCompare(b.titleName, 'ar'),
  );
  return groups;
}
