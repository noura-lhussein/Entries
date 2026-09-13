from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Avg

from .models import EuphratesCascadeReading


def _float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _kpi(
    *,
    kpi_id: str,
    label_en: str,
    label_ar: str,
    value: float | int | None,
    unit: str = '',
    delta_pct: float | None = None,
    status: str = 'neutral',
) -> dict[str, Any]:
    return {
        'id': kpi_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'unit': unit,
        'delta_pct': delta_pct,
        'status': status,
    }


def _series(readings: list[EuphratesCascadeReading], attr: str) -> list[float | None]:
    return [round(v, 3) if v is not None else None for v in (_float(getattr(r, attr)) for r in readings)]


def _day_labels(readings: list[EuphratesCascadeReading]) -> list[str]:
    return [str(r.reading_date.day) for r in readings]


def _cascade_storage_bcm(readings: list[EuphratesCascadeReading]) -> list[float | None]:
    """Combined Furat + Tishreen lake storage (source values are billion m³)."""
    values: list[float | None] = []
    for reading in readings:
        furat = _float(reading.furat_storage_mcm)
        tishreen = _float(reading.tishreen_storage_mcm)
        if furat is None and tishreen is None:
            values.append(None)
        else:
            values.append(round((furat or 0) + (tishreen or 0), 2))
    return values


def _month_summary(readings: list[EuphratesCascadeReading]) -> dict[str, Any]:
    if not readings:
        return {}

    summary: dict[str, Any] = {}

    inflows = [
        (_float(r.inflow_jarabulus), r.reading_date.day)
        for r in readings
        if r.inflow_jarabulus is not None
    ]
    if inflows:
        min_row = min(inflows, key=lambda row: row[0])
        max_row = max(inflows, key=lambda row: row[0])
        summary['inflow'] = {
            'min': min_row[0],
            'min_day': min_row[1],
            'max': max_row[0],
            'max_day': max_row[1],
            'avg': round(sum(row[0] for row in inflows) / len(inflows), 1),
        }

    generations = [_float(r.total_generation_mwh) for r in readings if r.total_generation_mwh is not None]
    if generations:
        summary['generation'] = {
            'min': round(min(generations), 1),
            'max': round(max(generations), 1),
            'avg': round(sum(generations) / len(generations), 1),
        }

    storage = [v for v in _cascade_storage_bcm(readings) if v is not None]
    if storage:
        summary['storage'] = {
            'start': storage[0],
            'end': storage[-1],
            'change': round(storage[-1] - storage[0], 2),
        }

    return summary


