from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal
from functools import lru_cache
from typing import Any

from django.db.models import Q, Sum
from projects.targets_info import list_info_targets, target_as_namespace

from .info_scope import oil_gas_category_id_override, oil_gas_category_name
from .models import (
    DailyProduction,
    Export,
    Facility,
    OperationalTarget,
    PowerGasRequirement,
    PowerGasSupply,
    RefineryDailyOutput,
)
from .target_catalog import TARGET_METRIC_BY_KEY, TargetMetricSpec


def _month_bounds(on_date: date) -> tuple[date, date]:
    last_day = calendar.monthrange(on_date.year, on_date.month)[1]
    return date(on_date.year, on_date.month, 1), date(on_date.year, on_date.month, last_day)


def _prorate_monthly(value: Decimal, on_date: date) -> Decimal:
    days = calendar.monthrange(on_date.year, on_date.month)[1]
    return (value / Decimal(days)).quantize(Decimal('0.0001'))


@lru_cache(maxsize=1)
def _info_target_rows() -> tuple[dict[str, Any], ...]:
    return tuple(
        list_info_targets(
            oil_gas_category_name(),
            settings_id=oil_gas_category_id_override(),
            env_id_name='OIL_GAS_TITLE_CATEGORY_ID',
        )
    )


def clear_info_targets_cache() -> None:
    _info_target_rows.cache_clear()


def _resolve_from_info(
    metric_key: str,
    on_date: date,
    *,
    scope_type: str,
    scope_code: str,
):
    scope_code = (scope_code or '').strip()
    rows = [
        t
        for t in _info_target_rows()
        if t['metric_key'] == metric_key
        and t['scope_type'] == scope_type
        and (t.get('scope_code') or '') == scope_code
    ]
    if not rows:
        return None
    daily = next(
        (
            t
            for t in rows
            if t['period_type'] == OperationalTarget.PeriodType.DAILY
            and t['period_start'] == on_date
        ),
        None,
    )
    if daily:
        return target_as_namespace(daily)

    month_start, month_end = _month_bounds(on_date)
    monthly_candidates = [
        t
        for t in rows
        if t['period_type'] == OperationalTarget.PeriodType.MONTHLY
        and t['period_start'] <= on_date
        and (t.get('period_end') is None or t['period_end'] >= on_date)
        and t['period_start'] <= month_end
    ]
    if not monthly_candidates:
        return None
    monthly_candidates.sort(key=lambda t: t['period_start'], reverse=True)
    return target_as_namespace(monthly_candidates[0])


def resolve_target(
    metric_key: str,
    on_date: date,
    *,
    scope_type: str = OperationalTarget.ScopeType.NATIONAL,
    scope_code: str = '',
):
    scope_code = (scope_code or '').strip()
    info_row = _resolve_from_info(
        metric_key, on_date, scope_type=scope_type, scope_code=scope_code
    )
    if info_row is not None:
        return info_row

    daily = (
        OperationalTarget.objects.filter(
            metric_key=metric_key,
            scope_type=scope_type,
            scope_code=scope_code,
            period_type=OperationalTarget.PeriodType.DAILY,
            period_start=on_date,
        )
        .order_by('-updated_at')
        .first()
    )
    if daily:
        return daily

    month_start, month_end = _month_bounds(on_date)
    monthly = (
        OperationalTarget.objects.filter(
            metric_key=metric_key,
            scope_type=scope_type,
            scope_code=scope_code,
            period_type=OperationalTarget.PeriodType.MONTHLY,
            period_start__lte=on_date,
        )
        .filter(Q(period_end__gte=on_date) | Q(period_end__isnull=True))
        .filter(period_start__lte=month_end)
        .order_by('-period_start', '-updated_at')
        .first()
    )
    return monthly


def resolve_target_value(
    metric_key: str,
    on_date: date,
    *,
    scope_type: str = OperationalTarget.ScopeType.NATIONAL,
    scope_code: str = '',
) -> Decimal | None:
    row = resolve_target(metric_key, on_date, scope_type=scope_type, scope_code=scope_code)
    if not row:
        return None
    if row.period_type == OperationalTarget.PeriodType.MONTHLY:
        return _prorate_monthly(row.target_value, on_date)
    return row.target_value


def achievement_pct(
    actual: Decimal | float | int | None,
    target: Decimal | float | int | None,
    *,
    higher_is_better: bool = True,
) -> float | None:
    if actual is None or target is None or float(target) == 0:
        return None
    actual_f = float(actual)
    target_f = float(target)
    if higher_is_better:
        return round((actual_f / target_f) * 100, 1)
    if actual_f == 0:
        return 100.0
    return round((target_f / actual_f) * 100, 1)


def target_status(
    achievement: float | None,
    *,
    higher_is_better: bool = True,
) -> str:
    if achievement is None:
        return 'neutral'
    if higher_is_better:
        if achievement < 80:
            return 'critical'
        if achievement < 95:
            return 'warning'
        return 'ok'
    if achievement < 80:
        return 'critical'
    if achievement < 95:
        return 'warning'
    return 'ok'


