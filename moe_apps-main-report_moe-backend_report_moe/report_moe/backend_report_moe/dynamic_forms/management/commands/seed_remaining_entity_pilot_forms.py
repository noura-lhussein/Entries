"""
Seed Fact Titles + Attributes for remaining Master entity types.

Idempotent by title name.

Usage:
  python manage.py seed_remaining_entity_pilot_forms
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title

PILOTS = [
    {
        'title': 'تحديث احواض الهطول',
        'order': 903,
        'attributes': [
            ('الحوض', 'rainfall_basin', True),
            ('تاريخ التحديث', 'date', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث رصد الينابيع',
        'order': 904,
        'attributes': [
            ('النبع', 'spring', True),
            ('تاريخ الرصد', 'date', True),
            ('التدفق (م3/ث)', 'number', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث رصد البحيرات',
        'order': 905,
        'attributes': [
            ('البحيرة', 'lake', True),
            ('تاريخ الرصد', 'date', True),
            ('المنسوب (م)', 'number', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث رصد الانهار',
        'order': 906,
        'attributes': [
            ('النهر', 'river', True),
            ('تاريخ الرصد', 'date', True),
            ('التدفق (م3/ث)', 'number', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث رصد المجاري المائية',
        'order': 907,
        'attributes': [
            ('المجرى', 'stream', True),
            ('تاريخ الرصد', 'date', True),
            ('التدفق (م3/ث)', 'number', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث الوحدات الجيولوجية',
        'order': 908,
        'attributes': [
            ('الوحدة الجيولوجية', 'geology_unit', True),
            ('تاريخ التحديث', 'date', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث خطوط النقل الكهربائي',
        'order': 912,
        'attributes': [
            ('خط النقل', 'transmission_line', True),
            ('تاريخ التحديث', 'date', True),
            ('هل الخط عامل؟', 'boolean', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث محطات GIS 66 ك.ف',
        'order': 913,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_66', True),
            ('تاريخ التحديث', 'date', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث محطات GIS 230 ك.ف',
        'order': 914,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_230', True),
            ('تاريخ التحديث', 'date', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث محطات GIS 400 ك.ف',
        'order': 915,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_400', True),
            ('تاريخ التحديث', 'date', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث مواقع الطاقة المتجددة',
        'order': 916,
        'attributes': [
            ('الموقع', 'power_gis_renewable', True),
            ('تاريخ التحديث', 'date', True),
            ('القدرة (ميجاواط)', 'number', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث مستودعات الوقود',
        'order': 922,
        'attributes': [
            ('المستودع', 'storage_depot', True),
            ('تاريخ التحديث', 'date', True),
            ('المخزون (لتر)', 'number', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث انابيب النفط',
        'order': 923,
        'attributes': [
            ('الانبوب', 'pipeline', True),
            ('تاريخ التحديث', 'date', True),
            ('هل الانبوب عامل؟', 'boolean', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث الابار النفطية',
        'order': 924,
        'attributes': [
            ('البئر', 'oil_well', True),
            ('تاريخ الإنتاج', 'date', True),
            ('الإنتاج (برميل)', 'number', True),
            ('ملاحظات', 'textarea', False),
        ],
    },
    {
        'title': 'تحديث محطات الوقود',
        'order': 925,
        'attributes': [
            ('محطة الوقود', 'fuel_station', True),
            ('تاريخ التحديث', 'date', True),
            ('هل المحطة عاملة؟', 'boolean', False),
            ('ملاحظات', 'textarea', False),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed Fact titles for remaining Master entity types (GIS + ORM).'

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
