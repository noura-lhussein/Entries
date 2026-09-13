from __future__ import annotations

import calendar
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.utils import timezone

from .models import (
    ActivityStatus,
    DevelopmentProject,
    ProjectActivity,
    ProjectActivityPeriod,
    ProjectProgressPeriod,
    ProjectStatus,
    Sector,
)

DEFAULT_WEIGHTS = [12, 18, 35, 22, 13]


@dataclass(frozen=True)
class ActivityTemplate:
    title_en: str
    title_ar: str
    category: str
    start_ratio: float
    end_ratio: float


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


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
    value = 1.0 / (1.0 + math.exp(-10.0 * (progress_ratio - 0.5)))
    return round(value * 100.0, 2)


def project_schedule(project: DevelopmentProject) -> tuple[date, date]:
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


def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


INFRASTRUCTURE_TEMPLATE = [
    ActivityTemplate('Feasibility & detailed design', 'دراسة الجدوى والتصميم التفصيلي', 'Design', 0.0, 0.18),
    ActivityTemplate('Procurement & logistics', 'المشتريات واللوجستيات', 'Procurement', 0.12, 0.40),
    ActivityTemplate('Civil works & installation', 'الأعمال المدنية والتركيب', 'Implementation', 0.30, 0.78),
    ActivityTemplate('Testing & commissioning', 'الاختبار والتشغيل', 'Commissioning', 0.65, 0.92),
    ActivityTemplate('Handover & close-out', 'التسليم والإغلاق', 'Close-out', 0.88, 1.0),
]

SECTOR_TEMPLATES: dict[str, list[ActivityTemplate]] = {
    Sector.ELECTRICITY: [
        ActivityTemplate('Grid survey & system design', 'مسح الشبكة وتصميم النظام', 'Design', 0.0, 0.16),
        ActivityTemplate('Equipment procurement', 'توريد المعدات', 'Procurement', 0.10, 0.38),
        ActivityTemplate('Substation & line construction', 'إنشاء المحطات وخطوط النقل', 'Implementation', 0.28, 0.75),
        ActivityTemplate('Energization & commissioning', 'التغذية والتشغيل التجريبي', 'Commissioning', 0.62, 0.90),
        ActivityTemplate('Grid handover & O&M training', 'تسليم الشبكة وتدريب التشغيل', 'Close-out', 0.85, 1.0),
    ],
    Sector.WATER: [
        ActivityTemplate('Hydraulic survey & design', 'المسح الهيدروليكي والتصميم', 'Design', 0.0, 0.17),
        ActivityTemplate('Pumps, pipes & plant procurement', 'توريد المضخات والأنابيب والمنشآت', 'Procurement', 0.11, 0.39),
        ActivityTemplate('Civil works & pipeline laying', 'الأعمال المدنية ومد الأنابيب', 'Implementation', 0.29, 0.76),
        ActivityTemplate('Wet commissioning & water quality tests', 'التشغيل الرطب واختبارات الجودة', 'Commissioning', 0.63, 0.91),
        ActivityTemplate('Beneficiary handover', 'التسليم للمستفيدين', 'Close-out', 0.86, 1.0),
    ],
    Sector.OIL_GAS: [
        ActivityTemplate('Technical assessment & engineering', 'التقييم الفني والهندسة', 'Design', 0.0, 0.15),
        ActivityTemplate('Equipment & materials procurement', 'توريد المعدات والمواد', 'Procurement', 0.10, 0.36),
        ActivityTemplate('Site works & mechanical installation', 'أعمال الموقع والتركيب الميكانيكي', 'Implementation', 0.27, 0.74),
        ActivityTemplate('Pressure testing & system integration', 'اختبار الضغط ودمج الأنظمة', 'Commissioning', 0.60, 0.89),
        ActivityTemplate('Performance verification & close-out', 'التحقق من الأداء والإغلاق', 'Close-out', 0.84, 1.0),
    ],
    Sector.MINERAL: [
        ActivityTemplate('Geological survey & mine planning', 'المسح الجيولوجي وتخطيط المنجم', 'Design', 0.0, 0.20),
        ActivityTemplate('Mining equipment procurement', 'توريد معدات التعدين', 'Procurement', 0.12, 0.38),
        ActivityTemplate('Extraction & processing setup', 'إعداد الاستخراج والمعالجة', 'Implementation', 0.30, 0.78),
        ActivityTemplate('Environmental compliance testing', 'اختبارات الامتثال البيئي', 'Commissioning', 0.64, 0.90),
        ActivityTemplate('Production ramp-up & handover', 'زيادة الإنتاج والتسليم', 'Close-out', 0.86, 1.0),
    ],
    Sector.MULTI: INFRASTRUCTURE_TEMPLATE,
}

