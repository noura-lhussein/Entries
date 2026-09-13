from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal
from functools import lru_cache
from typing import Any

from django.db.models import Q
from projects.targets_info import list_info_targets, target_as_namespace

from .info_scope import electricity_category_id_override, electricity_category_name
from .models import OperationalTarget
from .target_catalog import SNAPSHOT_TARGET_MAP, TARGET_METRIC_BY_KEY, TargetMetricSpec


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
            electricity_category_name(),
            settings_id=electricity_category_id_override(),
            env_id_name='ELECTRICITY_TITLE_CATEGORY_ID',
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
    return (
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
    actual: float | Decimal | None,
    target: float | Decimal | None,
    *,
    higher_is_better: bool = True,
) -> float | None:
    if actual is None or target is None or float(target) == 0:
        return None
    ratio = (float(actual) / float(target)) * 100
    if not higher_is_better:
        if float(actual) == 0:
            return 100.0
        ratio = (float(target) / float(actual)) * 100
    return round(ratio, 1)


def target_status(achievement: float | None, *, higher_is_better: bool = True) -> str:
    if achievement is None:
        return 'neutral'
    if achievement < 80:
        return 'critical'
    if achievement < 95:
        return 'warning'
    return 'ok'


def national_targets_for_snapshot(snapshot_date: date) -> dict[str, Decimal | None]:
    result: dict[str, Decimal | None] = {}
    for snapshot_field, metric_key in SNAPSHOT_TARGET_MAP.items():
        result[snapshot_field] = resolve_target_value(
            metric_key,
            snapshot_date,
            scope_type=OperationalTarget.ScopeType.NATIONAL,
        )
    return result


def _actual_plant_generation(plant_code: str, on_date: date) -> Decimal | None:
    """Sum of that plant's units' 24h generation from Info for one date.

    KpiDailySnapshot/DailyGeneration (the legacy tables this used to read)
    have no live writer anymore — every call used to silently return None.
    """
    from electricity.info_dashboard import build_info_report_detail_payload

    payload = build_info_report_detail_payload(on_date)
    if not payload:
        return None
    total = None
    for row in payload.get('generation_unit_readings') or []:
        if (row.get('plant_code') or '').lower() != plant_code.lower():
            continue
        val = row.get('generation_mwh_24h')
        if val is not None:
            total = (total or 0.0) + val
    return Decimal(str(total)) if total is not None else None


def _actual_national(metric_key: str, on_date: date) -> Decimal | None:
    """National target actuals computed from accepted Info for one date.

    KpiDailySnapshot (the legacy source this used to read) is fed by a batch
    job that no longer runs — every call used to silently return None. Info
    only carries the *raw* daily-report metrics, not these pre-computed KPIs,
    so most of these are derived here rather than a direct field lookup:

    - total_generation_mwh: direct — Info's `total_generation_mwh_24h`.
    - peak_demand_mw: no true "demand" figure exists in the daily report;
      `gov_consumed_mw` (aggregate governorate consumption) is the closest
      available proxy for realized national demand.
    - supply_demand_gap_mw: gov_consumed_mw − available_generated_power
      (positive = demand exceeds what's actually available → shortage,
      matching this metric's higher_is_better=False convention).
    - capacity_factor_percent: total_generation_mwh_24h ÷ nominal_capacity_mwh.
    - plant_availability_percent: sum(available_mw) ÷ sum(nominal_mw) across
      every generation unit reported that date (entity-level Info, not a
      national metric).
    - renewable_share_percent: approximation — Info only carries hydro's
      actual *output* (hydro_output_mw); solar/wind only have installed
      *capacity* (solar_capacity_mw/wind_capacity_mw), not actual generation,
      so they cannot be safely included without overstating renewable share.
      This is (hydro_output_mw × 24) ÷ total_generation_mwh_24h — a
      hydro-only, likely understated, share.
    """
    from electricity.info_dashboard import build_info_report_detail_payload

    payload = build_info_report_detail_payload(on_date)
    if not payload:
        return None
    metrics = {
        row['metric_key']: row['value']
        for row in payload.get('metrics') or []
        if row.get('value') is not None
    }

    if metric_key == 'total_generation_mwh':
        val = metrics.get('total_generation_mwh_24h')
    elif metric_key == 'peak_demand_mw':
        val = metrics.get('gov_consumed_mw')
    elif metric_key == 'supply_demand_gap_mw':
        consumed = metrics.get('gov_consumed_mw')
        available = metrics.get('available_generated_power')
        val = (consumed - available) if consumed is not None and available is not None else None
    elif metric_key == 'capacity_factor_percent':
        generation = metrics.get('total_generation_mwh_24h')
        nominal = metrics.get('nominal_capacity_mwh')
        val = round(generation / nominal * 100, 1) if generation is not None and nominal else None
    elif metric_key == 'renewable_share_percent':
        hydro_mw = metrics.get('hydro_output_mw')
        total_generation = metrics.get('total_generation_mwh_24h')
        val = (
            round(hydro_mw * 24 / total_generation * 100, 1)
            if hydro_mw is not None and total_generation
            else None
        )
    elif metric_key == 'plant_availability_percent':
        units = payload.get('generation_unit_readings') or []
        available_sum = sum(u['available_mw'] for u in units if u.get('available_mw') is not None)
        nominal_sum = sum(u['nominal_mw'] for u in units if u.get('nominal_mw') is not None)
        val = round(available_sum / nominal_sum * 100, 1) if nominal_sum else None
    else:
        val = None
    return Decimal(str(val)) if val is not None else None


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

    if actual_value is None and scope_type == OperationalTarget.ScopeType.PLANT and scope_code:
        actual_value = _actual_plant_generation(scope_code, on_date)
    if actual_value is None and scope_type == OperationalTarget.ScopeType.NATIONAL:
        actual_value = _actual_national(metric_key, on_date)

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


