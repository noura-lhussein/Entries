"""Geology dashboard KPIs from accepted Info; GIS remains for map layer geometry."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from functools import lru_cache
from typing import Any

from django.db import DatabaseError, connection
from projects.display_models import ReportDynamicFormsAttribute, ReportDynamicFormsTitle

from geology.info_scope import accepted_infos_for_geology_category, geology_category_name

# Stable codes assigned by report_moe's seed_*_info_forms commands
# (dynamic_forms_title.code) — never match a Title by its Arabic `name`, which
# is free-text and can be renamed at any time from the report_moe UI.
TITLE_NATIONAL = 'geology.national'
TITLE_ORE_PRODUCTION = 'geology.ore_production'

# Bilingual labels for the geology-era layer's `era` property values.
ERA_LABELS: dict[str, tuple[str, str]] = {
    'Cenozoic': ('Cenozoic', 'حقبة الحياة الحديثة'),
    'Quaternary': ('Quaternary', 'الرباعي'),
    'Mesozoic': ('Mesozoic', 'حقبة الحياة الوسطى'),
    'Proterozoic': ('Proterozoic', 'البروتيروزوي'),
    'Paleozoic': ('Paleozoic', 'الباليوزوي'),
}


def _mineral_by_governorate() -> list[dict[str, Any]]:
    """Mineral deposit counts by governorate × mineral type (PostGIS intersect)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              g.pcode,
              g.name_en,
              g.name_ar,
              COALESCE(
                NULLIF(TRIM(m.properties->>'mineral_type_ar'), ''),
                NULLIF(TRIM(m.properties->>'name_ar'), ''),
                NULLIF(TRIM(m.properties->>'name'), ''),
                '—'
              ) AS mineral_type,
              COUNT(*) AS n
            FROM gis_water_feature m
            JOIN gis_admin_feature g
              ON g.layer_id = 'governorate'
             AND ST_Intersects(m.geom, g.geom)
            WHERE m.layer_id = 'geology-minerals'
            GROUP BY g.pcode, g.name_en, g.name_ar, mineral_type
            ORDER BY g.name_en ASC, n DESC, mineral_type ASC
            """
        )
        rows = cursor.fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    for pcode, name_en, name_ar, mineral_type, n in rows:
        key = str(pcode)
        entry = grouped.get(key)
        if entry is None:
            entry = {
                'pcode': key,
                'name_en': str(name_en or key),
                'name_ar': str(name_ar or name_en or key),
                'total': 0,
                'types': [],
            }
            grouped[key] = entry
        count = int(n)
        entry['total'] += count
        entry['types'].append(
            {
                'name_ar': str(mineral_type),
                'name_en': str(mineral_type),
                'count': count,
            }
        )

    out: list[dict[str, Any]] = []
    for entry in grouped.values():
        total = entry['total'] or 1
        for row in entry['types']:
            row['percent'] = round(row['count'] * 1000 / total) / 10
        entry['types'].sort(key=lambda item: (-item['count'], item['name_ar']))
        out.append(entry)

    out.sort(key=lambda item: (-item['total'], item['name_en']))
    return out


def _era_mix() -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              COALESCE(NULLIF(TRIM(properties->>'era'), ''), '—') AS era,
              COUNT(*) AS n
            FROM gis_water_feature
            WHERE layer_id = 'geology-era'
            GROUP BY 1
            ORDER BY n DESC, era ASC
            """
        )
        rows = cursor.fetchall()
    total = sum(int(n) for _, n in rows) or 1
    out: list[dict[str, Any]] = []
    for era, n in rows:
        key = str(era)
        label_en, label_ar = ERA_LABELS.get(key, (key, key))
        out.append(
            {
                'era': key,
                'label_en': label_en,
                'label_ar': label_ar,
                'count': int(n),
                'percent': round(int(n) * 1000 / total) / 10,
            }
        )
    return out


def _parse_number(value: str) -> float | None:
    text = str(value or '').strip().replace(',', '.')
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _latest_national_metrics() -> dict[str, float]:
    infos = accepted_infos_for_geology_category()
    if not infos:
        return {}
    try:
        attrs = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(
                id__in={r.attribute_id for r in infos}
            )
        }
        titles = {
            t.id: t.code
            for t in ReportDynamicFormsTitle.objects.filter(
                id__in={a.title_id for a in attrs.values() if a.title_id}
            )
        }
    except DatabaseError:
        return {}

    national_ids = {
        aid for aid, a in attrs.items() if titles.get(a.title_id) == TITLE_NATIONAL
    }
    rows: dict[str, dict[str, str]] = defaultdict(dict)
    for info in infos:
        # Not "if national_ids and ..." — see water/info_dashboard.py's
        # _row_facts for why: empty national_ids must mean zero rows, not
        # "no filter, match everything".
        if info.attribute_id not in national_ids:
            continue
        attr = attrs.get(info.attribute_id)
        if not attr or not info.row_key:
            continue
        rk = str(info.row_key)
        if attr.key:
            rows[rk][attr.key] = str(info.value or '')
        if attr.type == 'date':
            rows[rk]['_date'] = str(info.value or '')

    dated: list[tuple[date, dict[str, float]]] = []
    for facts in rows.values():
        d = None
        raw = facts.get('_date', '')
        try:
            d = date.fromisoformat(str(raw).strip()[:10])
        except ValueError:
            d = None
        metrics = {
            k: n
            for k, v in facts.items()
            if not k.startswith('_') and (n := _parse_number(v)) is not None
        }
        if d and metrics:
            dated.append((d, metrics))
    if not dated:
        return {}
    dated.sort(key=lambda item: item[0], reverse=True)
    return dated[0][1]


