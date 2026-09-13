from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.utils import timezone

from .models import (
    ActivityStatus,
    DevelopmentProject,
    MilestoneStatus,
    MilestoneType,
    ProjectActivity,
    ProjectActivityPeriod,
    ProjectMilestone,
    ProjectProgressPeriod,
)


@dataclass
class PeriodPoint:
    period_date: date
    planned_physical_pct: float
    actual_physical_pct: float | None
    planned_cumulative_spend_usd: float
    actual_cumulative_spend_usd: float | None
    notes: str = ''
    id: int | None = None
    is_generated: bool = False
    activity_id: int | None = None


def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def _month_end(year: int, month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def _iter_month_ends(start: date, end: date) -> list[date]:
    points: list[date] = []
    year, month = start.year, start.month
    cursor = _month_end(year, month)
    if cursor < start:
        month += 1
        if month > 12:
            year += 1
            month = 1
        cursor = _month_end(year, month)
    while cursor <= end:
        points.append(cursor)
        month += 1
        if month > 12:
            year += 1
            month = 1
        cursor = _month_end(year, month)
    return points


def _logistic_s_curve(progress_ratio: float) -> float:
    if progress_ratio <= 0:
        return 0.0
    if progress_ratio >= 1:
        return 100.0
    k = 10.0
    midpoint = 0.5
    value = 1.0 / (1.0 + math.exp(-k * (progress_ratio - midpoint)))
    return round(value * 100.0, 2)


def _project_schedule(project: DevelopmentProject) -> tuple[date, date]:
    start = project.start_date
    end = project.end_date
    if not start and project.start_year:
        start = date(project.start_year, 1, 1)
    if not end and project.reporting_through:
        end = project.reporting_through
    if not start:
        start = timezone.localdate().replace(day=1)
    if not end or end < start:
        end = date(start.year + 1, 12, 31)
    return start, end


def _value_at_month(periods: list[PeriodPoint], month: date, field: str) -> float | None:
    if not periods:
        return None
    value: float | None = None
    for point in periods:
        if point.period_date <= month:
            raw = getattr(point, field)
            value = _to_float(raw) if raw is not None else None
        else:
            break
    return value


def _generate_baseline_periods(project: DevelopmentProject) -> list[PeriodPoint]:
    start, end = _project_schedule(project)
    reporting_end = min(end, timezone.localdate())
    month_ends = _iter_month_ends(start, reporting_end)
    if not month_ends:
        month_ends = [reporting_end]

    total_months = max(len(_iter_month_ends(start, end)), 1)
    budget = _to_float(project.budget_usd)
    spent = _to_float(project.amount_spent_usd)
    points: list[PeriodPoint] = []

    for index, period_date in enumerate(month_ends, start=1):
        ratio = index / total_months
        planned_physical = _logistic_s_curve(ratio)
        planned_spend = round(budget * planned_physical / 100.0, 2)
        actual_physical = None
        actual_spend = None
        if period_date == month_ends[-1]:
            actual_spend = spent
            if budget > 0:
                actual_physical = round(min(spent / budget * 100.0 * 1.05, 100.0), 2)
            else:
                actual_physical = round(planned_physical * 0.92, 2)
        points.append(
            PeriodPoint(
                period_date=period_date,
                planned_physical_pct=planned_physical,
                actual_physical_pct=actual_physical,
                planned_cumulative_spend_usd=planned_spend,
                actual_cumulative_spend_usd=actual_spend,
                is_generated=True,
            ),
        )
    return points


def _period_from_model(row: ProjectProgressPeriod) -> PeriodPoint:
    return PeriodPoint(
        id=row.id,
        period_date=row.period_date,
        planned_physical_pct=_to_float(row.planned_physical_pct),
        actual_physical_pct=_to_float(row.actual_physical_pct) if row.actual_physical_pct is not None else None,
        planned_cumulative_spend_usd=_to_float(row.planned_cumulative_spend_usd),
        actual_cumulative_spend_usd=_to_float(row.actual_cumulative_spend_usd)
        if row.actual_cumulative_spend_usd is not None
        else None,
        notes=row.notes,
        is_generated=False,
    )


def _activity_period_from_model(row: ProjectActivityPeriod) -> PeriodPoint:
    return PeriodPoint(
        id=row.id,
        period_date=row.period_date,
        planned_physical_pct=_to_float(row.planned_physical_pct),
        actual_physical_pct=_to_float(row.actual_physical_pct) if row.actual_physical_pct is not None else None,
        planned_cumulative_spend_usd=_to_float(row.planned_cumulative_spend_usd),
        actual_cumulative_spend_usd=_to_float(row.actual_cumulative_spend_usd)
        if row.actual_cumulative_spend_usd is not None
        else None,
        is_generated=False,
        activity_id=row.activity_id,
    )


def _generate_baseline_activity_periods(activity: ProjectActivity, project: DevelopmentProject) -> list[PeriodPoint]:
    reporting_end = min(activity.planned_end, timezone.localdate())
    month_ends = _iter_month_ends(activity.planned_start, reporting_end)
    if not month_ends:
        month_ends = [activity.planned_end]

    total_months = max(len(_iter_month_ends(activity.planned_start, activity.planned_end)), 1)
    budget = _to_float(activity.planned_budget_usd) or (
        _to_float(project.budget_usd) * _to_float(activity.weight_pct) / 100.0
    )
    spent_share = _to_float(project.amount_spent_usd) * _to_float(activity.weight_pct) / 100.0
    points: list[PeriodPoint] = []

    for index, period_date in enumerate(month_ends, start=1):
        ratio = index / total_months
        planned_physical = _logistic_s_curve(ratio)
        planned_spend = round(budget * planned_physical / 100.0, 2)
        actual_physical = None
        actual_spend = None
        if period_date == month_ends[-1] and spent_share > 0:
            actual_spend = round(spent_share, 2)
            if budget > 0:
                actual_physical = round(min(spent_share / budget * 100.0, 100.0), 2)
        points.append(
            PeriodPoint(
                period_date=period_date,
                planned_physical_pct=planned_physical,
                actual_physical_pct=actual_physical,
                planned_cumulative_spend_usd=planned_spend,
                actual_cumulative_spend_usd=actual_spend,
                is_generated=True,
                activity_id=activity.id,
            ),
        )
    return points


def _resolve_activity_periods(activity: ProjectActivity, project: DevelopmentProject) -> tuple[list[PeriodPoint], bool]:
    stored = list(activity.periods.order_by('period_date'))
    if stored:
        return [_activity_period_from_model(row) for row in stored], False
    return _generate_baseline_activity_periods(activity, project), True


def _rollup_project_periods(
    project: DevelopmentProject,
    activities: list[ProjectActivity],
    activity_periods_map: dict[int, list[PeriodPoint]],
) -> list[PeriodPoint]:
    start, end = _project_schedule(project)
    reporting_end = min(end, timezone.localdate())
    month_ends = _iter_month_ends(start, reporting_end)
    if not month_ends:
        month_ends = [reporting_end]

    points: list[PeriodPoint] = []
    for period_date in month_ends:
        planned_physical = 0.0
        actual_physical = 0.0
        has_actual_physical = False
        planned_spend = 0.0
        actual_spend = 0.0
        has_actual_spend = False

        for activity in activities:
            weight = _to_float(activity.weight_pct) / 100.0
            periods = activity_periods_map.get(activity.id, [])
            if period_date < activity.planned_start:
                continue

            planned_value = _value_at_month(periods, period_date, 'planned_physical_pct') or 0.0
            planned_physical += weight * planned_value

            actual_value = _value_at_month(periods, period_date, 'actual_physical_pct')
            if actual_value is not None:
                has_actual_physical = True
                actual_physical += weight * actual_value

            planned_spend += _value_at_month(periods, period_date, 'planned_cumulative_spend_usd') or 0.0

            actual_spend_value = _value_at_month(periods, period_date, 'actual_cumulative_spend_usd')
            if actual_spend_value is not None:
                has_actual_spend = True
                actual_spend += actual_spend_value

        points.append(
            PeriodPoint(
                period_date=period_date,
                planned_physical_pct=round(planned_physical, 2),
                actual_physical_pct=round(actual_physical, 2) if has_actual_physical else None,
                planned_cumulative_spend_usd=round(planned_spend, 2),
                actual_cumulative_spend_usd=round(actual_spend, 2) if has_actual_spend else None,
                is_generated=False,
            ),
        )
    return points


def _resolve_periods(project: DevelopmentProject) -> tuple[list[PeriodPoint], bool, str]:
    activities = list(project.activities.order_by('sort_order', 'planned_start', 'id'))
    if activities:
        activity_periods_map: dict[int, list[PeriodPoint]] = {}
        any_generated = False
        for activity in activities:
            periods, generated = _resolve_activity_periods(activity, project)
            activity_periods_map[activity.id] = periods
            any_generated = any_generated or generated
        rolled = _rollup_project_periods(project, activities, activity_periods_map)
        return rolled, any_generated, 'activities'

    stored = list(project.progress_periods.order_by('period_date'))
    if stored:
        return [_period_from_model(row) for row in stored], False, 'project'
    return _generate_baseline_periods(project), True, 'project'


def _sync_project_progress_periods(project: DevelopmentProject, periods: list[PeriodPoint]) -> None:
    now = timezone.now()
    schedule_start, schedule_end = _project_schedule(project)
    project.progress_periods.all().delete()
    for row in periods:
        if row.period_date < schedule_start or row.period_date > schedule_end:
            continue
        ProjectProgressPeriod.objects.create(
            project=project,
            period_date=row.period_date,
            planned_physical_pct=Decimal(str(row.planned_physical_pct)),
            actual_physical_pct=Decimal(str(row.actual_physical_pct))
            if row.actual_physical_pct is not None
            else None,
            planned_cumulative_spend_usd=Decimal(str(row.planned_cumulative_spend_usd)),
            actual_cumulative_spend_usd=Decimal(str(row.actual_cumulative_spend_usd))
            if row.actual_cumulative_spend_usd is not None
            else None,
            notes=row.notes,
            updated_at=now,
        )


def _update_activity_progress(activity: ProjectActivity, periods: list[PeriodPoint]) -> None:
    latest = _latest_actual_period(periods)
    progress = 0.0
    if latest and latest.actual_physical_pct is not None:
        progress = latest.actual_physical_pct
    elif periods:
        progress = periods[-1].planned_physical_pct

    status = activity.status
    if progress >= 100:
        status = ActivityStatus.COMPLETED
    elif progress > 0:
        status = ActivityStatus.IN_PROGRESS

    activity.progress_pct = Decimal(str(round(progress, 2)))
    activity.status = status
    activity.updated_at = timezone.now()
    activity.save(update_fields=['progress_pct', 'status', 'updated_at'])


def _latest_actual_period(periods: list[PeriodPoint]) -> PeriodPoint | None:
    for row in reversed(periods):
        if row.actual_physical_pct is not None or row.actual_cumulative_spend_usd is not None:
            return row
    return periods[-1] if periods else None


def _compute_kpis(project: DevelopmentProject, periods: list[PeriodPoint]) -> list[dict[str, Any]]:
    budget = _to_float(project.budget_usd)
    spent = _to_float(project.amount_spent_usd)
    latest = _latest_actual_period(periods)
    planned_physical = latest.planned_physical_pct if latest else 0.0
    actual_physical = latest.actual_physical_pct if latest and latest.actual_physical_pct is not None else 0.0
    planned_spend = latest.planned_cumulative_spend_usd if latest else 0.0
    ac = spent if spent else (latest.actual_cumulative_spend_usd if latest else 0.0)

    def kpi(
        kpi_id: str,
        label_en: str,
        label_ar: str,
        value: float | None,
        unit: str = '',
        status: str = 'neutral',
    ) -> dict[str, Any]:
        return {
            'id': kpi_id,
            'label_en': label_en,
            'label_ar': label_ar,
            'value': value,
            'unit': unit,
            'status': status,
        }

    def physical_progress_status(actual: float, planned: float) -> str:
        if planned <= 0:
            return 'neutral'
        ratio = actual / planned
        if ratio >= 0.95:
            return 'ok'
        if ratio >= 0.85:
            return 'warning'
        return 'critical'

    def financial_progress_status(
        actual_spend: float,
        planned_spend_value: float,
        actual_physical_value: float,
        planned_physical_value: float,
    ) -> str:
        if planned_spend_value <= 0:
            return 'neutral'
        spend_ratio = actual_spend / planned_spend_value
        physical_ratio = (
            actual_physical_value / planned_physical_value if planned_physical_value > 0 else 1.0
        )
        if spend_ratio > 1.08 and physical_ratio < 0.92:
            return 'critical'
        if spend_ratio > 1.05 and physical_ratio < 0.95:
            return 'warning'
        if spend_ratio < 0.85:
            return 'critical'
        if spend_ratio < 0.95:
            return 'warning'
        return 'ok'

    def variance_pct(actual: float, planned: float) -> float | None:
        if planned <= 0:
            return None
        return round((actual - planned) / planned * 100.0, 1)

    financial_status = financial_progress_status(ac, planned_spend, actual_physical, planned_physical)
    physical_status = physical_progress_status(actual_physical, planned_physical)

    def kpi_with_tracking(
        kpi_id: str,
        label_en: str,
        label_ar: str,
        value: float | None,
        unit: str = '',
        status: str = 'neutral',
        planned_value: float | None = None,
        tracked_variance_pct: float | None = None,
    ) -> dict[str, Any]:
        row = kpi(kpi_id, label_en, label_ar, value, unit, status)
        if planned_value is not None:
            row['planned_value'] = planned_value
        if tracked_variance_pct is not None:
            row['variance_pct'] = tracked_variance_pct
        return row

    return [
        kpi('budget', 'Total budget', 'إجمالي الميزانية', budget, 'USD'),
        kpi_with_tracking(
            'spent',
            'Amount spent (actual)',
            'المبلغ المنفق (فعلي)',
            ac,
            'USD',
            financial_status,
            planned_value=planned_spend,
            tracked_variance_pct=variance_pct(ac, planned_spend),
        ),
        kpi('remaining', 'Remaining', 'المتبقي', max(budget - ac, 0), 'USD'),
        kpi_with_tracking(
            'physical_actual',
            'Physical progress (actual)',
            'التقدم الفعلي',
            actual_physical,
            '%',
            physical_status,
            planned_value=planned_physical,
            tracked_variance_pct=variance_pct(actual_physical, planned_physical),
        ),
        kpi('physical_planned', 'Physical progress (planned)', 'التقدم المخطط', planned_physical, '%'),
    ]


def _serialize_period(point: PeriodPoint) -> dict[str, Any]:
    payload = {
        'id': point.id,
        'period_date': point.period_date.isoformat(),
        'planned_physical_pct': point.planned_physical_pct,
        'actual_physical_pct': point.actual_physical_pct,
        'planned_cumulative_spend_usd': point.planned_cumulative_spend_usd,
        'actual_cumulative_spend_usd': point.actual_cumulative_spend_usd,
        'notes': point.notes,
        'is_generated': point.is_generated,
    }
    if point.activity_id is not None:
        payload['activity_id'] = point.activity_id
    return payload


def _serialize_milestone(row: ProjectMilestone) -> dict[str, Any]:
    return {
        'id': row.id,
        'code': row.code,
        'title_en': row.title_en,
        'title_ar': row.title_ar,
        'milestone_type': row.milestone_type,
        'planned_date': row.planned_date.isoformat(),
        'actual_date': row.actual_date.isoformat() if row.actual_date else None,
        'weight_pct': _to_float(row.weight_pct),
        'planned_value_usd': _to_float(row.planned_value_usd) if row.planned_value_usd is not None else None,
        'actual_value_usd': _to_float(row.actual_value_usd) if row.actual_value_usd is not None else None,
        'status': row.status,
        'sort_order': row.sort_order,
    }


def _serialize_activity(row: ProjectActivity) -> dict[str, Any]:
    return {
        'id': row.id,
        'title_en': row.title_en,
        'title_ar': row.title_ar,
        'category': row.category,
        'planned_start': row.planned_start.isoformat(),
        'planned_end': row.planned_end.isoformat(),
        'actual_start': row.actual_start.isoformat() if row.actual_start else None,
        'actual_end': row.actual_end.isoformat() if row.actual_end else None,
        'weight_pct': _to_float(row.weight_pct),
        'planned_budget_usd': _to_float(row.planned_budget_usd),
        'progress_pct': _to_float(row.progress_pct),
        'status': row.status,
        'sort_order': row.sort_order,
    }


def _generate_baseline_milestones(project: DevelopmentProject) -> list[dict[str, Any]]:
    start, end = _project_schedule(project)
    duration = max((end - start).days, 1)
    checkpoints = [
        (0.15, 'Project mobilization', 'تعبئة المشروع', MilestoneType.PHYSICAL, 10),
        (0.35, 'Procurement complete', 'اكتمال المشتريات', MilestoneType.FINANCIAL, 20),
        (0.55, 'Construction midpoint', 'منتصف التنفيذ', MilestoneType.PHYSICAL, 30),
        (0.75, 'Systems commissioning', 'تشغيل الأنظمة', MilestoneType.DELIVERABLE, 25),
        (1.0, 'Project handover', 'تسليم المشروع', MilestoneType.DELIVERABLE, 15),
    ]
    rows: list[dict[str, Any]] = []
    budget = _to_float(project.budget_usd)
    for index, (ratio, title_en, title_ar, milestone_type, weight) in enumerate(checkpoints):
        planned_date = start + timedelta(days=int(duration * ratio))
        status = MilestoneStatus.PLANNED
        actual_date = None
        if ratio <= 0.55 and project.amount_spent_usd and project.budget_usd:
            spend_ratio = _to_float(project.amount_spent_usd) / max(_to_float(project.budget_usd), 1)
            if spend_ratio >= ratio * 0.9:
                status = MilestoneStatus.COMPLETED
                actual_date = planned_date
        rows.append(
            {
                'id': None,
                'code': f'M{index + 1}',
                'title_en': title_en,
                'title_ar': title_ar,
                'milestone_type': milestone_type,
                'planned_date': planned_date.isoformat(),
                'actual_date': actual_date.isoformat() if actual_date else None,
                'weight_pct': weight,
                'planned_value_usd': round(budget * weight / 100.0, 2),
                'actual_value_usd': round(_to_float(project.amount_spent_usd) * weight / 100.0, 2)
                if project.amount_spent_usd
                else None,
                'status': status,
                'sort_order': index,
                'is_generated': True,
            },
        )
    return rows


def build_project_monitoring_payload(project: DevelopmentProject) -> dict[str, Any]:
    activities = list(project.activities.order_by('sort_order', 'planned_start', 'id'))
    periods, periods_generated, periods_source = _resolve_periods(project)

    milestones = list(project.milestones.order_by('sort_order', 'planned_date', 'id'))
    milestone_payload = [_serialize_milestone(row) for row in milestones]
    milestones_generated = False
    if not milestone_payload:
        milestone_payload = _generate_baseline_milestones(project)
        milestones_generated = True

    activity_monitoring: list[dict[str, Any]] = []
    activity_periods_generated = False
    for activity in activities:
        activity_periods, generated = _resolve_activity_periods(activity, project)
        activity_periods_generated = activity_periods_generated or generated
        activity_monitoring.append(
            {
                'activity': _serialize_activity(activity),
                'periods': [_serialize_period(point) for point in activity_periods],
                'periods_generated': generated,
            },
        )

    labels = [point.period_date.strftime('%b %Y') for point in periods]
    return {
        'project_id': project.id,
        'is_baseline_generated': periods_generated or milestones_generated or activity_periods_generated,
        'periods_generated': periods_generated,
        'periods_source': periods_source,
        'activity_periods_generated': activity_periods_generated,
        'milestones_generated': milestones_generated,
        'activities_generated': False,
        'kpis': _compute_kpis(project, periods),
        'curves': {
            'labels': labels,
            'physical': {
                'planned': [point.planned_physical_pct for point in periods],
                'actual': [point.actual_physical_pct for point in periods],
            },
            'financial': {
                'planned': [point.planned_cumulative_spend_usd for point in periods],
                'actual': [point.actual_cumulative_spend_usd for point in periods],
            },
        },
        'periods': [_serialize_period(point) for point in periods],
        'activity_monitoring': activity_monitoring,
        'milestones': milestone_payload,
        'activities': [_serialize_activity(row) for row in activities],
    }


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _resolve_activity_id(row: dict[str, Any], id_map: dict[int, int]) -> int | None:
    activity_id = row.get('activity_id')
    if activity_id is None:
        return None
    try:
        activity_id = int(activity_id)
    except (TypeError, ValueError):
        return None
    return id_map.get(activity_id, activity_id)


def _save_activity_periods(
    project: DevelopmentProject,
    payload_rows: list[dict[str, Any]],
    now,
    id_map: dict[int, int] | None = None,
) -> None:
    id_map = id_map or {}
    activity_ids = {row.id for row in project.activities.all()}
    project.activity_periods.all().delete()
    for row in payload_rows:
        activity_id = _resolve_activity_id(row, id_map)
        if not activity_id or activity_id not in activity_ids:
            continue
        period_date = _parse_date(row.get('period_date'))
        if not period_date:
            continue
        ProjectActivityPeriod.objects.create(
            project=project,
            activity_id=activity_id,
            period_date=period_date,
            planned_physical_pct=Decimal(str(row.get('planned_physical_pct') or 0)),
            actual_physical_pct=Decimal(str(row['actual_physical_pct']))
            if row.get('actual_physical_pct') is not None
            else None,
            planned_cumulative_spend_usd=Decimal(str(row.get('planned_cumulative_spend_usd') or 0)),
            actual_cumulative_spend_usd=Decimal(str(row['actual_cumulative_spend_usd']))
            if row.get('actual_cumulative_spend_usd') is not None
            else None,
            updated_at=now,
        )


def _activity_status(value: Any) -> str:
    allowed = {choice.value for choice in ActivityStatus}
    if value in allowed:
        return str(value)
    return ActivityStatus.NOT_STARTED


def _upsert_activities(
    project: DevelopmentProject,
    payload_rows: list[dict[str, Any]],
    now,
) -> dict[int, int]:
    """Create/update activities. Returns map of client/temp ids -> persisted ids."""
    by_id = {row.id: row for row in project.activities.all()}
    id_map: dict[int, int] = {activity_id: activity_id for activity_id in by_id}
    next_sort = max((row.sort_order for row in by_id.values()), default=-1) + 1

    for row in payload_rows:
        planned_start = _parse_date(row.get('planned_start'))
        planned_end = _parse_date(row.get('planned_end'))
        title_en = (row.get('title_en') or '').strip()
        title_ar = (row.get('title_ar') or '').strip()
        client_id = row.get('temp_id', row.get('id'))
        try:
            client_id_int = int(client_id) if client_id is not None else None
        except (TypeError, ValueError):
            client_id_int = None

        activity_id = row.get('id')
        try:
            activity_id = int(activity_id) if activity_id is not None else None
        except (TypeError, ValueError):
            activity_id = None

        # Negative / zero client ids are drafts — create, do not treat as DB ids.
        if activity_id is not None and activity_id <= 0:
            activity_id = None

        if activity_id and activity_id in by_id:
            activity = by_id[activity_id]
            if title_en:
                activity.title_en = title_en
            if 'title_ar' in row:
                activity.title_ar = title_ar
            if 'category' in row:
                activity.category = (row.get('category') or '').strip()
            if planned_start:
                activity.planned_start = planned_start
            if planned_end:
                activity.planned_end = planned_end
            if 'actual_start' in row:
                activity.actual_start = _parse_date(row.get('actual_start'))
            if 'actual_end' in row:
                activity.actual_end = _parse_date(row.get('actual_end'))
            if 'weight_pct' in row:
                activity.weight_pct = Decimal(str(row.get('weight_pct') or 0))
            if 'planned_budget_usd' in row:
                activity.planned_budget_usd = Decimal(str(row.get('planned_budget_usd') or 0))
            if 'status' in row:
                activity.status = _activity_status(row.get('status'))
            if 'sort_order' in row:
                activity.sort_order = int(row.get('sort_order') or 0)
            activity.updated_at = now
            activity.save()
            id_map[activity_id] = activity.id
            if client_id_int is not None:
                id_map[client_id_int] = activity.id
            continue

        if not title_en or not planned_start or not planned_end:
            continue

        sort_order = row.get('sort_order')
        if sort_order is None:
            sort_order = next_sort
            next_sort += 1
        else:
            sort_order = int(sort_order)

        activity = ProjectActivity.objects.create(
            project=project,
            title_en=title_en,
            title_ar=title_ar,
            category=(row.get('category') or '').strip(),
            planned_start=planned_start,
            planned_end=planned_end,
            actual_start=_parse_date(row.get('actual_start')),
            actual_end=_parse_date(row.get('actual_end')),
            weight_pct=Decimal(str(row.get('weight_pct') or 0)),
            planned_budget_usd=Decimal(str(row.get('planned_budget_usd') or 0)),
            progress_pct=Decimal(str(row.get('progress_pct') or 0)),
            status=_activity_status(row.get('status')),
            sort_order=sort_order,
            updated_at=now,
        )
        by_id[activity.id] = activity
        id_map[activity.id] = activity.id
        if client_id_int is not None:
            id_map[client_id_int] = activity.id

    return id_map


def _uses_activity_flow(payload: dict[str, Any]) -> bool:
    if 'activity_periods' in payload:
        return True
    activities = payload.get('activities') or []
    if not activities:
        return False
    return any(
        row.get('weight_pct') is not None
        or row.get('planned_budget_usd') is not None
        or row.get('title_en')
        or row.get('temp_id') is not None
        for row in activities
    )


def save_project_monitoring_data(project: DevelopmentProject, payload: dict[str, Any]) -> dict[str, Any]:
    now = timezone.now()
    used_activity_flow = False

    if _uses_activity_flow(payload):
        used_activity_flow = True
        id_map: dict[int, int] = {}
        if payload.get('replace_activities'):
            project.activity_periods.all().delete()
            project.activities.all().delete()
        if 'activities' in payload:
            id_map = _upsert_activities(project, payload.get('activities') or [], now)
        if 'activity_periods' in payload:
            _save_activity_periods(project, payload.get('activity_periods') or [], now, id_map)

        activities = list(project.activities.order_by('sort_order', 'planned_start', 'id'))
        activity_periods_map: dict[int, list[PeriodPoint]] = {}
        for activity in activities:
            periods = [_activity_period_from_model(row) for row in activity.periods.order_by('period_date')]
            activity_periods_map[activity.id] = periods
            _update_activity_progress(activity, periods)

        rolled = _rollup_project_periods(project, activities, activity_periods_map)
        _sync_project_progress_periods(project, rolled)

    if 'periods' in payload and not used_activity_flow:
        schedule_start, schedule_end = _project_schedule(project)
        project.progress_periods.all().delete()
        for index, row in enumerate(payload.get('periods') or []):
            period_date = _parse_date(row.get('period_date'))
            if not period_date:
                continue
            if period_date < schedule_start or period_date > schedule_end:
                continue
            ProjectProgressPeriod.objects.create(
                project=project,
                period_date=period_date,
                planned_physical_pct=Decimal(str(row.get('planned_physical_pct') or 0)),
                actual_physical_pct=Decimal(str(row['actual_physical_pct']))
                if row.get('actual_physical_pct') is not None
                else None,
                planned_cumulative_spend_usd=Decimal(str(row.get('planned_cumulative_spend_usd') or 0)),
                actual_cumulative_spend_usd=Decimal(str(row['actual_cumulative_spend_usd']))
                if row.get('actual_cumulative_spend_usd') is not None
                else None,
                notes=row.get('notes') or '',
                updated_at=now,
            )

    if 'milestones' in payload:
        project.milestones.all().delete()
        for index, row in enumerate(payload.get('milestones') or []):
            planned_date = _parse_date(row.get('planned_date'))
            if not planned_date:
                continue
            ProjectMilestone.objects.create(
                project=project,
                code=row.get('code') or '',
                title_en=row['title_en'],
                title_ar=row.get('title_ar') or '',
                milestone_type=row.get('milestone_type') or MilestoneType.DELIVERABLE,
                planned_date=planned_date,
                actual_date=_parse_date(row.get('actual_date')),
                weight_pct=Decimal(str(row.get('weight_pct') or 0)),
                planned_value_usd=Decimal(str(row['planned_value_usd']))
                if row.get('planned_value_usd') is not None
                else None,
                actual_value_usd=Decimal(str(row['actual_value_usd']))
                if row.get('actual_value_usd') is not None
                else None,
                status=row.get('status') or MilestoneStatus.PLANNED,
                sort_order=int(row.get('sort_order') or index),
                updated_at=now,
            )

    if 'activities' in payload and not used_activity_flow:
        project.activities.all().delete()
        project.activity_periods.all().delete()
        for index, row in enumerate(payload.get('activities') or []):
            planned_start = _parse_date(row.get('planned_start'))
            planned_end = _parse_date(row.get('planned_end'))
            if not planned_start or not planned_end:
                continue
            ProjectActivity.objects.create(
                project=project,
                title_en=row['title_en'],
                title_ar=row.get('title_ar') or '',
                category=row.get('category') or '',
                planned_start=planned_start,
                planned_end=planned_end,
                actual_start=_parse_date(row.get('actual_start')),
                actual_end=_parse_date(row.get('actual_end')),
                weight_pct=Decimal(str(row.get('weight_pct') or 0)),
                planned_budget_usd=Decimal(str(row.get('planned_budget_usd') or 0)),
                progress_pct=Decimal(str(row.get('progress_pct') or 0)),
                status=row.get('status') or ActivityStatus.NOT_STARTED,
                sort_order=int(row.get('sort_order') or index),
                updated_at=now,
            )

    project.updated_at = now
    project.save(update_fields=['updated_at'])
    return build_project_monitoring_payload(project)