TITLE_OVERRIDES: list[tuple[re.Pattern[str], list[ActivityTemplate]]] = [
    (
        re.compile(r'solar|mini[- ]?grid|photovoltaic|pv\b', re.I),
        [
            ActivityTemplate('Solar resource assessment', 'تقييم الموارد الشمسية', 'Design', 0.0, 0.14),
            ActivityTemplate('Panels, inverters & battery procurement', 'توريد الألواح والمحولات والبطاريات', 'Procurement', 0.08, 0.32),
            ActivityTemplate('Mounting structures & DC wiring', 'هياكل التثبيت والتمديدات', 'Implementation', 0.24, 0.68),
            ActivityTemplate('AC integration & commissioning', 'الدمج والتشغيل التجريبي', 'Commissioning', 0.55, 0.86),
            ActivityTemplate('Community handover & metering', 'التسليم للمجتمع والعدادات', 'Close-out', 0.82, 1.0),
        ],
    ),
    (
        re.compile(r'electrif|rural power|distribution network', re.I),
        [
            ActivityTemplate('Load survey & network design', 'مسح الأحمال وتصميم الشبكة', 'Design', 0.0, 0.16),
            ActivityTemplate('Transformers & conductor procurement', 'توريد المحولات والموصلات', 'Procurement', 0.10, 0.36),
            ActivityTemplate('Pole erection & line stringing', 'إنشاء الأعمدة ومد الأسلاك', 'Implementation', 0.28, 0.74),
            ActivityTemplate('Energization & voltage testing', 'التغذية واختبار الجهد', 'Commissioning', 0.60, 0.88),
            ActivityTemplate('Consumer connections & handover', 'توصيل المشتركين والتسليم', 'Close-out', 0.84, 1.0),
        ],
    ),
    (
        re.compile(r'wastewater|sewage|treatment plant', re.I),
        [
            ActivityTemplate('Process design & environmental permit', 'تصميم العمليات والتصاريح', 'Design', 0.0, 0.18),
            ActivityTemplate('Treatment units & pumps procurement', 'توريد وحدات المعالجة والمضخات', 'Procurement', 0.11, 0.38),
            ActivityTemplate('Plant civil works & piping', 'الأعمال المدنية للمحطة والأنابيب', 'Implementation', 0.30, 0.76),
            ActivityTemplate('Biological startup & effluent testing', 'بدء التشغيل البيولوجي واختبار المياه', 'Commissioning', 0.62, 0.90),
            ActivityTemplate('Municipal handover', 'التسليم للبلدية', 'Close-out', 0.86, 1.0),
        ],
    ),
    (
        re.compile(r'pumping station|pump', re.I),
        [
            ActivityTemplate('Hydraulic modelling & station design', 'النمذجة الهيدروليكية وتصميم المحطة', 'Design', 0.0, 0.15),
            ActivityTemplate('Pump sets & control panels procurement', 'توريد المضخات ولوحات التحكم', 'Procurement', 0.09, 0.34),
            ActivityTemplate('Intake works & pump house construction', 'أعمال المأخذ وإنشاء غرفة المضخات', 'Implementation', 0.26, 0.72),
            ActivityTemplate('Wet run & flow calibration', 'التشغيل الرطب ومعايرة التدفق', 'Commissioning', 0.58, 0.87),
            ActivityTemplate('Operator training & handover', 'تدريب المشغلين والتسليم', 'Close-out', 0.83, 1.0),
        ],
    ),
    (
        re.compile(r'irrigation|canal', re.I),
        [
            ActivityTemplate('Canal survey & hydraulic design', 'مسح القناة والتصميم الهيدروليكي', 'Design', 0.0, 0.17),
            ActivityTemplate('Gates, liners & equipment procurement', 'توريد البوابات والبطانات والمعدات', 'Procurement', 0.10, 0.37),
            ActivityTemplate('Canal dredging & lining works', 'تنظيف القناة وأعمال البطانة', 'Implementation', 0.28, 0.75),
            ActivityTemplate('Flow trials & farmer connections', 'تجارب التدفق وربط المزارعين', 'Commissioning', 0.60, 0.89),
            ActivityTemplate('Irrigation season handover', 'التسليم لموسم الري', 'Close-out', 0.85, 1.0),
        ],
    ),
    (
        re.compile(r'groundwater|monitoring network|well', re.I),
        [
            ActivityTemplate('Aquifer mapping & monitoring design', 'رسم الخزان وتصميم المراقبة', 'Design', 0.0, 0.16),
            ActivityTemplate('Sensors, loggers & drilling procurement', 'توريد الحساسات والحفارات', 'Procurement', 0.09, 0.35),
            ActivityTemplate('Well drilling & sensor installation', 'حفر الآبار وتركيب الحساسات', 'Implementation', 0.26, 0.72),
            ActivityTemplate('Telemetry calibration & data validation', 'معايرة الاتصالات والتحقق من البيانات', 'Commissioning', 0.58, 0.86),
            ActivityTemplate('Data centre handover', 'تسليم مركز البيانات', 'Close-out', 0.82, 1.0),
        ],
    ),
    (
        re.compile(r'refinery|maintenance programme|maintenance program', re.I),
        [
            ActivityTemplate('Shutdown planning & scope definition', 'تخطيط التوقف وتحديد النطاق', 'Design', 0.0, 0.12),
            ActivityTemplate('Spare parts & contractor mobilization', 'قطع الغيار وتعبئة المقاولين', 'Procurement', 0.08, 0.30),
            ActivityTemplate('Unit overhaul & mechanical works', 'إصلاح الوحدات والأعمال الميكانيكية', 'Implementation', 0.22, 0.70),
            ActivityTemplate('Leak tests & restart commissioning', 'اختبارات التسرب وإعادة التشغيل', 'Commissioning', 0.55, 0.85),
            ActivityTemplate('Production restoration sign-off', 'اعتماد استئناف الإنتاج', 'Close-out', 0.80, 1.0),
        ],
    ),
    (
        re.compile(r'efficiency|retrofit|energy saving', re.I),
        [
            ActivityTemplate('Energy audit & retrofit design', 'تدقيق الطاقة وتصميم التحديث', 'Design', 0.0, 0.14),
            ActivityTemplate('Efficient equipment procurement', 'توريد المعدات عالية الكفاءة', 'Procurement', 0.08, 0.32),
            ActivityTemplate('Retrofit installation works', 'أعمال تركيب التحديث', 'Implementation', 0.24, 0.68),
            ActivityTemplate('Performance measurement & verification', 'قياس الأداء والتحقق', 'Commissioning', 0.55, 0.84),
            ActivityTemplate('Savings certification & handover', 'اعتماد التوفير والتسليم', 'Close-out', 0.80, 1.0),
        ],
    ),
    (
        re.compile(r'emergency power|backup power|generator', re.I),
        [
            ActivityTemplate('Power needs assessment', 'تقييم احتياجات الطاقة', 'Design', 0.0, 0.10),
            ActivityTemplate('Generators & fuel systems procurement', 'توريد المولدات وأنظمة الوقود', 'Procurement', 0.06, 0.28),
            ActivityTemplate('Pad construction & generator installation', 'إنشاء القواعد وتركيب المولدات', 'Implementation', 0.20, 0.62),
            ActivityTemplate('Load bank testing & synchronization', 'اختبار الحمل والمزامنة', 'Commissioning', 0.50, 0.80),
            ActivityTemplate('Emergency operations handover', 'تسليم عمليات الطوارئ', 'Close-out', 0.76, 1.0),
        ],
    ),
]