def _mineral_type_distribution() -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              COALESCE(
                NULLIF(TRIM(properties->>'mineral_type_ar'), ''),
                NULLIF(TRIM(properties->>'name_ar'), ''),
                NULLIF(TRIM(properties->>'name'), ''),
                '—'
              ) AS mineral_type,
              COUNT(*) AS n
            FROM gis_water_feature
            WHERE layer_id = 'geology-minerals'
            GROUP BY 1
            ORDER BY n DESC, mineral_type ASC
            """
        )
        rows = cursor.fetchall()
    total = sum(int(n) for _, n in rows) or 1
    return [
        {
            'name_ar': str(name),
            'name_en': str(name),
            'count': int(n),
            'percent': round(int(n) * 1000 / total) / 10,
        }
        for name, n in rows
    ]


def build_geology_info_dashboard(
    *,
    layers: list[dict[str, Any]],
    plan_year: int | None = None,
) -> dict[str, Any]:
    metrics = _latest_national_metrics()
    total_features = sum(int(row.get('feature_count') or 0) for row in layers)
    # Catalog KPI from accepted Info only — no CSV fallback (use 0 when missing).
    catalog = metrics.get('geology_catalog_records')
    source = 'dynamic_forms' if metrics else 'gis'
    by_gov = _mineral_by_governorate()
    ore = build_ore_production_info_dashboard(plan_year=plan_year)
    return {
        'sector': 'mineral-resources',
        'source': source,
        'category_name': geology_category_name(),
        'kpis': [
            {
                'id': 'geology_layers',
                'label_en': 'Geology map layers',
                'label_ar': 'طبقات الخريطة الجيولوجية',
                'value': len(layers),
                'unit': '',
            },
            {
                'id': 'geology_features',
                'label_en': 'Mapped geological units',
                'label_ar': 'الوحدات الجيولوجية على الخريطة',
                'value': total_features,
                'unit': '',
            },
            {
                'id': 'geology_info',
                'label_en': 'Geology info catalog records',
                'label_ar': 'سجلات كتالوج المعلومات الجيولوجية',
                'value': int(catalog) if catalog is not None else 0,
                'unit': '',
            },
            {
                'id': 'geology_category_volcanic',
                'label_en': 'Volcanic catalog units',
                'label_ar': 'وحدات بركانية (كتالوج)',
                'value': int(metrics.get('geology_category_volcanic') or 0),
                'unit': '',
            },
            {
                'id': 'geology_category_sedimentary',
                'label_en': 'Sedimentary catalog units',
                'label_ar': 'وحدات رسوبية (كتالوج)',
                'value': int(metrics.get('geology_category_sedimentary') or 0),
                'unit': '',
            },
            {
                'id': 'geology_category_modern',
                'label_en': 'Modern catalog units',
                'label_ar': 'طبقات حديثة (كتالوج)',
                'value': int(metrics.get('geology_category_modern') or 0),
                'unit': '',
            },
        ],
        'layers': layers,
        'ore_production': ore,
        'mineral_types': _mineral_type_distribution(),
        'mineral_by_governorate': by_gov,
        'era_mix': _era_mix(),
        'summary': _dashboard_summary(layers, total_features, catalog, by_gov, ore),
        'notes': [
            {
                'en': 'Catalog KPIs from accepted Info; map layer geometry remains GIS.',
                'ar': 'مؤشرات الكتالوج من Info المعتمد؛ هندسة طبقات الخريطة تبقى من GIS.',
            }
        ],
    }


def _dashboard_summary(
    layers: list[dict[str, Any]],
    total_features: int,
    catalog: float | None,
    by_gov: list[dict[str, Any]],
    ore: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        'inventory_features': total_features,
        'info_catalog_records': int(catalog) if catalog is not None else 0,
        'map_layers': len(layers),
        'governorates_with_minerals': len(by_gov),
        'ore_products': ore['totals']['products'] if ore else 0,
        'ore_contracts': ore['totals']['contracts'] if ore else 0,
        'plan_year': ore['plan_year'] if ore else None,
        'available_plan_years': ore['available_plan_years'] if ore else [],
    }


@lru_cache(maxsize=8)
def _ore_production_attrs_by_name() -> dict[str, ReportDynamicFormsAttribute]:
    """Attributes of the ore-production title, keyed by `Attribute.key` only.

    Never keyed by `.label` — label is free-text Arabic display text editable
    from the report_moe UI at any time; `key` is the stable contract (see
    `check_info_contract`). Cached: form *schema*, not report data, and only
    changes via seed_ore_production_info_form. Call
    `_ore_production_attrs_by_name.cache_clear()` after reseeding in a
    long-lived process.
    """
    title = ReportDynamicFormsTitle.objects.filter(
        code=TITLE_ORE_PRODUCTION,
    ).first()
    if title is None:
        return {}
    by_name: dict[str, ReportDynamicFormsAttribute] = {}
    for attr in ReportDynamicFormsAttribute.objects.filter(title_id=title.id):
        if attr.key:
            by_name[attr.key] = attr
    return by_name


def _ore_production_rows_by_key() -> dict[str, dict[str, Any]]:
    by_name = _ore_production_attrs_by_name()
    if not by_name:
        return {}
    attrs_by_id = {attr.id: attr for attr in by_name.values()}
    infos = accepted_infos_for_geology_category()
    if not infos:
        return {}
    rows: dict[str, dict[str, Any]] = defaultdict(dict)
    for info in infos:
        attr = attrs_by_id.get(info.attribute_id)
        if attr is None or not info.row_key or not attr.key:
            continue
        rk = str(info.row_key)
        rows[rk][attr.key] = info.value or ''
        if info.entity_id is not None:
            rows[rk]['_entity_id'] = info.entity_id
    return rows


def _ore_row_number(facts: dict[str, Any], key: str) -> float | None:
    return _parse_number(facts.get(key, ''))


def _ore_row_int(facts: dict[str, Any], key: str) -> int | None:
    num = _ore_row_number(facts, key)
    return int(num) if num is not None else None


def _serialize_ore_row(product: Any, facts: dict[str, Any], product_id: int) -> dict[str, Any]:
    annual_plan = _ore_row_number(facts, 'annual_plan_tons')
    h1_plan = _ore_row_number(facts, 'h1_plan_tons')
    h1_executed = _ore_row_number(facts, 'h1_executed_tons')
    baseline = h1_plan if h1_plan else annual_plan
    execution_pct = (
        round(h1_executed * 100 / baseline, 2)
        if baseline and h1_executed is not None and baseline != 0
        else None
    )
    return {
        'product_id': product_id,
        'product_name_ar': product.name_ar if product else '—',
        'product_name_en': product.name_en if product else '',
        'production_type': product.production_type if product else '',
        'unit': product.unit if product else '',
        'annual_plan_tons': annual_plan,
        'h1_plan_tons': h1_plan,
        'h1_executed_tons': h1_executed,
        'execution_pct': execution_pct,
        'contract_count': _ore_row_int(facts, 'contract_count'),
        'reserve_text': facts.get('reserve_text') or '',
    }


def build_ore_production_info_dashboard(*, plan_year: int | None = None) -> dict[str, Any] | None:
    """Ore production & contracts, read-only from accepted report_moe Info.

    Returns None when the Info form hasn't been seeded yet or carries no rows —
    same "no coverage" contract as water/electricity's info_dashboard builders.
    """
    rows_by_key = _ore_production_rows_by_key()
    if not rows_by_key:
        return None

    from geology.models import OreProduct

    products = {p.id: p for p in OreProduct.objects.all()}

    parsed_rows: list[dict[str, Any]] = []
    available_years: set[int] = set()
    for facts in rows_by_key.values():
        year = _ore_row_int(facts, 'plan_year')
        product_id = facts.get('_entity_id')
        if year is None or product_id is None:
            continue
        available_years.add(year)
        parsed_rows.append({'year': year, 'product_id': int(product_id), 'facts': facts})

    if not available_years:
        return None

    selected_year = plan_year if plan_year in available_years else max(available_years)

    def rows_for_year(year: int) -> list[dict[str, Any]]:
        year_rows = [r for r in parsed_rows if r['year'] == year]
        result: list[dict[str, Any]] = []
        for row in year_rows:
            product = products.get(row['product_id'])
            result.append(_serialize_ore_row(product, row['facts'], row['product_id']))
        result.sort(key=lambda r: product_sort_order(products.get(r['product_id'])))
        return result

    result_rows = rows_for_year(selected_year)
    rows_by_year = {str(year): rows_for_year(year) for year in sorted(available_years)}

    totals = {
        'products': len({r['product_id'] for r in result_rows}),
        'lines': len(result_rows),
        'contracts': sum(r['contract_count'] or 0 for r in result_rows),
        'annual_plan': round(sum(r['annual_plan_tons'] or 0 for r in result_rows), 3),
        'h1_plan': round(sum(r['h1_plan_tons'] or 0 for r in result_rows), 3),
        'h1_executed': round(sum(r['h1_executed_tons'] or 0 for r in result_rows), 3),
    }

    return {
        'status': 'ready',
        'source': 'dynamic_forms',
        'category_name': geology_category_name(),
        'plan_year': selected_year,
        'rows': result_rows,
        'rows_by_year': rows_by_year,
        'totals': totals,
        'available_plan_years': sorted(available_years, reverse=True),
    }


def product_sort_order(product: Any) -> tuple[int, str]:
    if product is None:
        return (10_000, '')
    return (product.sort_order, product.name_ar)
