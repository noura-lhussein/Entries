from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('water', '0003_euphratescascadereading'),
    ]

    operations = [
        migrations.AddField(
            model_name='rainfallbasin',
            name='area_km2',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
