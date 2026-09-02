import type { BudgetReferenceType } from './project-budget.models';

export interface BudgetReferenceTab {
  type: BudgetReferenceType;
  labelKey: string;
}

export const BUDGET_REFERENCE_TABS: BudgetReferenceTab[] = [
  { type: 'categories', labelKey: 'budget.reference.categories' },
  { type: 'foundations', labelKey: 'budget.reference.foundations' },
  { type: 'responsibles', labelKey: 'budget.reference.responsibles' },
  { type: 'project-types', labelKey: 'budget.reference.project-types' },
  { type: 'targets', labelKey: 'budget.reference.targets' },
  { type: 'policies', labelKey: 'budget.reference.policies' },
  { type: 'measure-units', labelKey: 'budget.reference.measure-units' },
  { type: 'currencies', labelKey: 'budget.reference.currencies' },
];
