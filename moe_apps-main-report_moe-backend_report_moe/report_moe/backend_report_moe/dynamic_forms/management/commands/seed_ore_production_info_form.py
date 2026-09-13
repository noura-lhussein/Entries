"""
Ensure the "إنتاج الخامات والعقود" (Ore production & contracts) Info form exists
under TitleCategory «إدارة قطاع التعدين», with one row per ore product per plan year.

Usage:
  python manage.py seed_ore_production_info_form
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع التعدين'
TITLE_NAME = 'إنتاج الخامات والعقود'
TITLE_CODE = 'geology.ore_production'

# (label, key, type, required)
FIELDS = (
    ('المنتج', 'product', 'ore_product', True),
    ('سنة الخطة', 'plan_year', 'number', True),
    ('المخطط السنوي', 'annual_plan_tons', 'number', False),
    ('مخطط النصف الأول', 'h1_plan_tons', 'number', False),
    ('المنفذ (النصف الأول)', 'h1_executed_tons', 'number', False),
    ('عدد العقود', 'contract_count', 'number', False),
    ('الاحتياطي', 'reserve_text', 'text', False),
)


class Command(BaseCommand):
    help = 'Seed the ore production & contracts Info form (Title + Attributes).'

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
            name=TITLE_NAME,
            defaults={
                'order': 810, 'category': category, 'entry_mode': 'multi_record',
                'code': TITLE_CODE, 'is_system': True,
            },
        )
        changed = []
        if title.category_id != category.id:
            title.category = category
            changed.append('category')
        if title.entry_mode != 'multi_record':
            title.entry_mode = 'multi_record'
            changed.append('entry_mode')
        if title.code != TITLE_CODE:
            title.code = TITLE_CODE
            changed.append('code')
        if not title.is_system:
            title.is_system = True
            changed.append('is_system')
        if changed:
            title.save(update_fields=changed)
        self.stdout.write(
            f"  Title id={title.id} {'created' if created else 'linked'}: {TITLE_NAME} (code={TITLE_CODE})"
        )

        n = 0
        for order, (label, key, attr_type, required) in enumerate(FIELDS, start=1):
            attr, was = Attribute.objects.get_or_create(
                title=title,
                label=label,
                defaults={
                    'type': attr_type, 'required': required, 'key': key, 'order': order,
                    'is_system': True,
                },
            )
            if was:
                n += 1
            else:
                changed = []
                if attr.key != key:
                    attr.key = key
                    changed.append('key')
                if not attr.is_system:
                    attr.is_system = True
                    changed.append('is_system')
                if changed:
                    attr.save(update_fields=changed)
        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {n}.'))
