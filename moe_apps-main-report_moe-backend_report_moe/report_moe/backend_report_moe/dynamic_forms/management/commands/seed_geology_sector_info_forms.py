"""
Ensure TitleCategory «إدارة قطاع التعدين» and national geology KPI Info title.

Usage:
  python manage.py seed_geology_sector_info_forms
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import LABEL_AR_FALLBACK, apply_arabic_label_to_attribute
from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع التعدين'
NATIONAL_TITLE = 'مؤشرات قطاع الجيولوجيا'
NATIONAL_CODE = 'geology.national'
METRICS = (
    'geology_catalog_records',
    'geology_category_volcanic',
    'geology_category_sedimentary',
    'geology_category_modern',
)


def _upsert(title: Title, *, key: str, attr_type: str, required: bool) -> bool:
    label_ar = LABEL_AR_FALLBACK.get(key, key)
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
        if changed:
            attr.save(update_fields=changed)
        return False
    Attribute.objects.create(
        title=title,
        label=label_ar,
        type=attr_type,
        required=required,
        key=key,
        is_system=True,
        is_measure=(attr_type == 'number'),
    )
    return True


class Command(BaseCommand):
    help = 'Seed geology sector TitleCategory and national KPI Info title.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, cat_created = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': 40},
        )
        self.stdout.write(
            f"Category id={category.id} {'created' if cat_created else 'exists'}: {CATEGORY_NAME}"
        )
        title, created = Title.objects.get_or_create(
            name=NATIONAL_TITLE,
            defaults={'order': 800, 'category': category, 'code': NATIONAL_CODE, 'is_system': True},
        )
        changed = []
        if title.category_id != category.id:
            title.category = category
            changed.append('category')
        if title.order != 800:
            title.order = 800
            changed.append('order')
        if title.code != NATIONAL_CODE:
            title.code = NATIONAL_CODE
            changed.append('code')
        if not title.is_system:
            title.is_system = True
            changed.append('is_system')
        if changed:
            title.save(update_fields=changed)
        self.stdout.write(
            f"  Title id={title.id} {'created' if created else 'linked'}: {NATIONAL_TITLE} (code={NATIONAL_CODE})"
        )
        n = 0
        if _upsert(title, key='report_date', attr_type='date', required=True):
            n += 1
        for key in METRICS:
            if _upsert(title, key=key, attr_type='number', required=False):
                n += 1
        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {n}.'))
