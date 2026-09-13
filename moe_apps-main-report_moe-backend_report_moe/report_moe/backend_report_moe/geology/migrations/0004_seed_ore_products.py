from django.db import migrations

# Matches old_moeds's geology/ore_catalog.py DEFAULT_ORE_PRODUCTS list.
# (name_ar, name_en, production_type, unit)
DEFAULT_ORE_PRODUCTS = (
    ('الجص', 'Gypsum', '', 'طن'),
    ('رمال كوارتزية', 'Quartz sand', 'ذاتي', 'طن'),
    ('رمال كوارتزية', 'Quartz sand', 'معهّد', 'م3'),
    ('ملح', 'Salt', '', 'طن'),
    ('الاسمنت', 'Cement', '', 'طن'),
    ('دولوميت', 'Dolomite', '', 'طن'),
    ('غضار', 'Clay', '', 'طن'),
    ('سجيل زيتي', 'Oil shale', '', 'طن'),
    ('حديد', 'Iron', '', 'طن'),
    ('رخام', 'Marble', '', 'طن'),
    ('سكوريا', 'Scoria', '', 'طن'),
    ('حجر جيري', 'Limestone', '', 'طن'),
    ('اسفلت', 'Asphalt', '', 'طن'),
    ('فوسفات', 'Phosphate', '', 'طن'),
    ('بازلت', 'Basalt', '', 'طن'),
    ('بنتونيت', 'Bentonite', '', 'طن'),
    ('تراكيت', 'Trachyte', '', 'طن'),
    ('زيوليت', 'Zeolite', '', 'طن'),
    ('تريبولي', 'Tripoli', '', 'طن'),
    ('تورب', 'Peat', '', 'طن'),
    ('سيانيت نيفيليني', 'Nepheline syenite', '', 'طن'),
)


def seed_ore_products(apps, schema_editor):
    OreProduct = apps.get_model('geology', 'OreProduct')
    if OreProduct.objects.exists():
        return
    for index, (name_ar, name_en, production_type, unit) in enumerate(DEFAULT_ORE_PRODUCTS):
        OreProduct.objects.create(
            name_ar=name_ar,
            name_en=name_en,
            production_type=production_type,
            unit=unit,
            sort_order=index,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('geology', '0003_oreproduct'),
    ]

    operations = [
        migrations.RunPython(seed_ore_products, noop_reverse),
    ]