def _actual_field_production(field_code: str, on_date: date, metric_key: str) -> Decimal | None:
    row = DailyProduction.objects.filter(
        field__code__iexact=field_code,
        production_date=on_date,
    ).first()
    if not row:
        return None
    mapping = {
        'crude_oil_bbl': row.crude_oil_bbl,
        'natural_gas_mmscf': row.natural_gas_mmscf,
        'condensate_bbl': row.condensate_bbl,
    }
    return mapping.get(metric_key)


def _actual_refinery_output(refinery_name: str, on_date: date, metric_key: str) -> Decimal | None:
    row = RefineryDailyOutput.objects.filter(
        refinery__refinery_name__iexact=refinery_name,
        production_date=on_date,
    ).first()
    if not row:
        return None
    mapping = {
        'gasoline_ton': row.gasoline_ton,
        'diesel_ton': row.diesel_ton,
        'fuel_oil_ton': row.fuel_oil_ton,
    }
    return mapping.get(metric_key)


def _actual_facility_value(facility_code: str, on_date: date, metric_key: str) -> Decimal | None:
    facility = Facility.objects.filter(code__iexact=facility_code.strip()).first()
    if not facility:
        return None
    if metric_key == 'supplied_mmscf':
        return PowerGasSupply.objects.filter(supply_date=on_date, facility=facility).aggregate(
            total=Sum('supplied_mmscf'),
        )['total']
    if metric_key == 'required_mmscf':
        return PowerGasRequirement.objects.filter(requirement_date=on_date, facility=facility).aggregate(
            total=Sum('required_mmscf'),
        )['total']
    if metric_key == 'gas_supply_to_power_percent':
        supplied = PowerGasSupply.objects.filter(supply_date=on_date, facility=facility).aggregate(
            total=Sum('supplied_mmscf'),
        )['total']
        required = PowerGasRequirement.objects.filter(requirement_date=on_date, facility=facility).aggregate(
            total=Sum('required_mmscf'),
        )['total']
        if not supplied or not required or required == 0:
            return None
        return ((supplied / required) * Decimal('100')).quantize(Decimal('0.1'))
    return None


def build_target_comparison(
    metric_key: str,
    on_date: date,
    *,
    scope_type: str = OperationalTarget.ScopeType.NATIONAL,
    scope_code: str = '',
    actual_value: Decimal | float | int | None = None,
) -> dict[str, Any]:
    spec: TargetMetricSpec | None = TARGET_METRIC_BY_KEY.get(metric_key)
    target_row = resolve_target(metric_key, on_date, scope_type=scope_type, scope_code=scope_code)
    target_value = resolve_target_value(metric_key, on_date, scope_type=scope_type, scope_code=scope_code)

    if actual_value is None and scope_type == OperationalTarget.ScopeType.FIELD and scope_code:
        actual_value = _actual_field_production(scope_code, on_date, metric_key)
    if actual_value is None and scope_type == OperationalTarget.ScopeType.REFINERY and scope_code:
        actual_value = _actual_refinery_output(scope_code, on_date, metric_key)
    if actual_value is None and scope_type == OperationalTarget.ScopeType.FACILITY and scope_code:
        actual_value = _actual_facility_value(scope_code, on_date, metric_key)
    if actual_value is None and metric_key == 'total_export_bbl':
        actual_value = Export.objects.filter(export_date=on_date).aggregate(total=Sum('crude_bbl'))['total']

    actual_f = float(actual_value) if actual_value is not None else None
    target_f = float(target_value) if target_value is not None else None
    higher = spec.higher_is_better if spec else True
    achieve = achievement_pct(actual_f, target_f, higher_is_better=higher)

    return {
        'metric_key': metric_key,
        'label_en': target_row.label_en if target_row and target_row.label_en else (spec.label_en if spec else metric_key),
        'label_ar': target_row.label_ar if target_row and target_row.label_ar else (spec.label_ar if spec else metric_key),
        'unit': target_row.unit if target_row and target_row.unit else (spec.unit if spec else ''),
        'scope_type': scope_type,
        'scope_code': scope_code,
        'period_type': target_row.period_type if target_row else None,
        'actual_value': actual_f,
        'target_value': target_f,
        'achievement_pct': achieve,
        'status': target_status(achieve, higher_is_better=higher),
        'higher_is_better': higher,
    }


def list_targets_for_scope(
    on_date: date,
    *,
    scope_type: str,
    scope_code: str = '',
) -> list[dict[str, Any]]:
    scope_code = (scope_code or '').strip()
    info_keys = {
        t['metric_key']
        for t in _info_target_rows()
        if t['scope_type'] == scope_type and (t.get('scope_code') or '') == scope_code
    }
    if info_keys:
        keys = sorted(info_keys)
    else:
        keys = (
            OperationalTarget.objects.filter(scope_type=scope_type, scope_code=scope_code)
            .values_list('metric_key', flat=True)
            .distinct()
        )
    return [
        build_target_comparison(
            metric_key,
            on_date,
            scope_type=scope_type,
            scope_code=scope_code,
        )
        for metric_key in keys
    ]


