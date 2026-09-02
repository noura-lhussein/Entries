import type { CategorySelectOption } from './project-budget.models';

const PATH_SEP = ' › ';

/** Investment category roots: 31=new, 32=ongoing, 33=replacement. */
export function projectTypeCategoryPrefix(projectTypeName: string): string | null {
  const name = (projectTypeName || '').trim();
  if (!name) return null;
  if (name.includes('استبدال') || name.includes('تجديد')) return '33';
  if (name.includes('مباشر')) return '32';
  if (name.includes('جديد')) return '31';
  return null;
}

export function filterCategoriesByProjectType(
  items: CategorySelectOption[],
  projectTypeName: string,
): CategorySelectOption[] {
  const prefix = projectTypeCategoryPrefix(projectTypeName);
  if (!prefix) return items;
  return items.filter((item) => (item.code ?? '').startsWith(prefix));
}

export function sortCategoryOptions(items: CategorySelectOption[]): CategorySelectOption[] {
  return [...items].sort((left, right) =>
    categorySortKey(left).localeCompare(categorySortKey(right), 'ar'),
  );
}

export function categoryOptionLabel(item: CategorySelectOption): string {
  if (item.breadcrumb?.length > 1) {
    return item.breadcrumb.join(PATH_SEP);
  }
  return item.name || String(item.id);
}

export function categorySortKey(item: CategorySelectOption): string {
  return (item.breadcrumb?.length ? item.breadcrumb.join('\0') : item.name) || String(item.id);
}

export function findCategoryOption(
  items: CategorySelectOption[],
  id: number | null,
): CategorySelectOption | null {
  if (id == null) return null;
  return items.find((item) => item.id === id) ?? null;
}
