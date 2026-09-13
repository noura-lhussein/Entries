from __future__ import annotations

import math
from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import ExtractMonth, ExtractYear

from .basin_geometry import (
    circle_polygon,
    convex_hull,
    expand_polygon,
    polygon_area_km2,
    ring_to_geojson_polygon,
)
from .models import RainfallBasin, RainfallObservation, RainfallStation
from .official_basin_geometry import load_official_basin_features

MONTH_LABELS_EN = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]
MONTH_LABELS_AR = [
    'كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران',
    'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول',
]


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


def _observation_qs(
    year: int,
    basin_slug: str | None = None,
    governorate: str | None = None,
):
    qs = RainfallObservation.objects.filter(observation_date__year=year)
    if basin_slug:
        qs = qs.filter(station__basin__slug=basin_slug)
    if governorate:
        qs = qs.filter(station__governorate=governorate)
    return qs


def _distinct_governorates(
    year: int,
    basin_slug: str | None = None,
) -> list[str]:
    station_ids = RainfallObservation.objects.filter(
        observation_date__year=year,
    ).values_list('station_id', flat=True).distinct()
    qs = RainfallStation.objects.filter(
        id__in=station_ids).exclude(governorate='')
    if basin_slug:
        qs = qs.filter(basin__slug=basin_slug)
    return sorted(
        qs.values_list('governorate', flat=True).order_by().distinct()
    )


