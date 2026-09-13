"""
Seed pilot Titles + Attributes for electricity and oil/gas entity updates.

Usage:
  python manage.py seed_energy_entity_pilot_forms
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title

PILOTS = [
    {
        'title': 'تحديث توليد محطات الكهرباء',
        'order': 910,
        'attributes': [
            ('محطة التوليد', 'power_plant', True),
            ('تاريخ التقرير', 'date', True),
            ('التوليد (ميجاواط ساعة)', 'number', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث حالة محطات التحويل',
        'order': 911,
        'attributes': [
            ('محطة التحويل', 'substation', True),
            ('تاريخ التحديث', 'date', True),
            ('هل المحطة عاملة؟', 'boolean', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث إنتاج الحقول النفطية',
        'order': 920,
        'attributes': [
            ('الحقل', 'oil_field', True),
            ('تاريخ الإنتاج', 'date', True),
            ('الإنتاج (برميل)', 'number', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث إنتاج المصافي',
        'order': 921,
        'attributes': [
            ('المصفاة', 'oil_refinery', True),
            ('تاريخ الإنتاج', 'date', True),
            ('الإنتاج (طن)', 'number', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed pilot Form Builder titles for electricity and oil/gas updates.'

    @transaction.atomic
    def handle(self, *args, **options):
        total_new = 0
        for pilot in PILOTS:
            title, created = Title.objects.get_or_create(
                name=pilot['title'],
                defaults={'order': pilot['order']},
            )
            self.stdout.write(
                f"Title id={title.id} {'created' if created else 'exists'}"
            )
            for label, attr_type, required in pilot['attributes']:
                _, was_created = Attribute.objects.get_or_create(
                    title=title,
                    label=label,
                    defaults={'type': attr_type, 'required': required},
                )
                if was_created:
                    total_new += 1
                    self.stdout.write(f"  + attribute type={attr_type}")
                else:
                    self.stdout.write(f"  = attribute exists type={attr_type}")

        self.stdout.write(self.style.SUCCESS(
            f'Done. New attributes: {total_new}. '
            'Assign each title + a leaf sub-section to a user to enter data.'
        ))
