from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import Max

from .models import Dam, DamStorageReading


def _float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
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


def _fill_pct(storage_mcm: float, max_storage_mcm: float | None) -> float | None:
    if not max_storage_mcm or max_storage_mcm <= 0:
        return None
    return round(storage_mcm / max_storage_mcm * 100, 1)


def _fill_band(fill_pct: float | None) -> str:
    if fill_pct is None:
        return 'unknown'
    if fill_pct < 15:
        return 'critical'
    if fill_pct < 35:
        return 'low'
    if fill_pct < 65:
        return 'moderate'
    return 'high'


def _latest_readings_for_year(year: int, governorate: str | None = None) -> list[dict[str, Any]]:
    qs = DamStorageReading.objects.filter(reading_date__year=year)
    if governorate:
        qs = qs.filter(dam__governorate=governorate)

    latest_dates = (
        qs.values('dam_id')
        .annotate(latest_date=Max('reading_date'))
    )
    latest_map = {row['dam_id']: row['latest_date'] for row in latest_dates}

    rows: list[dict[str, Any]] = []
    if not latest_map:
        return rows

    readings = (
        DamStorageReading.objects.filter(
            dam_id__in=latest_map.keys(),
            reading_date__year=year,
        )
        .select_related('dam')
        .order_by('dam_id', '-reading_date')
    )

    seen: set[int] = set()
    for reading in readings:
        if reading.dam_id in seen:
            continue
        if reading.reading_date != latest_map[reading.dam_id]:
            continue
        seen.add(reading.dam_id)
        dam = reading.dam
        storage = _float(reading.storage_mcm)
        max_storage = _float(dam.max_storage_mcm) if dam.max_storage_mcm else None
        fill = _fill_pct(storage, max_storage)
        rows.append({
            'dam_id': dam.id,
            'name': dam.name,
            'governorate': dam.governorate,
            'storage_mcm': round(storage, 3),
            'max_storage_mcm': round(max_storage, 3) if max_storage else None,
            'fill_pct': fill,
            'fill_band': _fill_band(fill),
            'reading_date': reading.reading_date.isoformat(),
            'latitude': _float(dam.latitude) if dam.latitude else None,
            'longitude': _float(dam.longitude) if dam.longitude else None,
            'purpose': dam.purpose,
            'dam_type': dam.dam_type,
        })

    return rows


