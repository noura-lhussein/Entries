"""
Backfill Title.field_groups + Attribute metadata for electricity daily titles.

Usage:
  python manage.py seed_electricity_entry_metadata
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import LABEL_AR_FALLBACK, UNIT_AR_FALLBACK
from dynamic_forms.models import Attribute, Title

NATIONAL = 'مؤشرات التقرير اليومي للكهرباء'

NATIONAL_GROUPS = [
    {'id': 'generation', 'title_ar': 'التوليد', 'order': 1, 'collapsed_by_default': False},
    {'id': 'fuel', 'title_ar': 'الوقود', 'order': 2, 'collapsed_by_default': False},
    {'id': 'gas', 'title_ar': 'الغاز', 'order': 3, 'collapsed_by_default': True},
    {'id': 'grid', 'title_ar': 'الشبكة', 'order': 4, 'collapsed_by_default': True},
    {'id': 'incidents', 'title_ar': 'الحوادث', 'order': 5, 'collapsed_by_default': True},
]

# key → group
NATIONAL_GROUP_BY_KEY: dict[str, str] = {
    'تاريخ التقرير': 'generation',
    'nominal_capacity_mwh': 'generation',
    'total_generation_mwh_24h': 'generation',
    'gas_generation_mwh_24h': 'generation',
    'steam_generation_mwh': 'generation',
    'available_generated_power': 'generation',
    'net_generation_mwh': 'generation',
    'peak_generation_mw': 'generation',
    'hydro_dams_capacity_mw': 'generation',
    'hydro_output_mw': 'generation',
    'solar_capacity_mw': 'generation',
    'wind_capacity_mw': 'generation',
    'self_use_losses_mw': 'generation',
    'industrial_self_use_mw': 'generation',
    'generation_without_industrial_mw': 'generation',
    'rotary_reserve_mw': 'generation',
    'gas_groups_mw': 'generation',
    'steam_groups_mw': 'generation',
    'gov_consumed_mw': 'generation',
    'gov_allocated_mw': 'generation',
    'gov_excess_mw': 'generation',
    'steam_fuel_demand_tpd': 'fuel',
    'total_fuel_demand_tpd': 'fuel',
    'fuel_oil_consumed_tpd': 'fuel',
    'fuel_oil_received_tpd': 'fuel',
    'fuel_flow_consumed_tpd': 'fuel',
    'fuel_oil_balance_tpd': 'fuel',
    'fuel_tank_max_capacity_tons': 'fuel',
    'fuel_reserve_tons': 'fuel',
    'fuel_tank_stock_tons': 'fuel',
    'fuel_reserve_pct': 'fuel',
    'available_fuel_quantity': 'fuel',
    'gas_demand_mm3d': 'gas',
    'gas_consumed_mm3d': 'gas',
    'gas_import_mm3d': 'gas',
    'grid_frequency_hz': 'grid',
    'generation_incidents_count': 'incidents',
    'grid_incidents_count': 'incidents',
}

DEFAULT_GROUPS = [
    {'id': 'main', 'title_ar': 'البيانات', 'order': 1, 'collapsed_by_default': False},
]


class Command(BaseCommand):
    help = 'Seed entry-form metadata (groups/units/order) for electricity titles.'

    @transaction.atomic
    def handle(self, *args, **options):
        updated_titles = 0
        updated_attrs = 0

        title = Title.objects.filter(name=NATIONAL, deleted=False).first()
        if title:
            title.subtitle = 'الشركة السورية للكهرباء'
            title.entry_mode = 'single_record'
            title.field_groups = NATIONAL_GROUPS
            title.preview_field_keys = [
                'تاريخ التقرير',
                'total_generation_mwh_24h',
                'peak_generation_mw',
            ]
            title.save(
                update_fields=[
                    'subtitle',
                    'entry_mode',
                    'field_groups',
                    'preview_field_keys',
                ]
            )
            updated_titles += 1
            for i, attr in enumerate(
                Attribute.objects.filter(title=title).order_by('id'), start=1
            ):
                raw = (attr.label or '').strip()
                key = raw if raw in LABEL_AR_FALLBACK or raw in NATIONAL_GROUP_BY_KEY else (
                    attr.key or ''
                )
                if raw in LABEL_AR_FALLBACK:
                    key = raw
                group = NATIONAL_GROUP_BY_KEY.get(key) or NATIONAL_GROUP_BY_KEY.get(raw) or 'generation'
                label_ar = LABEL_AR_FALLBACK.get(key) or LABEL_AR_FALLBACK.get(raw) or (
                    raw if raw == 'تاريخ التقرير' else raw
                )
                # Keep technical key in `key`; show Arabic in `label`.
                if key and key in LABEL_AR_FALLBACK:
                    attr.key = key
                    attr.label = label_ar
                elif raw == 'تاريخ التقرير':
                    attr.key = 'report_date'
                    attr.label = 'تاريخ التقرير'
                attr.group = group
                attr.order = i
                attr.unit_ar = UNIT_AR_FALLBACK.get(key) or UNIT_AR_FALLBACK.get(raw) or attr.unit_ar
                if attr.type == 'number' and attr.min_value is None:
                    attr.min_value = 0
                if key == 'fuel_oil_balance_tpd':
                    attr.max_field = 'fuel_tank_max_capacity_tons'
                    attr.warn_if_gt_field = 'fuel_tank_max_capacity_tons'
                    attr.message_ar = 'القيمة أعلى من سعة الخزان'
                attr.save()
                updated_attrs += 1

        # Other electricity titles under category: generic main group + order
        cat_titles = Title.objects.filter(
            deleted=False, category__name='إدارة قطاع الكهرباء'
        ).exclude(name=NATIONAL)
        for t in cat_titles:
            if not t.field_groups:
                t.field_groups = DEFAULT_GROUPS
                t.entry_mode = t.entry_mode or 'single_record'
                t.save(update_fields=['field_groups', 'entry_mode'])
                updated_titles += 1
            for i, attr in enumerate(
                Attribute.objects.filter(title=t).order_by('id'), start=1
            ):
                changed = False
                if not attr.group:
                    attr.group = 'main'
                    changed = True
                if not attr.order or attr.order == 1 and i > 1:
                    attr.order = i
                    changed = True
                # Strip units from labels into unit_ar when pattern «… (وحدة)»
                label = attr.label or ''
                if '(' in label and ')' in label and not attr.unit_ar:
                    left, _, rest = label.partition('(')
                    unit, _, _ = rest.partition(')')
                    if unit.strip() and left.strip():
                        attr.label = left.strip()
                        attr.unit_ar = unit.strip()
                        changed = True
                if changed:
                    attr.save()
                    updated_attrs += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. titles={updated_titles}, attributes={updated_attrs}'
            )
        )
