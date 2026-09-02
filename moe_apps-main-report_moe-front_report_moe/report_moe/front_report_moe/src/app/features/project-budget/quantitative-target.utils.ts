import type { Project } from './project-budget.models';

export function formatQuantitativeTarget(
  project: Pick<
    Project,
    | 'quantitative_target_value'
    | 'quantitative_target_unit_name'
    | 'quantitative_target_unit_symbol'
  >,
): string {
  const value = project.quantitative_target_value;
  if (value === null || value === undefined || value === '') {
    return '';
  }
  const unitLabel =
    project.quantitative_target_unit_symbol?.trim() ||
    project.quantitative_target_unit_name?.trim() ||
    '';
  return unitLabel ? `${value} ${unitLabel}` : String(value);
}