def resolve_activity_templates(project: DevelopmentProject) -> list[ActivityTemplate]:
    title = project.title_en or ''
    for pattern, templates in TITLE_OVERRIDES:
        if pattern.search(title):
            return templates
    return SECTOR_TEMPLATES.get(project.sector, INFRASTRUCTURE_TEMPLATE)


def build_activity_definitions(project: DevelopmentProject) -> list[dict[str, Any]]:
    start, end = project_schedule(project)
    duration = max((end - start).days, 1)
    templates = resolve_activity_templates(project)
    budget = _to_float(project.budget_usd)
    spent_ratio = _to_float(project.amount_spent_usd) / budget if budget > 0 else 0.0
    today = timezone.localdate()
    schedule_ratio = min(max((min(today, end) - start).days / duration, 0.0), 1.0)

    rows: list[dict[str, Any]] = []
    for index, template in enumerate(templates):
        weight = DEFAULT_WEIGHTS[index] if index < len(DEFAULT_WEIGHTS) else round(100 / len(templates), 2)
        planned_start = start + timedelta(days=int(duration * template.start_ratio))
        planned_end = start + timedelta(days=int(duration * template.end_ratio))
        planned_budget = round(budget * weight / 100.0, 2)

        progress = 0.0
        status = ActivityStatus.NOT_STARTED
        actual_start = None
        actual_end = None

        if project.status == ProjectStatus.COMPLETED or spent_ratio >= template.end_ratio:
            progress = 100.0
            status = ActivityStatus.COMPLETED
            actual_start = planned_start
            actual_end = min(planned_end, today)
        elif spent_ratio >= template.start_ratio or schedule_ratio >= template.start_ratio:
            span = max(template.end_ratio - template.start_ratio, 0.01)
            if spent_ratio >= template.start_ratio:
                progress = round(min((spent_ratio - template.start_ratio) / span * 100.0, 100.0), 1)
            else:
                progress = round(min((schedule_ratio - template.start_ratio) / span * 100.0, 95.0), 1)
            status = ActivityStatus.ON_HOLD if project.status == ProjectStatus.SUSPENDED else ActivityStatus.IN_PROGRESS
            actual_start = planned_start
            if progress >= 100:
                actual_end = min(planned_end, today)
                status = ActivityStatus.COMPLETED
        elif project.status == ProjectStatus.PLANNED and schedule_ratio < template.start_ratio:
            status = ActivityStatus.NOT_STARTED

        rows.append(
            {
                'title_en': template.title_en,
                'title_ar': template.title_ar,
                'category': template.category,
                'planned_start': planned_start,
                'planned_end': planned_end,
                'actual_start': actual_start,
                'actual_end': actual_end,
                'weight_pct': weight,
                'planned_budget_usd': planned_budget,
                'progress_pct': progress,
                'status': status,
                'sort_order': index,
            },
        )
    return rows