def _build_insights(
    *,
    latest: EuphratesCascadeReading,
    prev: EuphratesCascadeReading | None,
    avg_generation: float | None,
    report_label: str,
    month_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []

    if report_label:
        insights.append({
            'id': 'report-period',
            'text_en': f'Operational readings cover: {report_label}.',
            'text_ar': f'القراءات التشغيلية تغطي: {report_label}.',
            'severity': 'info',
        })

    inflow_summary = month_summary.get('inflow')
    if inflow_summary:
        insights.append({
            'id': 'inflow-range',
            'text_en': (
                f'Jarabulus inflow averaged {inflow_summary["avg"]:,.0f} m³/s, '
                f'peaking at {inflow_summary["max"]:,.0f} m³/s (day {inflow_summary["max_day"]}) '
                f'and bottoming at {inflow_summary["min"]:,.0f} m³/s (day {inflow_summary["min_day"]}).'
            ),
            'text_ar': (
                f'متوسط وارد جرابلس {inflow_summary["avg"]:,.0f} م³/ث، '
                f'بذروة {inflow_summary["max"]:,.0f} م³/ث (اليوم {inflow_summary["max_day"]}) '
                f'وأدنى مستوى {inflow_summary["min"]:,.0f} م³/ث (اليوم {inflow_summary["min_day"]}).'
            ),
            'severity': 'info',
        })

    gen_summary = month_summary.get('generation')
    if gen_summary:
        insights.append({
            'id': 'generation-range',
            'text_en': (
                f'Cascade generation averaged {gen_summary["avg"]:,.0f} MWh/day '
                f'(range {gen_summary["min"]:,.0f}–{gen_summary["max"]:,.0f} MWh).'
            ),
            'text_ar': (
                f'متوسط توليد السلسلة {gen_summary["avg"]:,.0f} MWh/يوم '
                f'(نطاق {gen_summary["min"]:,.0f}–{gen_summary["max"]:,.0f} MWh).'
            ),
            'severity': 'info',
        })

    storage_summary = month_summary.get('storage')
    if storage_summary:
        change = storage_summary['change']
        insights.append({
            'id': 'storage-trend',
            'text_en': (
                f'Combined cascade storage moved from {storage_summary["start"]:.2f} to '
                f'{storage_summary["end"]:.2f} billion m³ '
                f'({change:+.2f} BCM over the month).'
            ),
            'text_ar': (
                f'تحرك التخزين الإجمالي للسلسلة من {storage_summary["start"]:.2f} إلى '
                f'{storage_summary["end"]:.2f} مليار م³ '
                f'({change:+.2f} مليار م³ خلال الشهر).'
            ),
            'severity': 'info' if change >= 0 else 'warning',
        })

    if prev and latest.total_generation_mwh and prev.total_generation_mwh:
        change = (
            (float(latest.total_generation_mwh) - float(prev.total_generation_mwh))
            / float(prev.total_generation_mwh) * 100
        )
        if abs(change) >= 8:
            insights.append({
                'id': 'generation-change',
                'text_en': (
                    f'Total cascade generation moved {change:+.1f}% vs previous day '
                    f'({float(latest.total_generation_mwh):,.0f} MWh).'
                ),
                'text_ar': (
                    f'تحرك إجمالي توليد السلسلة {change:+.1f}% عن اليوم السابق '
                    f'({float(latest.total_generation_mwh):,.0f} MWh).'
                ),
                'severity': 'info' if change >= 0 else 'warning',
            })

    if latest.inflow_jarabulus is not None and latest.furat_level_m is not None:
        insights.append({
            'id': 'hydraulic-balance',
            'text_en': (
                f'Jarabulus inflow {float(latest.inflow_jarabulus):,.0f} m³/s with Euphrates lake '
                f'level at {float(latest.furat_level_m):.2f} m '
                f'({float(latest.furat_storage_mcm or 0):,.2f} billion m³ stored).'
            ),
            'text_ar': (
                f'وارد جرابلس {float(latest.inflow_jarabulus):,.0f} م³/ث ومنسوب بحيرة الفرات '
                f'{float(latest.furat_level_m):.2f} م '
                f'({float(latest.furat_storage_mcm or 0):,.2f} مليار م³ مخزون).'
            ),
            'severity': 'info',
        })

    if avg_generation:
        insights.append({
            'id': 'avg-generation',
            'text_en': f'Average daily generation across the three plants is {avg_generation:,.0f} MWh.',
            'text_ar': f'متوسط التوليد اليومي في المحطات الثلاث {avg_generation:,.0f} MWh.',
            'severity': 'info',
        })

    for dam_id, name_en, name_ar, level, gen in (
        ('tishreen', 'Tishreen', 'تشرين', latest.tishreen_level_m, latest.tishreen_generation_mwh),
        ('furat', 'Euphrates (Tabqa)', 'الفرات', latest.furat_level_m, latest.furat_generation_mwh),
        ('kadiran', 'Baath (Kadiran)', 'كديران', None, latest.kadiran_generation_mwh),
    ):
        if gen is not None and float(gen) <= 0:
            insights.append({
                'id': f'{dam_id}-zero-gen',
                'text_en': f'{name_en} reported zero generation on {latest.reading_date.isoformat()}.',
                'text_ar': f'{name_ar}: توليد صفري بتاريخ {latest.reading_date.isoformat()}.',
                'severity': 'warning',
            })

    return insights[:6]


def build_euphrates_dashboard_payload(
    *,
    month: str | None = None,
) -> dict[str, Any]:
    qs = EuphratesCascadeReading.objects.order_by('reading_date')
    if not qs.exists():
        return {
            'status': 'empty',
            'report_label': '',
            'filters': {'months': []},
            'selected_month': None,
            'kpis': [],
            'insights': [{
                'id': 'empty',
                'text_en': 'No Euphrates cascade readings imported. Run import_euphrates_cascade.',
                'text_ar': 'لم تُستورد قراءات سدود الفرات. نفّذ import_euphrates_cascade.',
                'severity': 'info',
            }],
            'charts': {},
            'month_summary': {},
            'executive': {'labels': [], 'inflow': {'values': []}, 'generation': {'values': []}, 'storage': {'values': []}},
            'dams': [],
            'readings_table': [],
        }

    months = sorted(
        {reading_date.strftime('%Y-%m') for reading_date in qs.dates('reading_date', 'month')},
        reverse=True,
    )
    selected_month = month if month in months else months[0]
    year, mon = (int(p) for p in selected_month.split('-'))

    readings = list(
        qs.filter(reading_date__year=year, reading_date__month=mon).order_by('reading_date'),
    )
    if not readings:
        readings = list(qs.order_by('-reading_date')[:31])
        selected_month = readings[0].reading_date.strftime('%Y-%m') if readings else months[0]

    labels = [r.reading_date.strftime('%Y-%m-%d') for r in readings]
    latest = readings[-1]
    prev = readings[-2] if len(readings) > 1 else None
    report_label = latest.report_label or ''

    avg_total_gen = _float(
        qs.filter(reading_date__year=year, reading_date__month=mon)
        .aggregate(v=Avg('total_generation_mwh'))['v'],
    )

    kpis = [
        _kpi(
            kpi_id='jarabulus-inflow',
            label_en='Jarabulus inflow',
            label_ar='وارد جرابلس',
            value=_float(latest.inflow_jarabulus),
            unit='m³/s',
        ),
        _kpi(
            kpi_id='furat-level',
            label_en='Euphrates lake level',
            label_ar='منسوب بحيرة الفرات',
            value=_float(latest.furat_level_m),
            unit='m',
            delta_pct=(
                round(
                    (float(latest.furat_level_m) - float(prev.furat_level_m))
                    / float(prev.furat_level_m) * 100,
                    2,
                )
                if prev and latest.furat_level_m and prev.furat_level_m
                else None
            ),
        ),
        _kpi(
            kpi_id='tishreen-level',
            label_en='Tishreen dam level',
            label_ar='منسوب سد تشرين',
            value=_float(latest.tishreen_level_m),
            unit='m',
        ),
        _kpi(
            kpi_id='total-generation',
            label_en='Total daily generation',
            label_ar='إجمالي التوليد اليومي',
            value=_float(latest.total_generation_mwh),
            unit='MWh',
            status='ok',
        ),
        _kpi(
            kpi_id='furat-storage',
            label_en='Cascade lake storage',
            label_ar='تخزين بحيرات السلسلة',
            value=round(
                (_float(latest.furat_storage_mcm) or 0) + (_float(latest.tishreen_storage_mcm) or 0),
                2,
            ),
            unit='BCM',
        ),
    ]

    dams = [
        {
            'slug': 'tishreen',
            'name_en': 'Tishreen Dam',
            'name_ar': 'سد تشرين',
            'level_m': _float(latest.tishreen_level_m),
            'storage_bcm': _float(latest.tishreen_storage_mcm),
            'outflow': _float(latest.tishreen_outflow),
            'generation_mwh': _float(latest.tishreen_generation_mwh),
            'max_storage_bcm': 1.883,
        },
        {
            'slug': 'furat',
            'name_en': 'Euphrates Dam (Tabqa)',
            'name_ar': 'سد الفرات (طبقة)',
            'level_m': _float(latest.furat_level_m),
            'storage_bcm': _float(latest.furat_storage_mcm),
            'outflow': _float(latest.furat_outflow),
            'generation_mwh': _float(latest.furat_generation_mwh),
            'max_storage_bcm': 14.1,
        },
        {
            'slug': 'kadiran',
            'name_en': 'Kadiran Dam',
            'name_ar': 'سد كديران',
            'level_m': None,
            'storage_bcm': None,
            'outflow': _float(latest.kadiran_outflow),
            'generation_mwh': _float(latest.kadiran_generation_mwh),
            'max_storage_bcm': 0.09,
        },
    ]

    day_labels = _day_labels(readings)
    month_summary = _month_summary(readings)

    executive = {
        'labels': day_labels,
        'inflow': {'values': _series(readings, 'inflow_jarabulus')},
        'generation': {'values': _series(readings, 'total_generation_mwh')},
        'storage': {'values': _cascade_storage_bcm(readings)},
    }

    charts = {
        'inflow': {'labels': labels, 'values': _series(readings, 'inflow_jarabulus')},
        'levels': {
            'labels': labels,
            'series': [
                {'key': 'tishreen', 'label_en': 'Tishreen', 'label_ar': 'تشرين', 'values': _series(readings, 'tishreen_level_m')},
                {'key': 'furat', 'label_en': 'Euphrates lake', 'label_ar': 'بحيرة الفرات', 'values': _series(readings, 'furat_level_m')},
            ],
        },
        'generation': {
            'labels': labels,
            'series': [
                {'key': 'tishreen', 'label_en': 'Tishreen', 'label_ar': 'تشرين', 'values': _series(readings, 'tishreen_generation_mwh')},
                {'key': 'furat', 'label_en': 'Euphrates', 'label_ar': 'الفرات', 'values': _series(readings, 'furat_generation_mwh')},
                {'key': 'kadiran', 'label_en': 'Kadiran', 'label_ar': 'كديران', 'values': _series(readings, 'kadiran_generation_mwh')},
                {'key': 'total', 'label_en': 'Total', 'label_ar': 'الإجمالي', 'values': _series(readings, 'total_generation_mwh')},
            ],
        },
        'storage': {
            'labels': labels,
            'series': [
                {'key': 'tishreen', 'label_en': 'Tishreen', 'label_ar': 'تشرين', 'values': _series(readings, 'tishreen_storage_mcm')},
                {'key': 'furat', 'label_en': 'Euphrates', 'label_ar': 'الفرات', 'values': _series(readings, 'furat_storage_mcm')},
            ],
        },
    }

    insights = _build_insights(
        latest=latest,
        prev=prev,
        avg_generation=avg_total_gen,
        report_label=report_label,
        month_summary=month_summary,
    )

    data_through = readings[-1].reading_date.isoformat() if readings else None

    return {
        'status': 'ready',
        'data_through': data_through,
        'readings_count': len(readings),
        'report_label': report_label,
        'filters': {'months': months},
        'selected_month': selected_month,
        'kpis': kpis,
        'insights': insights,
        'month_summary': month_summary,
        'executive': executive,
        'charts': charts,
        'dams': dams,
        'readings_table': [
            {
                'date': r.reading_date.isoformat(),
                'inflow_jarabulus': _float(r.inflow_jarabulus),
                'tishreen_level_m': _float(r.tishreen_level_m),
                'furat_level_m': _float(r.furat_level_m),
                'tishreen_storage_bcm': _float(r.tishreen_storage_mcm),
                'furat_storage_bcm': _float(r.furat_storage_mcm),
                'cascade_storage_bcm': (
                    round((_float(r.furat_storage_mcm) or 0) + (_float(r.tishreen_storage_mcm) or 0), 2)
                    if r.furat_storage_mcm is not None or r.tishreen_storage_mcm is not None
                    else None
                ),
                'tishreen_outflow': _float(r.tishreen_outflow),
                'furat_outflow': _float(r.furat_outflow),
                'kadiran_outflow': _float(r.kadiran_outflow),
                'tishreen_generation_mwh': _float(r.tishreen_generation_mwh),
                'furat_generation_mwh': _float(r.furat_generation_mwh),
                'kadiran_generation_mwh': _float(r.kadiran_generation_mwh),
                'total_generation_mwh': _float(r.total_generation_mwh),
            }
            for r in reversed(readings)
        ],
    }
