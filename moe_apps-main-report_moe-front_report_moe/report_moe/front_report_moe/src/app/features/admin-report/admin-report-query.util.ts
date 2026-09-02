import { parseFilterIds, serializeFilterIds } from '../../shared/utils/filter-params';
import { DATA_TABLE_PAGE_SIZE } from '../../shared/utils/data-table-page-size';

export interface BuildInfoQueryInput {
  activeFilters: Record<string, unknown>;
  selectedMainId: number | null;
  selectedDate: string | null;
  isExportReports: boolean;
  opts?: {
    subMainId?: number;
    titleId?: number;
    includeUser?: boolean;
    includeTitleFilter?: boolean;
    pageSize?: number;
    page?: number;
  };
}

/** Build info-rows / row-count query string from filter + selection state. */
export function buildInfoQueryParams(input: BuildInfoQueryInput): string {
  const params = new URLSearchParams();
  const opts = input.opts;
  params.set('page', String(opts?.page ?? 1));
  params.set('page_size', String(opts?.pageSize ?? DATA_TABLE_PAGE_SIZE));
  const af = input.activeFilters;
  const subIds = parseFilterIds(af['sub_main_id']);
  const mainIds = parseFilterIds(af['main_section_id']);
  const titleIds = parseFilterIds(af['title_id']);
  const titleCategoryIds = parseFilterIds(af['title_category_id']);
  const userIds = parseFilterIds(af['user']);
  const date = input.selectedDate;
  const toolbarMain = input.selectedMainId;

  if (opts?.subMainId != null) {
    params.set('sub_main_id', String(opts.subMainId));
  } else if (subIds.length) {
    params.set('sub_main_id', serializeFilterIds(subIds));
  } else if (mainIds.length) {
    params.set('main_section_id', serializeFilterIds(mainIds));
  } else if (toolbarMain != null) {
    params.set('main_section_id', String(toolbarMain));
  }

  if (titleCategoryIds.length) {
    params.set('title_category_id', serializeFilterIds(titleCategoryIds));
  }
  if (opts?.titleId != null) {
    params.set('title_id', String(opts.titleId));
  } else if (opts?.includeTitleFilter !== false && titleIds.length) {
    params.set('title_id', serializeFilterIds(titleIds));
  }
  if (opts?.includeUser !== false && userIds.length) {
    params.set('user', serializeFilterIds(userIds));
  }
  const archiveStatus = String(af['archive_status'] || '').trim();
  if (archiveStatus === 'include') {
    params.set('include_archived', 'true');
  } else if (archiveStatus === 'archived_only') {
    params.set('archived_only', 'true');
  }
  if (input.isExportReports) {
    params.set('confirmed', 'accept');
    const cityIds = parseFilterIds(af['city_id']);
    const districtIds = parseFilterIds(af['district_id']);
    const from = String(af['from'] || '').trim();
    const to = String(af['to'] || '').trim();
    if (districtIds.length) {
      params.set('district_id', serializeFilterIds(districtIds));
    } else if (cityIds.length) {
      params.set('governorate_id', serializeFilterIds(cityIds));
      params.set('city_id', serializeFilterIds(cityIds));
    }
    if (from) params.set('from', from);
    if (to) params.set('to', to);
  } else if (date) {
    params.set('from', date);
    params.set('to', date);
  }
  return params.toString();
}

export interface OverviewBulkParamsInput {
  subMainId: number | null;
  titleId: number | null;
  userId: number | null;
  date: string | null;
  titleCategoryIds: string[];
}

/** Query object for overview bulk confirm/reject. */
export function overviewBulkParams(
  input: OverviewBulkParamsInput,
): Record<string, string | number> {
  if (input.subMainId == null) return {};
  const p: Record<string, string | number> = { sub_main_id: input.subMainId };
  if (input.titleCategoryIds.length) {
    p['title_category_id'] = serializeFilterIds(input.titleCategoryIds);
  }
  if (input.titleId != null) p['title_id'] = input.titleId;
  if (input.userId != null) p['user'] = input.userId;
  if (input.date) {
    p['from'] = input.date;
    p['to'] = input.date;
  }
  return p;
}

/** Shared opts for title-scoped list/count when subMain may be absent. */
export function titleScopedQueryOpts(
  subMainId: number | null,
  titleId: number,
): { subMainId?: number; titleId: number; includeTitleFilter: boolean } {
  const opts: {
    subMainId?: number;
    titleId: number;
    includeTitleFilter: boolean;
  } = { titleId, includeTitleFilter: false };
  if (subMainId != null) opts.subMainId = subMainId;
  return opts;
}