def _actual_mtd(metric_key: str, month_start: date, on_date: date, *, scope_type: str, scope_code: str = '') -> Decimal | None:
    """Month-to-date actual, summed from Info across [month_start, on_date].

    DailyGeneration (the legacy table this used to read) has no live writer —
    every call used to silently return None.
    """
    from electricity.info_dashboard import (
        TITLE_NATIONAL,
        TITLE_PLANT,
        TITLE_UNITS,
        _fact_number,
        _group_by_title_rowkey,
        _load_bundle_for_row_keys,
        _row_keys_in_window,
    )

    start_s, end_s = month_start.isoformat(), on_date.isoformat()

    if scope_type == OperationalTarget.ScopeType.PLANT and scope_code:
        if metric_key != 'generation_mwh':
            return None
        from .models import PowerPlant

        plant = PowerPlant.objects.filter(code__iexact=scope_code).first()
        if not plant:
            return None
        row_keys = _row_keys_in_window((TITLE_UNITS, TITLE_PLANT), start_s, end_s)
        if not row_keys:
            return None
        all_rows, attrs, titles, entity_by_row_key = _load_bundle_for_row_keys(row_keys)
        by_title = _group_by_title_rowkey(all_rows, attrs, titles, entity_by_row_key)
        total = None
        for item in list(by_title.get(TITLE_UNITS, [])) + list(by_title.get(TITLE_PLANT, [])):
            d = item.get('report_date') or ''
            if not (start_s <= d <= end_s) or item.get('entity_id') != plant.id:
                continue
            val = _fact_number(
                item['facts'],
                'التوليد 24س (ميجاواط ساعة)', 'التوليد (ميجاواط ساعة)', 'التوليد', 'generation_mwh',
            )
            if val is not None:
                total = (total or 0.0) + val
        return Decimal(str(total)) if total is not None else None

    if metric_key == 'total_generation_mwh' and scope_type == OperationalTarget.ScopeType.NATIONAL:
        row_keys = _row_keys_in_window((TITLE_NATIONAL,), start_s, end_s)
        if not row_keys:
            return None
        all_rows, attrs, titles, entity_by_row_key = _load_bundle_for_row_keys(row_keys)
        by_title = _group_by_title_rowkey(all_rows, attrs, titles, entity_by_row_key)
        total = None
        for item in by_title.get(TITLE_NATIONAL, []):
            d = item.get('report_date') or ''
            if not (start_s <= d <= end_s):
                continue
            val = _fact_number(item['facts'], 'total_generation_mwh_24h')
            if val is not None:
                total = (total or 0.0) + val
        return Decimal(str(total)) if total is not None else None

    return None


def build_monthly_rollup(
    on_date: date,
    *,
    scope_type: str = OperationalTarget.ScopeType.NATIONAL,
    scope_code: str = '',
) -> dict[str, Any]:
    month_start, _ = _month_bounds(on_date)
    days_in_month = calendar.monthrange(on_date.year, on_date.month)[1]
    elapsed = (on_date - month_start).days + 1

    info_keys = [
        t['metric_key']
        for t in _info_target_rows()
        if t['scope_type'] == scope_type
        and (t.get('scope_code') or '') == (scope_code or '')
        and t['period_type'] == OperationalTarget.PeriodType.MONTHLY
        and t['period_start'] == month_start
    ]
    keys = list(dict.fromkeys(info_keys))
    if not keys:
        keys = list(
            OperationalTarget.objects.filter(
                scope_type=scope_type,
                scope_code=scope_code or '',
                period_type=OperationalTarget.PeriodType.MONTHLY,
                period_start=month_start,
            )
            .values_list('metric_key', flat=True)
            .distinct()
        )
    if not keys:
        keys = [k for k in NATIONAL_KPI_METRIC_KEYS if k]

    metrics = []
    for metric_key in keys:
        monthly_row = resolve_target(metric_key, on_date, scope_type=scope_type, scope_code=scope_code)
        monthly_target = float(monthly_row.target_value) if monthly_row else None
        mtd_target = (monthly_target / days_in_month * elapsed) if monthly_target else None
        mtd_actual = _actual_mtd(metric_key, month_start, on_date, scope_type=scope_type, scope_code=scope_code)
        mtd_actual_f = float(mtd_actual) if mtd_actual is not None else None
        spec = TARGET_METRIC_BY_KEY.get(metric_key)
        higher = spec.higher_is_better if spec else True
        achieve = achievement_pct(mtd_actual_f, mtd_target, higher_is_better=higher)
        metrics.append({
            **build_target_comparison(metric_key, on_date, scope_type=scope_type, scope_code=scope_code),
            'mtd_actual': mtd_actual_f,
            'mtd_target': mtd_target,
            'month_plan': monthly_target,
            'day_of_month': elapsed,
            'days_in_month': days_in_month,
            'mtd_achievement_pct': achieve,
        })

    return {
        'date': on_date.isoformat(),
        'scope_type': scope_type,
        'scope_code': scope_code,
        'metrics': metrics,
    }
NATIONAL_KPI_METRIC_KEYS: tuple[str, ...] = tuple(dict.fromkeys(SNAPSHOT_TARGET_MAP.values()))
