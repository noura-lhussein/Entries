/** Return the sole option's value when the list has exactly one usable entry. */
export function soleOptionValue(
  options: ReadonlyArray<{ value: unknown }> | null | undefined,
): string | null {
  if (!options || options.length !== 1) return null;
  const raw = options[0]?.value;
  if (raw === '' || raw == null) return null;
  return String(raw);
}

/** Return the sole item when the list has exactly one entry. */
export function soleItem<T>(items: ReadonlyArray<T> | null | undefined): T | null {
  if (!items || items.length !== 1) return null;
  return items[0] ?? null;
}
