/** Filter snapshot passed from the report shell for file export. */
export interface ExportDownloadScope {
  activeFilters: Record<string, string>;
  selectedMainId: number | null;
  /** Scoped info query (pagination keys stripped by the caller). */
  scopedInfoQuery: string;
}

export interface ExportDownloadContext {
  hasScope: boolean;
  scope: ExportDownloadScope;
}
