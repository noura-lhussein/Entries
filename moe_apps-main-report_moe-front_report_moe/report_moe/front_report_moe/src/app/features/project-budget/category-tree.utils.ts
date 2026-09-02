import type { CategorySelectOption } from './project-budget.models';

const PATH_SEP = ' › ';

export interface CategoryTreeNode {
  id: number;
  code: string;
  name: string;
  parent: number | null;
  breadcrumb: string[];
  depth: number;
  children: CategoryTreeNode[];
}

export interface CategorySection {
  prefix: string;
  labelKey: string;
  roots: CategoryTreeNode[];
}

export interface CategoryTreeRow {
  node: CategoryTreeNode;
  depth: number;
}

export const CATEGORY_SECTION_DEFS: ReadonlyArray<{ prefix: string; labelKey: string }> = [
  { prefix: '31', labelKey: 'budget.projects.category-section-new' },
  { prefix: '32', labelKey: 'budget.projects.category-section-ongoing' },
  { prefix: '33', labelKey: 'budget.projects.category-section-renewal' },
];

export function categoryDisplayLabel(item: CategorySelectOption): string {
  const name =
    item.breadcrumb?.length > 1 ? item.breadcrumb.join(PATH_SEP) : item.name || String(item.id);
  const code = (item.code ?? '').trim();
  return code ? `${code} — ${name}` : name;
}

export function buildCategoryTree(items: CategorySelectOption[]): CategoryTreeNode[] {
  const nodes = new Map<number, CategoryTreeNode>();
  for (const item of items) {
    nodes.set(item.id, {
      id: item.id,
      code: item.code ?? '',
      name: item.name || String(item.id),
      parent: item.parent ?? null,
      breadcrumb: item.breadcrumb ?? [item.name || String(item.id)],
      depth: item.depth ?? 0,
      children: [],
    });
  }

  const roots: CategoryTreeNode[] = [];
  for (const node of nodes.values()) {
    if (node.parent != null && nodes.has(node.parent)) {
      nodes.get(node.parent)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  const sortRecursive = (list: CategoryTreeNode[]): void => {
    list.sort((left, right) =>
      (left.code || left.name).localeCompare(right.code || right.name, 'ar', { numeric: true }),
    );
    list.forEach((node) => sortRecursive(node.children));
  };
  sortRecursive(roots);
  return roots;
}

export function filterCategoryTree(nodes: CategoryTreeNode[], query: string): CategoryTreeNode[] {
  const term = query.trim().toLocaleLowerCase();
  if (!term) return nodes;

  const matches = (node: CategoryTreeNode): boolean => {
    const path = node.breadcrumb.join(' ').toLocaleLowerCase();
    return (
      node.name.toLocaleLowerCase().includes(term) ||
      node.code.toLocaleLowerCase().includes(term) ||
      path.includes(term)
    );
  };

  const prune = (list: CategoryTreeNode[]): CategoryTreeNode[] => {
    const out: CategoryTreeNode[] = [];
    for (const node of list) {
      const children = prune(node.children);
      if (matches(node) || children.length) {
        out.push({ ...node, children });
      }
    }
    return out;
  };

  return prune(nodes);
}

export function groupCategorySections(nodes: CategoryTreeNode[]): CategorySection[] {
  const known = new Set<number>();
  const sections: CategorySection[] = [];

  for (const def of CATEGORY_SECTION_DEFS) {
    const roots = nodes.filter((node) => node.code.startsWith(def.prefix));
    if (!roots.length) continue;
    roots.forEach((root) => known.add(root.id));
    sections.push({ prefix: def.prefix, labelKey: def.labelKey, roots });
  }

  const other = nodes.filter((node) => !known.has(node.id));
  if (other.length) {
    sections.push({
      prefix: 'other',
      labelKey: 'budget.projects.uncategorized',
      roots: other,
    });
  }

  return sections;
}

export function flattenCategoryTree(nodes: CategoryTreeNode[], depth = 0): CategoryTreeRow[] {
  const rows: CategoryTreeRow[] = [];
  for (const node of nodes) {
    rows.push({ node, depth });
    rows.push(...flattenCategoryTree(node.children, depth + 1));
  }
  return rows;
}

export function findCategoryById(
  items: CategorySelectOption[],
  id: number | null,
): CategorySelectOption | null {
  if (id == null) return null;
  return items.find((item) => item.id === id) ?? null;
}
