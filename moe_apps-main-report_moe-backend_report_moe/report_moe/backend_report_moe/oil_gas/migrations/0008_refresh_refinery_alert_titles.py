from django.db import migrations

REFINERY_NAMES_AR = {
    'Banias Refinery': 'بانياس',
    'Homs Refinery': 'حمص',
    'مصفاة بانياس': 'بانياس',
    'مصفاة حمص': 'حمص',
}

ALERT_TITLE_FIXES = {
    'توقف مصفاة Banias Refinery': 'توقف مصفاة بانياس',
    'توقف مصفاة Homs Refinery': 'توقف مصفاة حمص',
}


def refresh_refinery_data(apps, schema_editor):
    Refinery = apps.get_model('oil_gas', 'Refinery')
    Alert = apps.get_model('oil_gas', 'Alert')

    for refinery_name, name_ar in REFINERY_NAMES_AR.items():
        Refinery.objects.filter(refinery_name=refinery_name).update(name_ar=name_ar)

    for old_title, new_title in ALERT_TITLE_FIXES.items():
        Alert.objects.filter(title_ar=old_title, is_resolved=False).update(title_ar=new_title)


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0007_refinery_name_ar'),
    ]

    operations = [
        migrations.RunPython(refresh_refinery_data, migrations.RunPython.noop),
    ]