def _aggregate_snapshot(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_storage = sum(row['storage_mcm'] for row in rows)
    capacity_rows = [row for row in rows if row['max_storage_mcm'] and row['max_storage_mcm'] > 0]
    total_capacity = sum(row['max_storage_mcm'] for row in capacity_rows)
    avg_fill = None
    if capacity_rows:
        fills = [row['fill_pct'] for row in capacity_rows if row['fill_pct'] is not None]
        avg_fill = round(sum(fills) / len(fills), 1) if fills else None
    national_fill = round(total_storage / total_capacity * 100, 1) if total_capacity > 0 else None
    critical = sum(1 for row in rows if row['fill_band'] == 'critical')
    low = sum(1 for row in rows if row['fill_band'] == 'low')
    return {
        'total_storage_mcm': round(total_storage, 2),
        'total_capacity_mcm': round(total_capacity, 2),
        'national_fill_pct': national_fill,
        'avg_fill_pct': avg_fill,
        'monitored_dams': len(rows),
        'critical_dams': critical,
        'low_dams': low,
    }


def _build_insights(
    *,
    year: int,
    governorate: str | None,
    snapshot: dict[str, Any],
    prev_snapshot: dict[str, Any],
    rows: list[dict[str, Any]],
    gov_totals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []

    prev_total = prev_snapshot.get('total_storage_mcm', 0)
    total = snapshot['total_storage_mcm']
    if prev_total > 0:
        change_pct = round((total - prev_total) / prev_total * 100, 1)
        if change_pct >= 10:
            insights.append({
                'id': 'storage-up',
                'text_en': (
                    f'National stored volume rose {change_pct:+.1f}% vs {year - 1} '
                    f'({total:,.1f} million m³).'
                ),
                'text_ar': (
                    f'ارتفع الحجم المخزّن وطنياً بنسبة {change_pct:+.1f}% مقارنة بـ {year - 1} '
                    f'({total:,.1f} مليون م³).'
                ),
                'severity': 'info',
            })
        elif change_pct <= -10:
            insights.append({
                'id': 'storage-down',
                'text_en': (
                    f'National stored volume fell {change_pct:+.1f}% vs {year - 1} '
                    f'— review supply planning.'
                ),
                'text_ar': (
                    f'انخفض الحجم المخزّن وطنياً بنسبة {abs(change_pct):.1f}% مقارنة بـ {year - 1} '
                    f'— راجع خطط الإمداد.'
                ),
                'severity': 'warning',
            })

    if snapshot['national_fill_pct'] is not None:
        fill = snapshot['national_fill_pct']
        if fill < 25:
            insights.append({
                'id': 'low-national-fill',
                'text_en': f'National fill level is {fill:.1f}% of registered capacity — drought stress signal.',
                'text_ar': f'نسبة الامتلاء {fill:.1f}% من السعة المسجلة — مؤشر ضغط جفاف.',
                'severity': 'critical' if fill < 15 else 'warning',
            })
        elif fill >= 60:
            insights.append({
                'id': 'healthy-fill',
                'text_en': f'Reservoirs are at {fill:.1f}% of registered capacity — comfortable storage buffer.',
                'text_ar': f'نسبة امتلاء السدود {fill:.1f}% من السعة المسجلة — مخزون مريح.',
                'severity': 'info',
            })

    if snapshot['critical_dams'] > 0:
        insights.append({
            'id': 'critical-dams',
            'text_en': (
                f'{snapshot["critical_dams"]} dam(s) below 15% fill require immediate operational review.'
            ),
            'text_ar': (
                f'{snapshot["critical_dams"]} سداً أقل من 15% امتلاءً تحتاج مراجعة تشغيلية فورية.'
            ),
            'severity': 'critical',
        })

    if gov_totals and not governorate:
        lowest = min(gov_totals, key=lambda row: row['fill_pct'] if row['fill_pct'] is not None else 999)
        highest = max(gov_totals, key=lambda row: row['storage_mcm'])
        if lowest.get('fill_pct') is not None:
            insights.append({
                'id': 'gov-contrast',
                'text_en': (
                    f'{lowest["name_en"]} shows the lowest average fill ({lowest["fill_pct"]:.1f}%) '
                    f'while {highest["name_en"]} holds the largest stored volume '
                    f'({highest["storage_mcm"]:,.1f} MCM).'
                ),
                'text_ar': (
                    f'{lowest["name_ar"]} تسجل أدنى متوسط امتلاء ({lowest["fill_pct"]:.1f}%) '
                    f'بينما {highest["name_ar"]} تحتفظ بأكبر حجم مخزّن '
                    f'({highest["storage_mcm"]:,.1f} مليون متر مكعب).'
                ),
                'severity': 'info',
            })

    critical_rows = sorted(
        [row for row in rows if row['fill_band'] in ('critical', 'low') and row['fill_pct'] is not None],
        key=lambda row: row['fill_pct'] or 0,
    )[:3]
    for row in critical_rows:
        gov_en, gov_ar = _governorate_labels(row['governorate'])
        insights.append({
            'id': f'dam-{row["dam_id"]}-low',
            'text_en': (
                f'{row["name"]} ({gov_en}) at {row["fill_pct"]:.1f}% '
                f'({row["storage_mcm"]:.2f} / {row["max_storage_mcm"]:.2f} MCM).'
            ),
            'text_ar': (
                f'{row["name"]} ({gov_ar}) عند {row["fill_pct"]:.1f}% '
                f'({row["storage_mcm"]:.2f} / {row["max_storage_mcm"]:.2f} مليون متر مكعب).'
            ),
            'severity': 'critical' if row['fill_band'] == 'critical' else 'warning',
        })
        break

    if not insights:
        insights.append({
            'id': 'placeholder',
            'text_en': 'Import dam storage workbooks to unlock executive insights.',
            'text_ar': 'استورد ملفات السدود لتفعيل الرؤى التنفيذية.',
            'severity': 'info',
        })

    return insights[:6]


_GOVERNORATE_EN: dict[str, str] = {
    'حلب': 'Aleppo',
    'السويداء': 'As-Suwayda',
    'دمشق': 'Damascus',
    'درعا': 'Daraa',
    'دير الزور': 'Deir ez-Zor',
    'حماة': 'Hama',
    'حماه': 'Hama',
    'الحسكة': 'Hasakah',
    'حمص': 'Homs',
    'إدلب': 'Idlib',
    'اللاذقية': 'Latakia',
    'القنيطرة': 'Quneitra',
    'الرقة': 'Raqqa',
    'ريف دمشق': 'Rif Dimashq',
    'طرطوس': 'Tartus',
}


def _governorate_labels(name: str) -> tuple[str, str]:
    name_ar = name.strip()
    name_en = _GOVERNORATE_EN.get(name_ar, name_ar)
    return name_en, name_ar


def _distinct_governorates() -> list[str]:
    """Distinct governorate names (Dam Meta.ordering would break plain .distinct())."""
    return sorted(
        Dam.objects.exclude(governorate='')
        .values_list('governorate', flat=True)
        .order_by()
        .distinct(),
    )


def _gov_totals_from_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_gov: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        gov = row['governorate']
        if gov:
            by_gov.setdefault(gov, []).append(row)

    totals: list[dict[str, Any]] = []
    for gov in sorted(by_gov.keys()):
        gov_rows = by_gov[gov]
        gov_snapshot = _aggregate_snapshot(gov_rows)
        name_en, name_ar = _governorate_labels(gov)
        totals.append({
            'slug': gov,
            'name_en': name_en,
            'name_ar': name_ar,
            'storage_mcm': gov_snapshot['total_storage_mcm'],
            'fill_pct': gov_snapshot['national_fill_pct'],
        })
    totals.sort(key=lambda row: row['storage_mcm'], reverse=True)
    return totals


def build_dams_dashboard_payload(
    *,
    year: int | None = None,
    governorate: str | None = None,
) -> dict[str, Any]:
    years_qs = (
        DamStorageReading.objects.dates('reading_date', 'year', order='DESC')
    )
    available_years = sorted({d.year for d in years_qs}, reverse=True)

    if not available_years:
        return {
            'status': 'empty',
            'filters': {'years': [], 'governorates': []},
            'selected_year': None,
            'selected_governorate': governorate,
            'kpis': [],
            'insights': [{
                'id': 'empty',
                'text_en': 'No dam storage records imported yet. Run import_dam_data management command.',
                'text_ar': 'لم تُستورد بيانات السدود بعد. نفّذ أمر import_dam_data.',
                'severity': 'info',
            }],
            'charts': {},
            'map': {'dams': []},
        }

    selected_year = year if year in available_years else available_years[0]
    prev_year = selected_year - 1

    governorates = _distinct_governorates()

    rows = _latest_readings_for_year(selected_year, governorate)
    snapshot = _aggregate_snapshot(rows)
    prev_rows = _latest_readings_for_year(prev_year, governorate) if prev_year in available_years else []
    prev_snapshot = _aggregate_snapshot(prev_rows) if prev_rows else {'total_storage_mcm': 0}

    delta_pct = None
    if prev_snapshot['total_storage_mcm'] > 0:
        delta_pct = round(
            (snapshot['total_storage_mcm'] - prev_snapshot['total_storage_mcm'])
            / prev_snapshot['total_storage_mcm'] * 100,
            1,
        )

    kpis = [
        _kpi(
            kpi_id='total-storage',
            label_en='Total stored volume',
            label_ar='إجمالي المخزون',
            value=snapshot['total_storage_mcm'],
            unit='MCM',
            delta_pct=delta_pct,
            status='ok' if (delta_pct or 0) >= 0 else 'warning',
        ),
        _kpi(
            kpi_id='national-fill',
            label_en='National fill level',
            label_ar='نسبة الامتلاء',
            value=snapshot['national_fill_pct'],
            unit='%',
            status='critical' if (snapshot['national_fill_pct'] or 100) < 20 else 'neutral',
        ),
        _kpi(
            kpi_id='monitored-dams',
            label_en='Monitored dams',
            label_ar='السدود المراقبة',
            value=snapshot['monitored_dams'],
        ),
        _kpi(
            kpi_id='critical-dams',
            label_en='Critical dams (<15%)',
            label_ar='سدود قاربت للحد الميت (<15%)',
            value=snapshot['critical_dams'],
            status='critical' if snapshot['critical_dams'] else 'ok',
        ),
        _kpi(
            kpi_id='avg-fill',
            label_en='Average dam fill',
            label_ar='متوسط امتلاء السدود',
            value=snapshot['avg_fill_pct'],
            unit='%',
        ),
    ]

    gov_totals = _gov_totals_from_rows(rows) if not governorate else []

    trend_years = sorted(y for y in available_years if y >= selected_year - 10)[-11:]
    annual_trend = {
        'labels': [str(y) for y in trend_years],
        'values': [round(_aggregate_snapshot(_latest_readings_for_year(y, governorate))['total_storage_mcm'], 2)
                   for y in trend_years],
    }

    fill_distribution = {
        'labels_en': ['Critical (<15%)', 'Low (15–35%)', 'Moderate (35–65%)', 'High (>65%)', 'Unknown'],
        'labels_ar': ['قاربت للحد الميت (<15%)', 'منخفض (15–35%)', 'متوسط (35–65%)', 'مرتفع (>65%)', 'غير معروف'],
        'values': [
            sum(1 for row in rows if row['fill_band'] == 'critical'),
            sum(1 for row in rows if row['fill_band'] == 'low'),
            sum(1 for row in rows if row['fill_band'] == 'moderate'),
            sum(1 for row in rows if row['fill_band'] == 'high'),
            sum(1 for row in rows if row['fill_band'] == 'unknown'),
        ],
    }

    gov_comparison = {
        'labels_en': [row['name_en'] for row in gov_totals[:10]],
        'labels_ar': [row['name_ar'] for row in gov_totals[:10]],
        'values': [row['storage_mcm'] for row in gov_totals[:10]],
    }

    top_dams = sorted(rows, key=lambda row: row['storage_mcm'], reverse=True)[:10]

    data_through = (
        DamStorageReading.objects.filter(reading_date__year=selected_year)
        .aggregate(latest=Max('reading_date'))['latest']
    )
    readings_qs = DamStorageReading.objects.filter(reading_date__year=selected_year)
    if governorate:
        readings_qs = readings_qs.filter(dam__governorate=governorate)
    readings_count = readings_qs.count()

    insights = _build_insights(
        year=selected_year,
        governorate=governorate,
        snapshot=snapshot,
        prev_snapshot=prev_snapshot,
        rows=rows,
        gov_totals=gov_totals,
    )

    return {
        'status': 'ready',
        'data_through': data_through.isoformat() if isinstance(data_through, date) else None,
        'readings_count': readings_count,
        'dams_with_data_count': len(rows),
        'filters': {
            'years': available_years,
            'governorates': [{'slug': gov, 'name_en': gov, 'name_ar': gov} for gov in governorates],
        },
        'selected_year': selected_year,
        'selected_governorate': governorate,
        'kpis': kpis,
        'insights': insights,
        'charts': {
            'annual_trend': annual_trend,
            'fill_distribution': fill_distribution,
            'governorate_comparison': gov_comparison,
            'top_dams': top_dams,
        },
        'map': {
            'dams': [
                row for row in rows
                if row['latitude'] is not None and row['longitude'] is not None
            ],
        },
    }


def build_dams_map_catalog() -> dict[str, Any]:
    """Lightweight dam list for portal map popups (metadata + latest storage reading)."""
    latest_dates = (
        DamStorageReading.objects.values('dam_id')
        .annotate(latest_date=Max('reading_date'))
    )
    latest_map = {row['dam_id']: row['latest_date'] for row in latest_dates}

    readings_by_dam: dict[int, DamStorageReading] = {}
    if latest_map:
        for reading in (
            DamStorageReading.objects.filter(dam_id__in=latest_map.keys())
            .select_related('dam')
            .order_by('dam_id', '-reading_date')
        ):
            if reading.dam_id in readings_by_dam:
                continue
            if reading.reading_date != latest_map[reading.dam_id]:
                continue
            readings_by_dam[reading.dam_id] = reading

    dams: list[dict[str, Any]] = []
    for dam in Dam.objects.all().order_by('governorate', 'name'):
        reading = readings_by_dam.get(dam.id)
        storage = _float(reading.storage_mcm) if reading else None
        max_storage = _float(dam.max_storage_mcm) if dam.max_storage_mcm else None
        fill = _fill_pct(storage, max_storage) if storage is not None else None
        dams.append({
            'dam_id': dam.id,
            'name': dam.name,
            'governorate': dam.governorate,
            'latitude': _float(dam.latitude) if dam.latitude else None,
            'longitude': _float(dam.longitude) if dam.longitude else None,
            'dam_type': dam.dam_type,
            'purpose': dam.purpose,
            'height_m': _float(dam.height_m) if dam.height_m else None,
            'length_m': _float(dam.length_m) if dam.length_m else None,
            'max_storage_mcm': round(max_storage, 3) if max_storage else None,
            'dead_storage_mcm': _float(dam.dead_storage_mcm) if dam.dead_storage_mcm else None,
            'built_year': dam.built_year,
            'status_note': dam.status_note,
            'storage_mcm': round(storage, 3) if storage is not None else None,
            'fill_pct': fill,
            'reading_date': reading.reading_date.isoformat() if reading else None,
        })

    return {'dams': dams}
