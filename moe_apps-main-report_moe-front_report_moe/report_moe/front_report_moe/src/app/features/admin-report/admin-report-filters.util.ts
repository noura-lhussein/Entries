import { parseFilterIds, serializeFilterIds } from '../../shared/utils/filter-params';

export type TitleWithCategory = { id: number; category?: number | null };

/** Titles narrowed by selected category ids (empty = all). */
export function titlesForCategory<T extends TitleWithCategory>(
  titles: T[],
  categoryIds: string[],
): T[] {
  if (!categoryIds.length) return titles;
  return titles.filter((t) => t.category != null && categoryIds.includes(String(t.category)));
}

export function hasTitleScope(filters: Record<string, unknown>): boolean {
  return (
    parseFilterIds(filters['title_category_id']).length > 0 ||
    parseFilterIds(filters['title_id']).length > 0
  );
}

export function isCategoryScopedView(
  filters: Record<string, unknown>,
  selectedSubId: number | null,
  showAll: boolean,
): boolean {
  return hasTitleScope(filters) && selectedSubId == null && !showAll;
}

/** Cascade title_id when category changes. Empty string means cleared. */
export function applyTitleCategoryFilterChange(
  prevFilters: Record<string, unknown>,
  categoryIds: string[],
  titles: TitleWithCategory[],
): { title_category_id: string; title_id: string } {
  const allowed = titlesForCategory(titles, categoryIds).map((t) => String(t.id));
  const allowedSet = new Set(allowed);
  const prevTitleIds = parseFilterIds(prevFilters['title_id']).filter((id) =>
    categoryIds.length ? allowedSet.has(id) : true,
  );
  let titleId = prevTitleIds.length ? serializeFilterIds(prevTitleIds) : '';
  // Sole remaining title under the category → select it by default.
  if (!titleId && allowed.length === 1) {
    titleId = allowed[0];
  }
  return {
    title_category_id: categoryIds.length ? serializeFilterIds(categoryIds) : '',
    title_id: titleId,
  };
}

/** Filter title tables by title_id and/or title_category_id. */
export function filterTitleTablesByScope<T extends { titleId: number | null }>(
  tables: T[],
  filters: Record<string, unknown>,
  titles: TitleWithCategory[],
): T[] {
  const titleIds = parseFilterIds(filters['title_id']);
  const categoryIds = parseFilterIds(filters['title_category_id']);
  const allowedTitleIds = new Set(titlesForCategory(titles, categoryIds).map((t) => String(t.id)));
  return tables.filter((t) => {
    if (t.titleId == null) return false;
    const id = String(t.titleId);
    if (titleIds.length) return titleIds.includes(id);
    if (categoryIds.length) return allowedTitleIds.has(id);
    return true;
  });
}
