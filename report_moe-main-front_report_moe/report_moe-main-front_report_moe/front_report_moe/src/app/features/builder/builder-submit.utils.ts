import type { Attribute } from '../../core/services/builder.service';

export function isEmptySubmittedFormValue(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string' && value.trim() === '') return true;
  if (Array.isArray(value) && value.length === 0) return true;
  return false;
}

/**
 * Maps raw dynamic-form values to API payload entries, skipping empty optional fields
 * and non-attribute keys (e.g. virtual city control — not a numeric attribute id).
 */
export function collectNonEmptyAttributeValues(
  formData: Record<string, unknown>,
  attrs: Attribute[],
  resolveSubmittedValue: (attr: Attribute | undefined, raw: unknown) => unknown,
  options: { displayRowId: string },
): { attributeValues: { id: number; value: unknown }[]; displayRow: Record<string, unknown> };
export function collectNonEmptyAttributeValues(
  formData: Record<string, unknown>,
  attrs: Attribute[],
  resolveSubmittedValue: (attr: Attribute | undefined, raw: unknown) => unknown,
  options?: { displayRowId?: string },
): { attributeValues: { id: number; value: unknown }[]; displayRow?: Record<string, unknown> };
export function collectNonEmptyAttributeValues(
  formData: Record<string, unknown>,
  attrs: Attribute[],
  resolveSubmittedValue: (attr: Attribute | undefined, raw: unknown) => unknown,
  options?: { displayRowId?: string },
): { attributeValues: { id: number; value: unknown }[]; displayRow?: Record<string, unknown> } {
  const byId = new Map(attrs.map((a) => [a.id, a]));
  const attributeValues: { id: number; value: unknown }[] = [];
  let displayRow: Record<string, unknown> | undefined;
  if (options?.displayRowId != null) {
    displayRow = { id: options.displayRowId };
  }

  for (const [key, value] of Object.entries(formData)) {
    const attrId = Number(key);
    if (Number.isNaN(attrId)) continue;
    if (isEmptySubmittedFormValue(value)) continue;
    const resolved = resolveSubmittedValue(byId.get(attrId), value);
    attributeValues.push({ id: attrId, value: resolved });
    if (displayRow) {
      displayRow[`attr_${attrId}`] = resolved;
    }
  }

  return { attributeValues, displayRow };
}
