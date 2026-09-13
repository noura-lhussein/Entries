"""Build metadata-driven entry form schema (section + groups + fields)."""

from __future__ import annotations

import re
from typing import Any

from .models import Attribute, Title

_SNAKE = re.compile(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$')
# Pure ASCII technical token (metric keys and legacy English labels).
_TECH = re.compile(r'^[a-z][a-z0-9_]*$')

# Fallback Arabic labels when Attribute.label is still a technical key.
LABEL_AR_FALLBACK: dict[str, str] = {
    # Common
    'report_date': 'تاريخ التقرير',
    'report_label': 'تسمية التقرير',
    # Electricity national KPIs
    'nominal_capacity_mwh': 'القدرة الاسمية',
    'total_generation_mwh_24h': 'إجمالي التوليد 24س',
    'gas_generation_mwh_24h': 'توليد الغاز 24س',
    'steam_generation_mwh': 'التوليد البخاري',
    'steam_fuel_demand_tpd': 'طلب فيول بخاري',
    'gas_demand_mm3d': 'طلب الغاز',
    'total_fuel_demand_tpd': 'إجمالي طلب الفيول',
    'gas_consumed_mm3d': 'استهلاك الغاز',
    'fuel_oil_consumed_tpd': 'استهلاك الفيول',
    'hydro_dams_capacity_mw': 'قدرة السدود',
    'solar_capacity_mw': 'قدرة شمسية',
    'wind_capacity_mw': 'قدرة رياح',
    'fuel_oil_received_tpd': 'فيول وارد',
    'fuel_flow_consumed_tpd': 'تدفق فيول مستهلك',
    'fuel_oil_balance_tpd': 'رصيد الفيول',
    'fuel_tank_max_capacity_tons': 'سعة خزانات مجمّعة',
    'fuel_reserve_tons': 'احتياطي الوقود',
    'fuel_tank_stock_tons': 'مخزون الخزانات المجمّع',
    'fuel_reserve_pct': 'نسبة الاحتياطي',
    'grid_frequency_hz': 'تردد الشبكة',
    'available_generated_power': 'القدرة المولّدة المتاحة',
    'self_use_losses_mw': 'استهلاك ذاتي وخسائر',
    'net_generation_mwh': 'صافي التوليد',
    'industrial_self_use_mw': 'استهلاك صناعي ذاتي',
    'generation_without_industrial_mw': 'توليد بلا صناعي',
    'hydro_output_mw': 'خرج مائي',
    'rotary_reserve_mw': 'احتياطي دوّار',
    'gov_consumed_mw': 'استهلاك محافظات',
    'gov_allocated_mw': 'مخصّص محافظات',
    'gov_excess_mw': 'فائض محافظات',
    'gas_groups_mw': 'مجموعات غاز',
    'steam_groups_mw': 'مجموعات بخار',
    'gas_import_mm3d': 'استيراد غاز',
    'peak_generation_mw': 'ذروة التوليد',
    'available_fuel_quantity': 'كمية وقود متاحة',
    'generation_incidents_count': 'عدد حوادث التوليد',
    'grid_incidents_count': 'عدد حوادث الشبكة',
    # Oil & gas national KPIs
    'total_oil_production_bbl': 'إجمالي إنتاج النفط',
    'total_crude_transferred_bbl': 'إجمالي النفط الخام المرحل',
    'local_clean_gas_mm3': 'الإنتاج المحلي من الغاز النظيف',
    'clean_gas_import_azerbaijan_mm3': 'الغاز النظيف المستورد من أذربيجان',
    'clean_gas_import_jordan_mm3': 'الغاز النظيف المستورد من الأردن',
    'total_clean_gas_mm3': 'إجمالي الغاز النظيف (الإنتاج المحلي + المستورد)',
    'clean_gas_distributed_mm3': 'مجموع كميات الغاز النظيف الموزعة للمستهلكين',
    'electricity_clean_gas_consumption_mm3': 'استهلاك قطاع الكهرباء من الغاز النظيف',
    'mazut_sold_thu_fri_m3': 'كميات المازوت المباعة ليومي الخميس والجمعة',
    'gasoline_90_95_sold_thu_fri_m3': 'كميات البنزين (90+95) المباعة ليومي الخميس والجمعة',
    'domestic_lpg_sold_m3': 'كميات الغاز المسال (المنزلي LPG) المباعة',
    'fuel_oil_sold_m3': 'كميات الفيول المباعة',
    'brent_crude_price_usd_bbl': 'سعر النفط كخام برنت',
    'gas_price_usd_mmbtu': 'سعر الغاز (مليون وحدة حرارية بريطانية)',
    # Water sector national KPIs
    'rainfall_stations_reporting': 'محطات الهطول المبلّغة',
    'rainfall_total_mm': 'إجمالي الهطول',
    'dams_with_readings': 'سدود بقراءات',
    'dam_storage_avg_mcm': 'متوسط تخزين السدود',
    'dam_storage_total_mcm': 'إجمالي تخزين السدود',
    'drinking_stations_total': 'محطات مياه الشرب',
    'drinking_stations_operational': 'محطات عاملة',
    # Euphrates cascade
    'inflow_jarabulus': 'وارد جرابلس',
    'tishreen_level_m': 'منسوب تشرين',
    'tishreen_storage_mcm': 'تخزين تشرين',
    'tishreen_outflow': 'تصريف تشرين',
    'tishreen_generation_mwh': 'توليد تشرين',
    'furat_level_m': 'منسوب الفرات',
    'furat_storage_mcm': 'تخزين الفرات',
    'furat_outflow': 'تصريف الفرات',
    'furat_generation_mwh': 'توليد الفرات',
    'kadiran_outflow': 'تصريف خديان',
    'kadiran_generation_mwh': 'توليد خديان',
    'al_jalab_discharge': 'تصريف الجلاب',
    'total_generation_mwh': 'إجمالي التوليد',
    # Geology national KPIs
    'geology_catalog_records': 'سجلات كتالوج المعلومات الجيولوجية',
    'geology_category_volcanic': 'وحدات بركانية (كتالوج)',
    'geology_category_sedimentary': 'وحدات رسوبية (كتالوج)',
    'geology_category_modern': 'طبقات حديثة (كتالوج)',
    # Operational alerts
    'severity': 'مستوى الخطورة',
    'message_ar': 'الرسالة (عربي)',
    'message_en': 'الرسالة (إنجليزي)',
    'start_date': 'تاريخ البدء',
    'status': 'الحالة',
    # Operational targets
    'metric_key': 'مفتاح المؤشر',
    'scope_type': 'نوع النطاق',
    'scope_code': 'رمز النطاق',
    'period_type': 'نوع الفترة',
    'period_start': 'بداية الفترة',
    'period_end': 'نهاية الفترة',
    'target_value': 'القيمة المستهدفة',
    'unit': 'الوحدة',
    'label_ar': 'التسمية العربية',
    'label_en': 'التسمية الإنجليزية',
    'notes': 'ملاحظات',
}

UNIT_AR_FALLBACK: dict[str, str] = {
    'nominal_capacity_mwh': 'م.و.س',
    'total_generation_mwh_24h': 'م.و.س',
    'gas_generation_mwh_24h': 'م.و.س',
    'steam_generation_mwh': 'م.و.س',
    'steam_fuel_demand_tpd': 'طن',
    'gas_demand_mm3d': 'م.ق.ي',
    'total_fuel_demand_tpd': 'طن',
    'gas_consumed_mm3d': 'م.ق.ي',
    'fuel_oil_consumed_tpd': 'طن',
    'hydro_dams_capacity_mw': 'م.و',
    'solar_capacity_mw': 'م.و',
    'wind_capacity_mw': 'م.و',
    'fuel_oil_received_tpd': 'طن',
    'fuel_flow_consumed_tpd': 'طن',
    'fuel_oil_balance_tpd': 'طن',
    'fuel_tank_max_capacity_tons': 'طن',
    'fuel_reserve_tons': 'طن',
    'fuel_tank_stock_tons': 'طن',
    'fuel_reserve_pct': '%',
    'grid_frequency_hz': 'هرتز',
    'available_generated_power': 'م.و',
    'self_use_losses_mw': 'م.و',
    'net_generation_mwh': 'م.و.س',
    'industrial_self_use_mw': 'م.و',
    'generation_without_industrial_mw': 'م.و',
    'hydro_output_mw': 'م.و',
    'rotary_reserve_mw': 'م.و',
    'gov_consumed_mw': 'م.و',
    'gov_allocated_mw': 'م.و',
    'gov_excess_mw': 'م.و',
    'gas_groups_mw': 'م.و',
    'steam_groups_mw': 'م.و',
    'gas_import_mm3d': 'م.ق.ي',
    'peak_generation_mw': 'م.و',
    'inflow_jarabulus': 'م³/ث',
    'tishreen_outflow': 'م³/ث',
    'furat_outflow': 'م³/ث',
    'kadiran_outflow': 'م³/ث',
    'al_jalab_discharge': 'م³/ث',
    'tishreen_level_m': 'م',
    'furat_level_m': 'م',
    'tishreen_storage_mcm': 'مليون م³',
    'furat_storage_mcm': 'مليون م³',
    'tishreen_generation_mwh': 'م.و.س',
    'furat_generation_mwh': 'م.و.س',
    'kadiran_generation_mwh': 'م.و.س',
    'total_generation_mwh': 'م.و.س',
    'rainfall_total_mm': 'مم',
    'dam_storage_avg_mcm': 'مليون م³',
    'dam_storage_total_mcm': 'مليون م³',
}


def attribute_display_label(attr: Attribute) -> str:
    """Arabic label for UI / Excel; never expose technical English keys."""
    label = (attr.label or '').strip()
    key = (attr.key or '').strip()

    for candidate in (key, label):
        if candidate and candidate in LABEL_AR_FALLBACK:
            return LABEL_AR_FALLBACK[candidate]

    # Already a human/Arabic label (not a pure technical token).
    if label and not _TECH.fullmatch(label):
        return label

    if label and _SNAKE.match(label):
        return label.replace('_', ' ')
    return label or f'حقل {attr.pk}'


def apply_arabic_label_to_attribute(attr: Attribute, *, save: bool = True) -> bool:
    """
    Persist Arabic display label on Attribute; keep technical key in `key`.
    Returns True when the row was updated.
    """
    label = (attr.label or '').strip()
    key = (attr.key or '').strip()
    tech = key or (
        label if label in LABEL_AR_FALLBACK or _TECH.fullmatch(label) else '')
    arabic = (
        LABEL_AR_FALLBACK.get(tech)
        or LABEL_AR_FALLBACK.get(label)
        or ''
    )
    if not arabic:
        return False

    changed_fields: list[str] = []
    if not key and tech:
        attr.key = tech
        changed_fields.append('key')
    if attr.label != arabic:
        attr.label = arabic
        changed_fields.append('label')
    if not changed_fields:
        return False
    if save:
        attr.save(update_fields=changed_fields)
    return True


# Back-compat alias
_display_label = attribute_display_label

GROUP_TITLE_AR: dict[str, str] = {
    'other': 'أخرى',
    'main': 'البيانات',
    'generation': 'التوليد',
    'fuel': 'الوقود',
    'gas': 'الغاز',
    'grid': 'الشبكة',
    'incidents': 'الحوادث',
    'oil_production': 'إنتاج النفط',
    'clean_gas': 'الغاز النظيف',
    'fuel_sales': 'مبيعات المشتقات',
    'prices': 'الأسعار',
}


def group_title_ar(group_id: str) -> str:
    gid = (group_id or '').strip() or 'other'
    return GROUP_TITLE_AR.get(gid, gid)


def _unit_ar(attr: Attribute) -> str | None:
    if attr.unit_ar:
        return attr.unit_ar
    key = (attr.key or '').strip()
    if key and key in UNIT_AR_FALLBACK:
        return UNIT_AR_FALLBACK[key]
    label = (attr.label or '').strip()
    if label in UNIT_AR_FALLBACK:
        return UNIT_AR_FALLBACK[label]
    if label:
        for tech_key, ar_label in LABEL_AR_FALLBACK.items():
            if ar_label == label and tech_key in UNIT_AR_FALLBACK:
                return UNIT_AR_FALLBACK[tech_key]
    return None


def _dec(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_title_form_schema(title: Title) -> dict[str, Any]:
    attrs = list(
        Attribute.objects.filter(title=title).prefetch_related('options').order_by(
            'order', 'id'
        )
    )
    groups_meta = list(title.field_groups or [])
    if not groups_meta:
        # Derive groups from attribute.group values
        seen: dict[str, int] = {}
        for a in attrs:
            gid = (a.group or '').strip() or 'other'
            if gid not in seen:
                seen[gid] = len(seen) + 1
        groups_meta = [
            {
                'id': gid,
                'title_ar': group_title_ar(gid),
                'order': order,
                'collapsed_by_default': gid not in {'generation', 'fuel'} and gid != list(seen)[0],
            }
            for gid, order in seen.items()
        ]
    groups_meta = sorted(groups_meta, key=lambda g: (
        g.get('order') or 0, g.get('id') or ''))
    for g in groups_meta:
        if not (g.get('title_ar') or '').strip() or _TECH.fullmatch(str(g.get('title_ar') or '')):
            g['title_ar'] = group_title_ar(str(g.get('id') or 'other'))

    fields: list[dict[str, Any]] = []
    for a in attrs:
        key = a.stable_key
        field: dict[str, Any] = {
            'id': a.id,
            'key': key,
            'label_ar': attribute_display_label(a),
            'type': a.type,
            'group': (a.group or '').strip() or 'other',
            'order': a.order or a.id,
            'required': bool(a.required),
            'unit_ar': _unit_ar(a),
            'readonly': bool(a.readonly) or bool(a.computed_from),
            'help_ar': a.help_ar or None,
            'computed_from': a.computed_from or None,
            'min': _dec(a.min_value),
            'max': _dec(a.max_value),
            'max_field': a.max_field or None,
            'warn_if_gt_field': a.warn_if_gt_field or None,
            'message_ar': a.message_ar or None,
            'decimals': a.decimals,
            'options': [
                {'id': o.id, 'label': o.label} for o in a.options.all()
            ]
            if a.type == 'select'
            else [],
        }
        fields.append(field)

    preview = list(title.preview_field_keys or [])
    if not preview:
        # Prefer date + first two number fields
        date_keys = [f['key'] for f in fields if f['type'] == 'date'][:1]
        num_keys = [f['key'] for f in fields if f['type'] == 'number'][:2]
        preview = date_keys + num_keys

    return {
        'section': {
            'id': title.id,
            'order': title.order,
            'title_ar': title.name,
            'subtitle_ar': title.subtitle or None,
            'mode': title.entry_mode or 'single_record',
            'groups': groups_meta,
            'preview_field_keys': preview,
        },
        'fields': fields,
    }