def _build_planned_periods(
    activity: ProjectActivity,
    project: DevelopmentProject,
) -> list[dict[str, Any]]:
    reporting_end = min(activity.planned_end, timezone.localdate())
    month_ends = _iter_month_ends(activity.planned_start, reporting_end)
    if not month_ends:
        month_ends = [activity.planned_end]

    total_months = max(len(_iter_month_ends(activity.planned_start, activity.planned_end)), 1)
    budget = _to_float(activity.planned_budget_usd)
    rows: list[dict[str, Any]] = []
    for index, period_date in enumerate(month_ends, start=1):
        ratio = index / total_months
        planned_physical = _logistic_s_curve(ratio)
        planned_spend = round(budget * planned_physical / 100.0, 2)
        rows.append(
            {
                'period_date': period_date,
                'planned_physical_pct': planned_physical,
                'actual_physical_pct': None,
                'planned_cumulative_spend_usd': planned_spend,
                'actual_cumulative_spend_usd': None,
            },
        )
    return rows


def _apply_example_actuals(
    project: DevelopmentProject,
    activity: ProjectActivity,
    periods: list[dict[str, Any]],
) -> None:
    budget = _to_float(project.budget_usd)
    spent = _to_float(project.amount_spent_usd)
    if budget <= 0 or spent <= 0:
        return

    activity_budget = _to_float(activity.planned_budget_usd)
    activity_spent = round(spent * _to_float(activity.weight_pct) / 100.0, 2)
    if activity_spent <= 0 or activity_budget <= 0:
        return

    progress = _to_float(activity.progress_pct) / 100.0
    if progress <= 0:
        return

    today = timezone.localdate()
    reported: list[dict[str, Any]] = []
    for index, row in enumerate(periods):
        if row['period_date'] > today:
            continue
        month_ratio = (index + 1) / len(periods)
        if month_ratio > progress + 0.08:
            continue
        attainment = min(month_ratio / max(progress, 0.05), 1.0)
        row['actual_physical_pct'] = round(
            min(row['planned_physical_pct'] * (0.86 + 0.14 * attainment), _to_float(activity.progress_pct)),
            2,
        )
        row['actual_cumulative_spend_usd'] = round(
            min(row['planned_cumulative_spend_usd'] * (0.9 + 0.1 * attainment), activity_spent),
            2,
        )
        reported.append(row)

    if reported:
        reported[-1]['actual_cumulative_spend_usd'] = activity_spent
        reported[-1]['actual_physical_pct'] = round(_to_float(activity.progress_pct), 2)


