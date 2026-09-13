from django.db import migrations, models

REFINERY_NAMES_AR = {
    'Banias Refinery': 'بانياس',
    'Homs Refinery': 'حمص',
    'مصفاة بانياس': 'بانياس',
    'مصفاة حمص': 'حمص',
}


def set_refinery_names_ar(apps, schema_editor):
    Refinery = apps.get_model('oil_gas', 'Refinery')
    for refinery_name, name_ar in REFINERY_NAMES_AR.items():
        Refinery.objects.filter(refinery_name=refinery_name).update(name_ar=name_ar)

    Alert = apps.get_model('oil_gas', 'Alert')
    for refinery_name, name_ar in REFINERY_NAMES_AR.items():
        Alert.objects.filter(
            title_ar=f'توقف مصفاة {refinery_name}',
            is_resolved=False,
        ).update(title_ar=f'توقف مصفاة {name_ar}')


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0006_map_geometry'),
    ]

    operations = [
        migrations.AddField(
            model_name='refinery',
            name='name_ar',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.RunPython(set_refinery_names_ar, migrations.RunPython.noop),
    ]
