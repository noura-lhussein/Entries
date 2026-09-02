/** Share of approved budget that has been spent (0–100+). */
export function budgetExpenditurePercent(
  approved: number | string | null | undefined,
  expenditure: number | string | null | undefined,
): number | null {
  const approvedValue = Number(approved);
  const spentValue = Number(expenditure);
  if (!Number.isFinite(approvedValue) || approvedValue <= 0) return null;
  if (!Number.isFinite(spentValue) || spentValue < 0) return 0;
  return (spentValue / approvedValue) * 100;
}

export function formatBudgetExpenditurePercent(percent: number | null | undefined): string {
  if (percent == null || !Number.isFinite(percent)) return '—';
  const rounded = Math.round(percent * 10) / 10;
  return `${rounded}%`;
}

/** Bar width capped at 100 for display; value may exceed 100 when over budget. */
export function budgetExpenditureProgressWidth(percent: number | null | undefined): number {
  if (percent == null || !Number.isFinite(percent)) return 0;
  return Math.min(100, Math.max(0, percent));
}

export function budgetExpenditureOverBudget(percent: number | null | undefined): boolean {
  return percent != null && Number.isFinite(percent) && percent > 100;
}