def national_targets_for_snapshot(on_date: date) -> dict[str, Decimal | None]:
    from .target_catalog import SNAPSHOT_TARGET_MAP

    result: dict[str, Decimal | None] = {}
    for snapshot_field, metric_key in SNAPSHOT_TARGET_MAP.items():
        result[snapshot_field] = resolve_target_value(
            metric_key,
            on_date,
            scope_type=OperationalTarget.ScopeType.NATIONAL,
        )
    return result


def _actual_mtd(
    metric_key: str,
    month_start: date,
    on_date: date,
    *,
    scope_type: str,
    scope_code: str = '',
) -> Decimal | None:
    scope_code = (scope_code or '').strip()
    prod_qs = DailyProduction.objects.filter(
        production_date__gte=month_start,
        production_date__lte=on_date,
    )
    if scope_type == OperationalTarget.ScopeType.FIELD and scope_code:
        prod_qs = prod_qs.filter(field__code__iexact=scope_code)

    if metric_key == 'crude_oil_bbl':
        return prod_qs.aggregate(total=Sum('crude_oil_bbl'))['total']
    if metric_key == 'natural_gas_mmscf':
        return prod_qs.aggregate(total=Sum('natural_gas_mmscf'))['total']
    if metric_key == 'condensate_bbl':
        return prod_qs.aggregate(total=Sum('condensate_bbl'))['total']

    export_qs = Export.objects.filter(export_date__gte=month_start, export_date__lte=on_date)
    if metric_key == 'total_export_bbl':
        return export_qs.aggregate(total=Sum('crude_bbl'))['total']
    if metric_key == 'export_revenue_usd':
        return export_qs.aggregate(total=Sum('revenue_usd'))['total']
    return None


def build_monthly_rollup(
    on_date: date,
    *,
    scope_type: str = OperationalTarget.ScopeType.NATIONAL,
    scope_code: str = '',
) -> dict[str, Any]:
    month_start, _ = _month_bounds(on_date)
    days_in_month = calendar.monthrange(on_date.year, on_date.month)[1]
    days_elapsed = (on_date - month_start).days + 1
    scope_code = (scope_code or '').strip()

    info_monthly = [
        target_as_namespace(t)
        for t in _info_target_rows()
        if t['scope_type'] == scope_type
        and (t.get('scope_code') or '') == scope_code
        and t['period_type'] == OperationalTarget.PeriodType.MONTHLY
        and t['period_start'] == month_start
    ]
    if info_monthly:
        monthly_rows = sorted(info_monthly, key=lambda r: r.metric_key)
    else:
        monthly_rows = list(
            OperationalTarget.objects.filter(
                scope_type=scope_type,
                scope_code=scope_code,
                period_type=OperationalTarget.PeriodType.MONTHLY,
                period_start=month_start,
            ).order_by('metric_key')
        )

    metrics: list[dict[str, Any]] = []
    for row in monthly_rows:
        spec = TARGET_METRIC_BY_KEY.get(row.metric_key)
        monthly_target_f = float(row.target_value)
        target_mtd_f = monthly_target_f * days_elapsed / days_in_month
        actual_raw = _actual_mtd(
            row.metric_key,
            month_start,
            on_date,
            scope_type=scope_type,
            scope_code=scope_code,
        )
        actual_f = float(actual_raw) if actual_raw is not None else None
        higher = spec.higher_is_better if spec else True
        achieve_mtd = achievement_pct(actual_f, target_mtd_f, higher_is_better=higher)
        month_progress = achievement_pct(actual_f, monthly_target_f, higher_is_better=higher)

        metrics.append(
            {
                'metric_key': row.metric_key,
                'label_en': row.label_en or (spec.label_en if spec else row.metric_key),
                'label_ar': row.label_ar or (spec.label_ar if spec else row.metric_key),
                'unit': row.unit or (spec.unit if spec else ''),
                'monthly_target': monthly_target_f,
                'target_mtd': round(target_mtd_f, 2),
                'actual_mtd': actual_f,
                'achievement_mtd_pct': achieve_mtd,
                'month_progress_pct': month_progress,
                'status': target_status(achieve_mtd, higher_is_better=higher),
                'higher_is_better': higher,
            }
        )

    return {
        'date': on_date.isoformat(),
        'month_start': month_start.isoformat(),
        'month_label': on_date.strftime('%Y-%m'),
        'days_elapsed': days_elapsed,
        'days_in_month': days_in_month,
        'scope_type': scope_type,
        'scope_code': scope_code,
        'metrics': metrics,
    }
