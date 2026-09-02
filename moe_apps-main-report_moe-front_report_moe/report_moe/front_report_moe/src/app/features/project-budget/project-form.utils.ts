import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import type { Project, ProjectPayload } from './project-budget.models';

export function syncPreviousProjectField(form: UntypedFormGroup): void {
  const isRound = !!form.get('is_round')?.value;
  const control = form.get('previous_project');
  if (!control) return;

  if (isRound) {
    control.enable({ emitEvent: false });
    control.setValidators(Validators.required);
  } else {
    control.clearValidators();
    control.setValue(null, { emitEvent: false });
    control.disable({ emitEvent: false });
  }
  control.updateValueAndValidity({ emitEvent: false });
}

export function buildProjectForm(fb: UntypedFormBuilder, row?: Project): UntypedFormGroup {
  const form = fb.group({
    annual_budget: [row?.annual_budget ?? null, Validators.required],
    name_ar: [row?.name_ar ?? '', Validators.required],
    name_en: [row?.name_en ?? ''],
    status: [row?.status ?? 'draft', Validators.required],
    foundation: [row?.foundation ?? null, Validators.required],
    community: [row?.community ?? null, Validators.required],
    target: [row?.target ?? null],
    policy: [row?.policy ?? null],
    quantitative_target_value: [row?.quantitative_target_value ?? ''],
    quantitative_target_unit: [row?.quantitative_target_unit ?? null],
    previous_project: [row?.previous_project ?? null],
    proposed_budget: [row?.proposed_budget ?? null, Validators.required],
    approved_budget: [row?.approved_budget ?? null],
    budget_expenditure: [row?.budget_expenditure ?? null],
    completion_is_manual: [row?.completion_is_manual ?? false],
    percentage_completion: [
      row?.percentage_completion ?? 0,
      [Validators.min(0), Validators.max(100)],
    ],
    start_date: [row?.start_date ?? '', Validators.required],
    end_date: [row?.end_date ?? '', Validators.required],
    latitude: [row?.latitude ?? ''],
    longitude: [row?.longitude ?? ''],
    is_round: [row?.is_round ?? false],
    description: [row?.description ?? ''],
  });
  syncPreviousProjectField(form);
  return form;
}

export function normalizeProjectPayload(value: Record<string, unknown>): ProjectPayload {
  const payload: ProjectPayload = {};
  const nullableIds = [
    'annual_budget',
    'foundation',
    'community',
    'target',
    'policy',
    'quantitative_target_unit',
    'previous_project',
  ] as const;
  const nullableNumbers = ['latitude', 'longitude', 'quantitative_target_value'] as const;
  const dateKeys = ['start_date', 'end_date'] as const;

  for (const [key, raw] of Object.entries(value)) {
    if (raw === '' || raw === undefined) {
      if (key === 'description' || key === 'name_en') {
        (payload as Record<string, unknown>)[key] = '';
      } else if (nullableIds.includes(key as (typeof nullableIds)[number])) {
        (payload as Record<string, unknown>)[key] = null;
      } else if (nullableNumbers.includes(key as (typeof nullableNumbers)[number])) {
        (payload as Record<string, unknown>)[key] = null;
      } else if (dateKeys.includes(key as (typeof dateKeys)[number])) {
        (payload as Record<string, unknown>)[key] = null;
      }
      continue;
    }

    if (nullableIds.includes(key as (typeof nullableIds)[number])) {
      (payload as Record<string, unknown>)[key] = raw === null ? null : Number(raw);
      continue;
    }
    if (key === 'proposed_budget' || key === 'approved_budget' || key === 'budget_expenditure') {
      (payload as Record<string, unknown>)[key] = Number(raw);
      continue;
    }
    if (key === 'quantitative_target_value') {
      (payload as Record<string, unknown>)[key] = raw === null || raw === '' ? null : Number(raw);
      continue;
    }
    if (nullableNumbers.includes(key as (typeof nullableNumbers)[number])) {
      (payload as Record<string, unknown>)[key] = raw === null ? null : Number(raw);
      continue;
    }
    if (dateKeys.includes(key as (typeof dateKeys)[number])) {
      (payload as Record<string, unknown>)[key] =
        typeof raw === 'string' && raw ? raw.slice(0, 10) : null;
      continue;
    }
    if (key === 'is_round' || key === 'completion_is_manual') {
      (payload as Record<string, unknown>)[key] = !!raw;
      continue;
    }
    if (key === 'percentage_completion') {
      (payload as Record<string, unknown>)[key] = raw === null ? 0 : Number(raw);
      continue;
    }
    (payload as Record<string, unknown>)[key] = raw;
  }
  return payload;
}
