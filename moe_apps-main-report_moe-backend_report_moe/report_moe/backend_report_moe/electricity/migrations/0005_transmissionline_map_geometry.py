from __future__ import annotations

from decimal import Decimal

from django.db import migrations, models


def seed_transmission_coordinates(apps, schema_editor):
    TransmissionLine = apps.get_model('electricity', 'TransmissionLine')
    TransmissionLine.objects.filter(name='Damascus–Homs 400 kV').update(
        source_latitude=Decimal('33.513800'),
        source_longitude=Decimal('36.276500'),
        dest_latitude=Decimal('34.731900'),
        dest_longitude=Decimal('36.709800'),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('electricity', '0004_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transmissionline',
            name='dest_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transmissionline',
            name='dest_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transmissionline',
            name='source_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='transmissionline',
            name='source_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.RunPython(seed_transmission_coordinates, migrations.RunPython.noop),
    ]
