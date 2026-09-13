"""
Seed Title «مؤشرات سلسلة الفرات» under water TitleCategory.

Usage:
  python manage.py seed_euphrates_cascade_info_forms
  python manage.py seed_water_sector_info_forms  # links category
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import (
    LABEL_AR_FALLBACK,
    UNIT_AR_FALLBACK,
    apply_arabic_label_to_attribute,
)
from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع المياه'
TITLE_NAME = 'مؤشرات سلسلة الفرات'
TITLE_CODE = 'water.euphrates'
METRIC_KEYS = (
    'inflow_jarabulus',
    'tishreen_level_m',
    'tishreen_storage_mcm',
    'tishreen_outflow',
    'tishreen_generation_mwh',
    'furat_level_m',
    'furat_storage_mcm',
    'furat_outflow',
    'furat_generation_mwh',
    'kadiran_outflow',
    'kadiran_generation_mwh',
    'al_jalab_discharge',
    'total_generation_mwh',
)


def _unit_for_key(key: str) -> str:
    return UNIT_AR_FALLBACK.get(key, '')


def _upsert(title: Title, *, key: str, attr_type: str, required: bool) -> bool:
    label_ar = LABEL_AR_FALLBACK.get(key, key)
    unit_ar = _unit_for_key(key)
    attr = (
        Attribute.objects.filter(title=title, key=key).first()
        or Attribute.objects.filter(title=title, label=key).first()
        or Attribute.objects.filter(title=title, label=label_ar).first()
    )
    if attr:
        apply_arabic_label_to_attribute(attr, save=True)
        changed = []
        if attr.type != attr_type:
            attr.type = attr_type
            changed.append('type')
        if attr.required != required:
            attr.required = required
            changed.append('required')
        if not attr.is_system:
            attr.is_system = True
            changed.append('is_system')
        is_measure = attr_type == 'number'
        if attr.is_measure != is_measure:
            attr.is_measure = is_measure
            changed.append('is_measure')
        # Only seed unit when empty — admins set units from field setup UI.
        if unit_ar and not (attr.unit_ar or '').strip():
            attr.unit_ar = unit_ar
            changed.append('unit_ar')
        if changed:
            attr.save(update_fields=changed)
        return False
    Attribute.objects.create(
        title=title,
        label=label_ar,
        type=attr_type,
        required=required,
        key=key,
        unit_ar=unit_ar,
        is_system=True,
        is_measure=(attr_type == 'number'),
    )
    return True


class Command(BaseCommand):
    help = 'Seed Euphrates cascade national Info title and metric attributes.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': 30},
        )
        title, created = Title.objects.get_or_create(
            name=TITLE_NAME,
            defaults={'order': 810, 'category': category,
                      'code': TITLE_CODE, 'is_system': True},
        )
        changed = []
        if title.category_id != category.id:
            title.category = category
            changed.append('category')
        if title.order != 810:
            title.order = 810
            changed.append('order')
        if title.code != TITLE_CODE:
            title.code = TITLE_CODE
            changed.append('code')
        if not title.is_system:
            title.is_system = True
            changed.append('is_system')
        if changed:
            title.save(update_fields=changed)
        self.stdout.write(
            f"Title id={title.id} {'created' if created else 'exists'}: {TITLE_NAME} (code={TITLE_CODE})"
        )

        n = 0
        if _upsert(title, key='report_date', attr_type='date', required=True):
            n += 1
        if _upsert(title, key='report_label', attr_type='text', required=False):
            n += 1
        for key in METRIC_KEYS:
            if _upsert(title, key=key, attr_type='number', required=False):
                n += 1
        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {n}.'))
