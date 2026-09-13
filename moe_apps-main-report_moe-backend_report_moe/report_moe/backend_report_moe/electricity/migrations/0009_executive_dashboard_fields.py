from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0008_fix_misdated_may_2026_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='hydrodamreading',
            name='expected_m3s',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='hydrodamreading',
            name='inflow_m3s',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='hydrodamreading',
            name='dam_code',
            field=models.CharField(
                choices=[
                    ('thawra', 'Thawra (Revolution)'),
                    ('euphrates', 'Euphrates (Thawra)'),
                    ('tishreen', 'Tishreen'),
                ],
                max_length=32,
            ),
        ),
    ]