def _year_total(
    year: int,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> float:
    qs = _observation_qs(year, basin_slug, governorate)
    return float(qs.aggregate(total=Sum('precipitation_mm'))['total'] or 0)


def _rain_days(
    year: int,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> int:
    return _observation_qs(year, basin_slug, governorate).filter(precipitation_mm__gt=0).count()


def _active_stations(
    year: int,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> int:
    qs = _observation_qs(year, basin_slug, governorate)
    return qs.values('station_id').distinct().count()


def _max_daily_event(
    year: int,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> dict[str, Any] | None:
    qs = _observation_qs(year, basin_slug, governorate).select_related(
        'station', 'station__basin')
    row = qs.order_by('-precipitation_mm').first()
    if not row or row.precipitation_mm <= 0:
        return None
    return {
        'station_name': row.station.name,
        'governorate': row.station.governorate,
        'date': row.observation_date.isoformat(),
        'precipitation_mm': float(row.precipitation_mm),
    }


def _build_insights(
    *,
    year: int,
    basin_slug: str | None,
    governorate: str | None,
    total_mm: float,
    prev_total_mm: float,
    rain_days: int,
    max_event: dict[str, Any] | None,
    wettest_basin: dict[str, Any] | None,
    driest_basin: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []

    if prev_total_mm > 0:
        change_pct = round((total_mm - prev_total_mm) / prev_total_mm * 100, 1)
        if change_pct >= 15:
            insights.append({
                'id': 'yoy-increase',
                'text_en': f'National rainfall is {change_pct:+.1f}% vs {year - 1} — above-normal year.',
                'text_ar': f'الهطول على المستوى الوطني أعلى بنسبة {change_pct:+.1f}% مقارنة بـ {year - 1}.',
                'severity': 'info',
            })
        elif change_pct <= -15:
            insights.append({
                'id': 'yoy-decrease',
                'text_en': f'Rainfall is {change_pct:+.1f}% below {year - 1} — monitor drought risk.',
                'text_ar': f'الهطول أقل بنسبة {abs(change_pct):.1f}% عن {year - 1} — راقب مخاطر الجفاف.',
                'severity': 'warning',
            })

    if wettest_basin and driest_basin and not basin_slug and not governorate:
        insights.append({
            'id': 'basin-contrast',
            'text_en': (
                f'{wettest_basin["name_en"]} received the highest basin total '
                f'({wettest_basin["total_mm"]:.0f} mm) vs {driest_basin["name_en"]} '
                f'({driest_basin["total_mm"]:.0f} mm).'
            ),
            'text_ar': (
                f'سجّل {wettest_basin["name_ar"]} أعلى مجمل هطول '
                f'({wettest_basin["total_mm"]:.0f} ملم) مقابل {driest_basin["name_ar"]} '
                f'({driest_basin["total_mm"]:.0f} ملم).'
            ),
            'severity': 'info',
        })

    if max_event:
        insights.append({
            'id': 'max-event',
            'text_en': (
                f'Peak daily event: {max_event["precipitation_mm"]:.1f} mm at '
                f'{max_event["station_name"]} on {max_event["date"]}.'
            ),
            'text_ar': (
                f'أقصى حدث يومي: {max_event["precipitation_mm"]:.1f} ملم في '
                f'{max_event["station_name"]} بتاريخ {max_event["date"]}.'
            ),
            'severity': 'critical' if max_event['precipitation_mm'] >= 100 else 'info',
        })

    avg_rain_day = total_mm / rain_days if rain_days else 0
    if rain_days:
        insights.append({
            'id': 'rain-day-intensity',
            'text_en': (
                f'{rain_days:,} rain days recorded; average intensity on wet days '
                f'is {avg_rain_day:.1f} mm.'
            ),
            'text_ar': (
                f'سُجّل {rain_days:,} يوماً ممطراً؛ متوسط شدة الهطول في أيام المطر '
                f'{avg_rain_day:.1f} ملم.'
            ),
            'severity': 'info',
        })

    if not insights:
        insights.append({
            'id': 'no-data',
            'text_en': 'Import rainfall station data to unlock executive insights.',
            'text_ar': 'استورد بيانات محطات الهطول لتفعيل الرؤى التنفيذية.',
            'severity': 'info',
        })

    return insights


def _basin_geometry_from_stations(points: list[tuple[float, float]]) -> tuple[dict[str, Any], float, str]:
    if len(points) >= 3:
        hull = expand_polygon(convex_hull(points))
        area = polygon_area_km2(hull)
        return ring_to_geojson_polygon(hull), area, 'station_hull'
    if len(points) == 2:
        mid_lon = (points[0][0] + points[1][0]) / 2
        mid_lat = (points[0][1] + points[1][1]) / 2
        return circle_polygon(mid_lon, mid_lat, radius_km=35), math.pi * 35**2, 'station_buffer'
    lon, lat = points[0]
    return circle_polygon(lon, lat, radius_km=30), math.pi * 30**2, 'station_buffer'


def build_basin_choropleth(
    year: int | None = None,
    *,
    basin_metrics: dict[str, dict[str, float | int]] | None = None,
) -> dict[str, Any]:
    """Choropleth polygons from basin GIS / station hulls.

    Metrics come from ``basin_metrics`` when provided (Info-first dashboards).
    Otherwise fall back to ``RainfallObservation`` aggregates for ``year``.
    """
    features: list[dict[str, Any]] = []
    color_values: list[float] = []
    official_geometries = load_official_basin_features()
    using_official = bool(official_geometries)

    for basin in RainfallBasin.objects.order_by('name_en'):
        station_rows = RainfallStation.objects.filter(
            basin=basin,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        points = [(float(row.longitude), float(row.latitude))
                  for row in station_rows]

        official = official_geometries.get(basin.slug)
        if official:
            geometry = official['geometry']
            area_km2 = official['area_km2']
            geometry_source = official['geometry_source']
        elif points:
            geometry, area_km2, geometry_source = _basin_geometry_from_stations(
                points)
        else:
            continue

        if not geometry.get('coordinates'):
            continue

        if basin_metrics is not None:
            metrics = basin_metrics.get(basin.slug) or {}
            total_mm = float(metrics.get('total_mm') or 0)
            station_count = int(metrics.get('station_count') or 0)
        else:
            if year is None:
                continue
            total_mm = _year_total(year, basin.slug)
            station_count = _active_stations(year, basin.slug)
        density = total_mm / area_km2 if area_km2 > 0 else 0.0
        avg_mm = total_mm / station_count if station_count else 0.0
        color_values.append(avg_mm)

        features.append({
            'type': 'Feature',
            'geometry': geometry,
            'properties': {
                'slug': basin.slug,
                'name_en': basin.name_en,
                'name_ar': basin.name_ar,
                'total_mm': round(total_mm, 1),
                'density_mm_km2': round(density, 3),
                'avg_mm_per_station': round(avg_mm, 1),
                'choropleth_value': round(avg_mm, 1),
                'station_count': station_count,
                'area_km2': round(area_km2, 1),
                'geometry_source': geometry_source,
            },
        })

    if using_official:
        note_en = 'Basin outlines from the official MOE Syria hydrological basins map.'
        note_ar = 'حدود الأحواض من خريطة الأحواض الهيدرولوجية الرسمية لوزارة الطاقة.'
    else:
        note_en = (
            'Basin outlines are approximate (derived from station locations). '
            'Official watershed GIS can replace these boundaries.'
        )
        note_ar = (
            'حدود الأحواض تقريبية (مشتقة من مواقع المحطات). '
            'يمكن استبدالها بحدود GIS رسمية للأحواض عند توفرها.'
        )

    return {
        'type': 'FeatureCollection',
        'features': features,
        'scale': {
            'metric': 'avg_mm_per_station',
            'min_value': round(min(color_values), 1) if color_values else 0,
            'max_value': round(max(color_values), 1) if color_values else 0,
            'unit_en': 'mm',
            'unit_ar': 'ملم',
            'label_en': 'Average rainfall per station',
            'label_ar': 'متوسط الهطول لكل محطة',
            'geometry_note_en': note_en,
            'geometry_note_ar': note_ar,
        },
    }


def build_rainfall_dashboard_payload(
    *,
    year: int | None = None,
    basin_slug: str | None = None,
    governorate: str | None = None,
) -> dict[str, Any]:
    years_qs = (
        RainfallObservation.objects.annotate(y=ExtractYear('observation_date'))
        .values_list('y', flat=True)
        .distinct()
        .order_by('-y')
    )
    available_years = list(years_qs)
    if not available_years:
        return {
            'status': 'empty',
            'filters': {'years': [], 'basins': [], 'governorates': []},
            'selected_year': None,
            'selected_basin': basin_slug,
            'selected_governorate': governorate,
            'kpis': [],
            'insights': [{
                'id': 'empty',
                'text_en': 'No rainfall records imported yet. Run import_rainfall_data management command.',
                'text_ar': 'لم تُستورد بيانات الهطول بعد. نفّذ أمر import_rainfall_data.',
                'severity': 'info',
            }],
            'charts': {},
            'map': {'stations': [], 'basin_choropleth': None},
        }

    selected_year = year if year in available_years else available_years[0]
    prev_year = selected_year - 1

    basins = list(
        RainfallBasin.objects.order_by('name_en').values(
            'slug', 'name_en', 'name_ar'),
    )
    governorates = _distinct_governorates(selected_year, basin_slug)
    if governorate and governorate not in governorates:
        governorate = None

    total_mm = _year_total(selected_year, basin_slug, governorate)
    prev_total_mm = (
        _year_total(prev_year, basin_slug, governorate)
        if prev_year in available_years
        else 0
    )
    rain_days = _rain_days(selected_year, basin_slug, governorate)
    active_stations = _active_stations(selected_year, basin_slug, governorate)
    max_event = _max_daily_event(selected_year, basin_slug, governorate)

    delta_pct = None
    if prev_total_mm > 0:
        delta_pct = round((total_mm - prev_total_mm) / prev_total_mm * 100, 1)

    avg_per_station = total_mm / active_stations if active_stations else 0

    basin_totals: list[dict[str, Any]] = []
    for basin in RainfallBasin.objects.order_by('name_en'):
        basin_total = _year_total(selected_year, basin.slug, governorate)
        basin_totals.append({
            'slug': basin.slug,
            'name_en': basin.name_en,
            'name_ar': basin.name_ar,
            'total_mm': round(basin_total, 1),
        })

    wettest_basin = max(
        basin_totals, key=lambda row: row['total_mm'], default=None)
    driest_basin = min(
        basin_totals, key=lambda row: row['total_mm'], default=None) if basin_totals else None

    kpis = [
        _kpi(
            kpi_id='total-rainfall',
            label_en='Total rainfall',
            label_ar='مجموع الهطول',
            value=round(total_mm, 1),
            unit='mm',
            delta_pct=delta_pct,
            status='ok' if (delta_pct or 0) >= 0 else 'warning',
        ),
        _kpi(
            kpi_id='rain-days',
            label_en='Rain days',
            label_ar='أيام المطر',
            value=rain_days,
            unit='days',
        ),
        _kpi(
            kpi_id='active-stations',
            label_en='Active stations',
            label_ar='المحطات',
            value=active_stations,
        ),
        _kpi(
            kpi_id='avg-per-station',
            label_en='Avg. per station',
            label_ar='متوسط لكل محطة',
            value=round(avg_per_station, 1),
            unit='mm',
        ),
    ]
    if max_event:
        kpis.append(
            _kpi(
                kpi_id='max-daily',
                label_en='Peak daily rainfall',
                label_ar='أقصى هطول يومي',
                value=max_event['precipitation_mm'],
                unit='mm',
                status='critical' if max_event['precipitation_mm'] >= 100 else 'neutral',
            ),
        )

    annual_trend_years = sorted(
        y for y in available_years if y >= selected_year - 10)[-11:]
    annual_trend = {
        'labels': [str(y) for y in annual_trend_years],
        'values': [round(_year_total(y, basin_slug, governorate), 1) for y in annual_trend_years],
    }

    monthly_rows = (
        _observation_qs(selected_year, basin_slug, governorate)
        .annotate(month=ExtractMonth('observation_date'))
        .values('month')
        .annotate(total=Sum('precipitation_mm'))
        .order_by('month')
    )
    monthly_map = {row['month']: float(row['total'] or 0)
                   for row in monthly_rows}
    monthly_distribution = {
        'labels_en': MONTH_LABELS_EN,
        'labels_ar': MONTH_LABELS_AR,
        'values': [round(monthly_map.get(m, 0), 1) for m in range(1, 13)],
    }

    basin_comparison = {
        'labels_en': [row['name_en'] for row in basin_totals],
        'labels_ar': [row['name_ar'] for row in basin_totals],
        'values': [row['total_mm'] for row in basin_totals],
    }

    station_rows = (
        _observation_qs(selected_year, basin_slug, governorate)
        .values('station_id', 'station__name', 'station__governorate', 'station__basin__name_en')
        .annotate(
            total_mm=Sum('precipitation_mm'),
            rain_days=Count('id', filter=Q(precipitation_mm__gt=0)),
            max_daily=Max('precipitation_mm'),
        )
        .order_by('-total_mm')[:10]
    )
    top_stations = [
        {
            'name': row['station__name'],
            'governorate': row['station__governorate'],
            'basin_en': row['station__basin__name_en'],
            'total_mm': round(float(row['total_mm'] or 0), 1),
            'rain_days': row['rain_days'],
            'max_daily_mm': round(float(row['max_daily'] or 0), 1),
        }
        for row in station_rows
    ]

    map_station_qs = RainfallStation.objects.select_related('basin')
    if basin_slug:
        map_station_qs = map_station_qs.filter(basin__slug=basin_slug)
    if governorate:
        map_station_qs = map_station_qs.filter(governorate=governorate)
    map_stations: list[dict[str, Any]] = []
    for station in map_station_qs:
        stats = (
            _observation_qs(selected_year, basin_slug, governorate)
            .filter(station_id=station.id)
            .aggregate(
                total_mm=Sum('precipitation_mm'),
                rain_days=Count('id', filter=Q(precipitation_mm__gt=0)),
                max_daily=Max('precipitation_mm'),
            )
        )
        total = float(stats['total_mm'] or 0)
        if total <= 0 and not stats['rain_days']:
            continue
        map_stations.append({
            'id': station.id,
            'name': station.name,
            'governorate': station.governorate,
            'basin_slug': station.basin.slug,
            'basin_en': station.basin.name_en,
            'basin_ar': station.basin.name_ar,
            'latitude': _float(station.latitude),
            'longitude': _float(station.longitude),
            'total_mm': round(total, 1),
            'rain_days': stats['rain_days'] or 0,
            'max_daily_mm': round(float(stats['max_daily'] or 0), 1),
        })

    insights = _build_insights(
        year=selected_year,
        basin_slug=basin_slug,
        governorate=governorate,
        total_mm=total_mm,
        prev_total_mm=prev_total_mm,
        rain_days=rain_days,
        max_event=max_event,
        wettest_basin=wettest_basin,
        driest_basin=driest_basin,
    )

    data_through = (
        _observation_qs(selected_year, basin_slug, governorate)
        .aggregate(latest=Max('observation_date'))['latest']
    )

    observations_count = _observation_qs(
        selected_year, basin_slug, governorate).count()

    return {
        'status': 'ready',
        'data_through': data_through.isoformat() if isinstance(data_through, date) else None,
        'observations_count': observations_count,
        'active_stations_count': active_stations,
        'filters': {
            'years': available_years,
            'basins': basins,
            'governorates': governorates,
        },
        'selected_year': selected_year,
        'selected_basin': basin_slug,
        'selected_governorate': governorate,
        'kpis': kpis,
        'insights': insights,
        'charts': {
            'annual_trend': annual_trend,
            'monthly_distribution': monthly_distribution,
            'basin_comparison': basin_comparison,
            'top_stations': top_stations,
        },
        'map': {
            'stations': map_stations,
            'basin_choropleth': build_basin_choropleth(year=selected_year),
        },
    }
