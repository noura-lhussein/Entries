import type { TableColumn, TableRow } from '../components/table/table.component';

/** One table under a title: a specific main/sub section context. */
export interface SubMainTableSlice {
  subMainId: number | null;
  subMainName: string;
  mainSectionName: string;
  columns: TableColumn[];
  rows: TableRow[];
}

/** All sections/sub-sections for the same title grouped together. */
export interface TitleGroupedBlock {
  titleId: number | null;
  titleName: string;
  titleOrder: number;
  subMainSlices: SubMainTableSlice[];
}
