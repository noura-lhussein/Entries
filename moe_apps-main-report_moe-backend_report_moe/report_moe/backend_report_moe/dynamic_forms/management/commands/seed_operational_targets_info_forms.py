"""
Ensure operational-target Info titles under each sector TitleCategory.

Title pattern: «أهداف تشغيلية - <short ar name>»
Attribute.key = technical key; Attribute.label = Arabic.

Usage:
  python manage.py seed_operational_targets_info_forms
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import LABEL_AR_FALLBACK, apply_arabic_label_to_attribute
from dynamic_forms.models import Attribute, Title, TitleCategory

SECTORS: list[tuple[str, str, int, int]] = [
    # (category_name, short_ar, category_order, title_order)
    ('إدارة قطاع الكهرباء', 'الكهرباء', 10, 850),
    ('إدارة قطاع البترول', 'النفط والغاز', 20, 850),
    ('إدارة قطاع المياه', 'المياه', 30, 850),
    ('إدارة قطاع التعدين', 'التعدين', 40, 850),
]

# (key, type, required)
TARGET_ATTRIBUTES: list[tuple[str, str, bool]] = [
    ('metric_key', 'text', True),
    ('scope_type', 'text', True),
    ('scope_code', 'text', False),
    ('period_type', 'text', True),
    ('period_start', 'date', True),
    ('period_end', 'date', False),
    ('target_value', 'number', True),
    ('unit', 'text', False),
    ('label_ar', 'text', False),
    ('label_en', 'text', False),
    ('notes', 'textarea', False),
]


def title_name_for_short(short_ar: str) -> str:
    return f'أهداف تشغيلية - {short_ar}'


class Command(BaseCommand):
    help = 'Seed operational-target Info titles under each sector category.'

    @transaction.atomic
    def handle(self, *args, **options):
        total_attrs = 0
        for category_name, short_ar, cat_order, title_order in SECTORS:
            category, cat_created = TitleCategory.objects.get_or_create(
                name=category_name,
                defaults={'order': cat_order},
            )
            self.stdout.write(
                f"Category id={category.id} {'created' if cat_created else 'exists'}: {category_name}"
            )

            name = title_name_for_short(short_ar)
            title, title_created = Title.objects.get_or_create(
                name=name,
                defaults={'order': title_order, 'category': category},
            )
            if title.category_id != category.id or title.order != title_order:
                title.category = category
                title.order = title_order
                title.save(update_fields=['category', 'order'])
            self.stdout.write(
                f"  Title id={title.id} {'created' if title_created else 'linked'}: {title.name}"
            )

            for key, attr_type, required in TARGET_ATTRIBUTES:
                label_ar = LABEL_AR_FALLBACK.get(key, key)
                attr = (
                    Attribute.objects.filter(title=title, key=key).first()
                    or Attribute.objects.filter(title=title, label=key).first()
                    or Attribute.objects.filter(title=title, label=label_ar).first()
                )
                if attr:
                    apply_arabic_label_to_attribute(attr, save=True)
                    update_fields: list[str] = []
                    if attr.type != attr_type:
                        attr.type = attr_type
                        update_fields.append('type')
                    if attr.required != required:
                        attr.required = required
                        update_fields.append('required')
                    if update_fields:
                        attr.save(update_fields=update_fields)
                else:
                    Attribute.objects.create(
                        title=title,
                        label=label_ar,
                        type=attr_type,
                        required=required,
                        key=key,
                    )
                    total_attrs += 1

        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {total_attrs}.'))
