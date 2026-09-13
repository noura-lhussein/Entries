"""
Ensure TitleCategory «إدارة قطاع المياه», link entity pilot titles, national summary title.

Usage:
  python manage.py seed_water_entity_pilot_forms
  python manage.py seed_water_sector_info_forms
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع المياه'
CATEGORY_ORDER = 30
NATIONAL_TITLE = 'مؤشرات قطاع المياه'
NATIONAL_CODE = 'water.national'
# (name, order, code) — code is the stable identifier moeds' info_dashboard.py
# resolves by; name/order are free to edit from the report_moe UI.
LINKED_TITLES = (
    ('تحديث تخزين السدود', 901, 'water.dam_entity'),
    ('تحديث رصد الهطول', 902, 'water.rainfall_entity'),
    ('تحديث محطات مياه الشرب', 900, 'water.drinking_station_entity'),
    ('مؤشرات سلسلة الفرات', 810, 'water.euphrates'),
)

# (key, label_ar, label_en, unit_ar, unit_en, measure_order) — every one of these
# is a direct dashboard KPI (build_water_info_sector_payload), so is_measure=True.
NATIONAL_METRICS = (
    ('rainfall_stations_reporting', 'محطات الهطول المبلّغة', 'Rainfall stations reporting', '', '', 1),
    ('rainfall_total_mm', 'إجمالي الهطول', 'Total rainfall', 'مم', 'mm', 2),
    ('dams_with_readings', 'سدود بقراءات', 'Dams with readings', '', '', 3),
    ('dam_storage_avg_mcm', 'متوسط تخزين السدود', 'Average dam storage', 'مليون م³', 'M m³', 4),
    ('dam_storage_total_mcm', 'إجمالي تخزين السدود', 'Total dam storage', 'مليون م³', 'M m³', 5),
    ('drinking_stations_total', 'محطات مياه الشرب', 'Drinking water stations', '', '', 6),
    ('drinking_stations_operational', 'محطات عاملة', 'Operational stations', '', '', 7),
)


class Command(BaseCommand):
    help = 'Seed water sector TitleCategory and national summary Info title.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, cat_created = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': CATEGORY_ORDER},
        )
        self.stdout.write(
            f"Category id={category.id} {'created' if cat_created else 'exists'}: {CATEGORY_NAME}"
        )

        for name, order, code in LINKED_TITLES:
            title, created = Title.objects.get_or_create(
                name=name,
                defaults={'order': order, 'category': category, 'code': code, 'is_system': True},
            )
            changed = []
            if title.category_id != category.id:
                title.category = category
                changed.append('category')
            if title.order != order:
                title.order = order
                changed.append('order')
            if title.code != code:
                title.code = code
                changed.append('code')
            if not title.is_system:
                title.is_system = True
                changed.append('is_system')
            if changed:
                title.save(update_fields=changed)
            self.stdout.write(
                f"  Title id={title.id} {'created' if created else 'linked'}: {name} (code={code})"
            )

        national, n_created = Title.objects.get_or_create(
            name=NATIONAL_TITLE,
            defaults={'order': 800, 'category': category, 'code': NATIONAL_CODE, 'is_system': True},
        )
        changed = []
        if national.category_id != category.id:
            national.category = category
            changed.append('category')
        if national.order != 800:
            national.order = 800
            changed.append('order')
        if national.code != NATIONAL_CODE:
            national.code = NATIONAL_CODE
            changed.append('code')
        if not national.is_system:
            national.is_system = True
            changed.append('is_system')
        if changed:
            national.save(update_fields=changed)
        self.stdout.write(
            f"  Title id={national.id} {'created' if n_created else 'linked'}: {NATIONAL_TITLE} (code={NATIONAL_CODE})"
        )

        attr_created = 0
        date_attr, was = Attribute.objects.get_or_create(
            title=national,
            label='تاريخ التقرير',
            defaults={
                'type': 'date', 'required': True, 'key': 'report_date',
                'label_en': 'Report date', 'is_system': True,
            },
        )
        if was:
            attr_created += 1
        else:
            date_changed = []
            if date_attr.key != 'report_date':
                date_attr.key = 'report_date'
                date_changed.append('key')
            if not date_attr.is_system:
                date_attr.is_system = True
                date_changed.append('is_system')
            if date_changed:
                date_attr.save(update_fields=date_changed)

        for key, label_ar, label_en, unit_ar, unit_en, measure_order in NATIONAL_METRICS:
            attr = (
                Attribute.objects.filter(title=national, key=key).first()
                or Attribute.objects.filter(title=national, label=key).first()
                or Attribute.objects.filter(title=national, label=label_ar).first()
            )
            if attr:
                changed = []
                if attr.label != label_ar:
                    attr.label = label_ar
                    changed.append('label')
                if attr.key != key:
                    attr.key = key
                    changed.append('key')
                if attr.label_en != label_en:
                    attr.label_en = label_en
                    changed.append('label_en')
                if attr.unit_ar != unit_ar:
                    attr.unit_ar = unit_ar
                    changed.append('unit_ar')
                if attr.unit_en != unit_en:
                    attr.unit_en = unit_en
                    changed.append('unit_en')
                if attr.measure_order != measure_order:
                    attr.measure_order = measure_order
                    changed.append('measure_order')
                if not attr.is_measure:
                    attr.is_measure = True
                    changed.append('is_measure')
                if not attr.is_system:
                    attr.is_system = True
                    changed.append('is_system')
                if changed:
                    attr.save(update_fields=changed)
            else:
                Attribute.objects.create(
                    title=national,
                    label=label_ar,
                    type='number',
                    required=False,
                    key=key,
                    label_en=label_en,
                    unit_ar=unit_ar,
                    unit_en=unit_en,
                    measure_order=measure_order,
                    is_measure=True,
                    is_system=True,
                )
                attr_created += 1

        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {attr_created}.'))