def _value_at_month(periods: list[ProjectActivityPeriod], month: date, field: str) -> float | None:
    value: float | None = None
    for point in periods:
        if point.period_date <= month:
            raw = getattr(point, field)
            value = _to_float(raw) if raw is not None else None
        else:
            break
    return value


def _rollup_project_periods_from_db(
    project: DevelopmentProject,
    activities: list[ProjectActivity],
) -> list[dict[str, Any]]:
    start, end = project_schedule(project)
    reporting_end = min(end, timezone.localdate())
    month_ends = _iter_month_ends(start, reporting_end) or [reporting_end]
    points: list[dict[str, Any]] = []

    for period_date in month_ends:
        planned_physical = 0.0
        actual_physical = 0.0
        has_actual_physical = False
        planned_spend = 0.0
        actual_spend = 0.0
        has_actual_spend = False

        for activity in activities:
            weight = _to_float(activity.weight_pct) / 100.0
            periods = list(activity.periods.order_by('period_date'))
            if period_date < activity.planned_start:
                continue

            planned_physical += weight * (_value_at_month(periods, period_date, 'planned_physical_pct') or 0.0)
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
            {
                'period_date': period_date,
                'planned_physical_pct': round(planned_physical, 2),
                'actual_physical_pct': round(actual_physical, 2) if has_actual_physical else None,
                'planned_cumulative_spend_usd': round(planned_spend, 2),
                'actual_cumulative_spend_usd': round(actual_spend, 2) if has_actual_spend else None,
            },
        )
    return points


def _sync_rolled_up_project_periods(project: DevelopmentProject, now) -> None:
    activities = list(project.activities.order_by('sort_order', 'planned_start', 'id'))
    if not activities:
        return

    rolled = _rollup_project_periods_from_db(project, activities)
    schedule_start, schedule_end = project_schedule(project)
    project.progress_periods.all().delete()
    for row in rolled:
        if row['period_date'] < schedule_start or row['period_date'] > schedule_end:
            continue
        ProjectProgressPeriod.objects.create(
            project=project,
            period_date=row['period_date'],
            planned_physical_pct=Decimal(str(row['planned_physical_pct'])),
            actual_physical_pct=Decimal(str(row['actual_physical_pct'])) if row['actual_physical_pct'] is not None else None,
            planned_cumulative_spend_usd=Decimal(str(row['planned_cumulative_spend_usd'])),
            actual_cumulative_spend_usd=Decimal(str(row['actual_cumulative_spend_usd']))
            if row['actual_cumulative_spend_usd'] is not None
            else None,
            updated_at=now,
        )


def provision_project_activities(
    project: DevelopmentProject,
    *,
    with_example_actuals: bool = False,
    force: bool = False,
) -> list[ProjectActivity]:
    if project.activities.exists() and not force:
        return list(project.activities.order_by('sort_order', 'planned_start', 'id'))

    if force:
        project.activity_periods.all().delete()
        project.activities.all().delete()
        project.progress_periods.all().delete()

    now = timezone.now()
    created: list[ProjectActivity] = []
    for row in build_activity_definitions(project):
        activity = ProjectActivity.objects.create(
            project=project,
            title_en=row['title_en'],
            title_ar=row['title_ar'],
            category=row['category'],
            planned_start=row['planned_start'],
            planned_end=row['planned_end'],
            actual_start=row['actual_start'],
            actual_end=row['actual_end'],
            weight_pct=Decimal(str(row['weight_pct'])),
            planned_budget_usd=Decimal(str(row['planned_budget_usd'])),
            progress_pct=Decimal(str(row['progress_pct'])),
            status=row['status'],
            sort_order=row['sort_order'],
            updated_at=now,
        )
        period_rows = _build_planned_periods(activity, project)
        if with_example_actuals:
            _apply_example_actuals(project, activity, period_rows)

        for period in period_rows:
            ProjectActivityPeriod.objects.create(
                project=project,
                activity=activity,
                period_date=period['period_date'],
                planned_physical_pct=Decimal(str(period['planned_physical_pct'])),
                actual_physical_pct=Decimal(str(period['actual_physical_pct']))
                if period['actual_physical_pct'] is not None
                else None,
                planned_cumulative_spend_usd=Decimal(str(period['planned_cumulative_spend_usd'])),
                actual_cumulative_spend_usd=Decimal(str(period['actual_cumulative_spend_usd']))
                if period['actual_cumulative_spend_usd'] is not None
                else None,
                updated_at=now,
            )
        created.append(activity)

    _sync_rolled_up_project_periods(project, now)
    return created
