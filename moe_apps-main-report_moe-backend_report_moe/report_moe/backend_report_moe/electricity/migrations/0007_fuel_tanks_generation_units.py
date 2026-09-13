from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0006_rename_daily_metric_keys'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyreport',
            name='peak_generation_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='FuelTankReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_code', models.CharField(db_index=True, max_length=32)),
                ('current_tons', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('max_capacity_tons', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                (
                    'report',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='fuel_tank_readings',
                        to='electricity.dailyreport',
                    ),
                ),
            ],
            options={
                'ordering': ['station_code'],
            },
        ),
        migrations.CreateModel(
            name='GenerationUnitReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plant_code', models.CharField(db_index=True, max_length=32)),
                ('unit_code', models.CharField(blank=True, default='', max_length=32)),
                ('nominal_mw', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('available_mw', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('generation_mwh_24h', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('active', 'Active'),
                            ('maintenance', 'Maintenance'),
                            ('outage', 'Outage'),
                            ('standby', 'Standby'),
                        ],
                        default='active',
                        max_length=16,
                    ),
                ),
                (
                    'report',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='generation_unit_readings',
                        to='electricity.dailyreport',
                    ),
                ),
            ],
            options={
                'ordering': ['plant_code', 'unit_code'],
            },
        ),
        migrations.AddConstraint(
            model_name='fueltankreading',
            constraint=models.UniqueConstraint(
                fields=('report', 'station_code'),
                name='electricity_unique_fuel_tank_per_report',
            ),
        ),
        migrations.AddConstraint(
            model_name='generationunitreading',
            constraint=models.UniqueConstraint(
                fields=('report', 'plant_code', 'unit_code'),
                name='electricity_unique_generation_unit_per_report',
            ),
        ),
    ]
