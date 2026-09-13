"""
Ensure TitleCategory «إدارة قطاع الكهرباء» and daily-report Info titles/attributes.

Usage:
  python manage.py seed_electricity_daily_info_forms
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import LABEL_AR_FALLBACK
from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع الكهرباء'

NATIONAL_METRIC_LABELS: list[tuple[str, str]] = [
    ('nominal_capacity_mwh', 'القدرة الاسمية (MWh)'),
    ('total_generation_mwh_24h', 'إجمالي التوليد 24س (MWh)'),
    ('gas_generation_mwh_24h', 'توليد الغاز 24س (MWh)'),
    ('steam_generation_mwh', 'التوليد البخاري (MWh)'),
    ('steam_fuel_demand_tpd', 'طلب فيول بخاري (طن/يوم)'),
    ('gas_demand_mm3d', 'طلب الغاز (مليون م3/يوم)'),
    ('total_fuel_demand_tpd', 'إجمالي طلب الفيول (طن/يوم)'),
    ('gas_consumed_mm3d', 'استهلاك الغاز (مليون م3/يوم)'),
    ('fuel_oil_consumed_tpd', 'استهلاك الفيول (طن/يوم)'),
    ('hydro_dams_capacity_mw', 'قدرة السدود (MW)'),
    ('solar_capacity_mw', 'قدرة شمسية (MW)'),
    ('wind_capacity_mw', 'قدرة رياح (MW)'),
    ('fuel_oil_received_tpd', 'فيول وارد (طن/يوم)'),
    ('fuel_flow_consumed_tpd', 'تدفق فيول مستهلك (طن/يوم)'),
    ('fuel_oil_balance_tpd', 'رصيد الفيول (طن/يوم)'),
    ('fuel_tank_max_capacity_tons', 'سعة خزانات مجمّعة (طن)'),
    ('fuel_reserve_tons', 'احتياطي الوقود (طن)'),
    ('fuel_tank_stock_tons', 'مخزون الخزانات المجمّع (طن)'),
    ('fuel_reserve_pct', 'نسبة الاحتياطي (%)'),
    ('grid_frequency_hz', 'تردد الشبكة (Hz)'),
    ('available_generated_power', 'القدرة المولّدة المتاحة (MW)'),
    ('self_use_losses_mw', 'استهلاك ذاتي وخسائر (MW)'),
    ('net_generation_mwh', 'صافي التوليد (MWh)'),
    ('industrial_self_use_mw', 'استهلاك صناعي ذاتي (MW)'),
    ('generation_without_industrial_mw', 'توليد بلا صناعي (MW)'),
    ('hydro_output_mw', 'خرج مائي (MW)'),
    ('rotary_reserve_mw', 'احتياطي دوّار (MW)'),
    ('gov_consumed_mw', 'استهلاك محافظات (MW)'),
    ('gov_allocated_mw', 'مخصّص محافظات (MW)'),
    ('gov_excess_mw', 'فائض محافظات (MW)'),
    ('gas_groups_mw', 'مجموعات غاز (MW)'),
    ('steam_groups_mw', 'مجموعات بخار (MW)'),
    ('gas_import_mm3d', 'استيراد غاز (مليون م3/يوم)'),
    ('peak_generation_mw', 'ذروة التوليد (MW)'),
    ('available_fuel_quantity', 'كمية وقود متاحة'),
    ('generation_incidents_count', 'عدد حوادث التوليد'),
    ('grid_incidents_count', 'عدد حوادث الشبكة'),
]

# title_name, order, code, attributes: (label_ar, type, required[, key])
# `key` is the stable identifier moeds' electricity/info_dashboard.py resolves
# facts by — every non-entity-picker attribute below must carry one, or a
# label edit from the report_moe UI silently zeroes a KPI in moeds.
TITLE_SPECS: list[dict] = [
    {
        'title': 'مؤشرات التقرير اليومي للكهرباء',
        'code': 'electricity.national',
        'order': 800,
        # key = metric_key for migrate/dashboard; label = Arabic for UI/Excel.
        'attributes': [
            ('تاريخ التقرير', 'date', True, 'report_date'),
            *[
                (label_ar, 'number', False, key)
                for key, label_ar in NATIONAL_METRIC_LABELS
            ],
        ],
    },
    {
        'title': 'تحديث توليد محطات الكهرباء',
        'code': 'electricity.plant_entity',
        'order': 910,
        'attributes': [
            ('محطة التوليد', 'power_plant', True, 'plant'),
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('التوليد (ميجاواط ساعة)', 'number', True, 'generation_mwh'),
            ('المتاح (ميجاواط)', 'number', False, 'available_mw'),
            ('رمز الوحدة', 'text', False, 'unit_code'),
            ('الحالة', 'text', False, 'status'),
            ('القدرة الاسمية (ميجاواط)', 'number', False, 'nominal_mw'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        # Rows from this title are merged with plant_entity's into one combined
        # list in moeds (electricity/info_dashboard.py's `unit_source`) — field
        # keys below must match plant_entity's exactly for that merge to work.
        'title': 'تحديث توليد وحدات المحطات',
        'code': 'electricity.unit_entity',
        'order': 911,
        'attributes': [
            ('محطة التوليد', 'power_plant', True, 'plant'),
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('رمز الوحدة', 'text', False, 'unit_code'),
            ('القدرة الاسمية (ميجاواط)', 'number', False, 'nominal_mw'),
            ('المتاح (ميجاواط)', 'number', False, 'available_mw'),
            ('التوليد 24س (ميجاواط ساعة)', 'number', False, 'generation_mwh'),
            ('الحالة', 'text', False, 'status'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث حالة محطات التحويل',
        'code': 'electricity.substation_entity',
        'order': 912,
        'attributes': [
            ('محطة التحويل', 'substation', True, 'substation'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('هل المحطة عاملة؟', 'boolean', False, 'is_operational'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث خطوط النقل الكهربائي',
        'code': 'electricity.transmission_line_entity',
        'order': 913,
        'attributes': [
            ('خط النقل', 'transmission_line', True, 'line'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('هل الخط عامل؟', 'boolean', False, 'is_operational'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث محطات GIS 66 ك.ف',
        'code': 'electricity.gis_substation_66_entity',
        'order': 914,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_66', True, 'substation'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث محطات GIS 230 ك.ف',
        'code': 'electricity.gis_substation_230_entity',
        'order': 915,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_230', True, 'substation'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث محطات GIS 400 ك.ف',
        'code': 'electricity.gis_substation_400_entity',
        'order': 916,
        'attributes': [
            ('محطة التحويل', 'power_gis_substation_400', True, 'substation'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث مواقع الطاقة المتجددة',
        'code': 'electricity.renewable_site_entity',
        'order': 917,
        'attributes': [
            ('الموقع', 'power_gis_renewable', True, 'site'),
            ('تاريخ التحديث', 'date', True, 'update_date'),
            ('القدرة (ميجاواط)', 'number', False, 'capacity_mw'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث خزانات الوقود',
        'code': 'electricity.fuel_tank_entity',
        'order': 920,
        'attributes': [
            ('محطة الخزان', 'fuel_tank_station', True, 'station'),
            ('تاريخ القراءة', 'date', True, 'reading_date'),
            ('المخزون الحالي (طن)', 'number', True, 'current_stock_tons'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث أحمال المحافظات',
        'code': 'electricity.governorate_load_entity',
        'order': 921,
        'attributes': [
            ('المحافظة', 'load_governorate', True, 'governorate'),
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('المستهلك (ميجاواط)', 'number', True, 'consumed_mw'),
            ('المخصّص (ميجاواط)', 'number', False, 'allocated_mw'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تحديث قراءات السدود',
        'code': 'electricity.hydro_dam_entity',
        'order': 922,
        'attributes': [
            ('السد', 'hydro_dam', True, 'dam'),
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('المنسوب الأمامي (م)', 'number', False, 'front_level_m'),
            ('المنسوب الخلفي (م)', 'number', False, 'back_level_m'),
            ('التوليد (ميجاواط ساعة)', 'number', False, 'generation_mwh'),
            ('التصريف (م3/ث)', 'number', False, 'outflow_m3s'),
            ('الوارد (م3/ث)', 'number', False, 'inflow_m3s'),
            ('المتوقع (م3/ث)', 'number', False, 'expected_m3s'),
            ('ملاحظات', 'textarea', False, 'notes'),
        ],
    },
    {
        'title': 'تسجيل حوادث التوليد',
        'code': 'electricity.generation_incident',
        'order': 930,
        'attributes': [
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('وقت الحدث', 'text', False, 'event_time'),
            ('الوصف (عربي)', 'textarea', True, 'description_ar'),
            ('الوصف (إنجليزي)', 'textarea', False, 'description_en'),
        ],
    },
    {
        'title': 'تسجيل حوادث الخطوط',
        'code': 'electricity.grid_incident',
        'order': 931,
        'attributes': [
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('اسم الخط', 'text', True, 'line_name'),
            ('الجهد (ك.ف)', 'number', False, 'voltage_kv'),
            ('الإجراء (عربي)', 'textarea', True, 'action_ar'),
            ('الإجراء (إنجليزي)', 'textarea', False, 'action_en'),
        ],
    },
    {
        'title': 'صيانة وملاحظات يومية',
        'code': 'electricity.daily_notes',
        'order': 940,
        'attributes': [
            ('تاريخ التقرير', 'date', True, 'report_date'),
            ('مجموعات الصيانة', 'textarea', False, 'maintenance_groups'),
            ('ملاحظات (عربي)', 'textarea', False, 'notes_ar'),
            ('ملاحظات (إنجليزي)', 'textarea', False, 'notes_en'),
            ('وقت ذروة التوليد', 'text', False, 'peak_generation_time'),
            ('ساعة مرجعية', 'text', False, 'reference_hour'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed electricity daily Info titles under category إدارة قطاع الكهرباء.'

    @staticmethod
    def _upsert_attribute(title, label, attr_type, required, key=''):
        attr = None
        label_ar = (LABEL_AR_FALLBACK.get(key)
                    or label).strip() if key else label
        if key:
            attr = (
                Attribute.objects.filter(
                    title=title, key=key).order_by('id').first()
            )
            if not attr:
                # Legacy rows stored the metric key as label.
                attr = Attribute.objects.filter(
                    title=title, label=key).order_by('id').first()
            if not attr:
                arabic = LABEL_AR_FALLBACK.get(key)
                if arabic:
                    attr = Attribute.objects.filter(
                        title=title, label=arabic).order_by('id').first()
        if not attr:
            attr = Attribute.objects.filter(
                title=title, label=label_ar).first()
        if not attr and label_ar != label:
            attr = Attribute.objects.filter(title=title, label=label).first()
        # Only the national title's metrics are direct dashboard KPI cards
        # (electricity's entity titles feed per-entity tables/computed rollups,
        # same distinction as water's dam/rainfall entity titles).
        is_measure = attr_type == 'number' and title.code == 'electricity.national'
        if attr:
            changed_fields = []
            if attr.label != label_ar:
                attr.label = label_ar
                changed_fields.append('label')
            if key and attr.key != key:
                attr.key = key
                changed_fields.append('key')
            if attr.type != attr_type:
                attr.type = attr_type
                changed_fields.append('type')
            if attr.required != required:
                attr.required = required
                changed_fields.append('required')
            if not attr.is_system:
                attr.is_system = True
                changed_fields.append('is_system')
            if attr.is_measure != is_measure:
                attr.is_measure = is_measure
                changed_fields.append('is_measure')
            if changed_fields:
                attr.save(update_fields=changed_fields)
            return False
        Attribute.objects.create(
            title=title,
            label=label_ar,
            type=attr_type,
            required=required,
            key=key or '',
            is_system=True,
            is_measure=is_measure,
        )
        return True

    @transaction.atomic
    def handle(self, *args, **options):
        category, cat_created = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': 10},
        )
        self.stdout.write(
            f"Category id={category.id} {'created' if cat_created else 'exists'}: {CATEGORY_NAME}"
        )

        attr_created = 0
        for spec in TITLE_SPECS:
            code = spec['code']
            title, title_created = Title.objects.get_or_create(
                name=spec['title'],
                defaults={
                    'order': spec['order'], 'category': category, 'code': code, 'is_system': True},
            )
            changed = []
            if title.category_id != category.id:
                title.category = category
                changed.append('category')
            if title.order != spec['order']:
                title.order = spec['order']
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
                f"  Title id={title.id} {'created' if title_created else 'linked'}: {title.name} (code={code})"
            )
            for row in spec['attributes']:
                if len(row) == 4:
                    label, attr_type, required, key = row
                else:
                    label, attr_type, required = row
                    key = ''
                if self._upsert_attribute(title, label, attr_type, required, key):
                    attr_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. New attributes: {attr_created}.'))
