# Generated manually for operational targets + audit fields

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

AUDIT_FIELDS = [
    ('dailyproduction', 'DailyProduction'),
    ('refinerydailyoutput', 'RefineryDailyOutput'),
    ('fuelinventory', 'FuelInventory'),
    ('export', 'Export'),
]


def audit_field_operations():
    ops = []
    for model_name, _ in AUDIT_FIELDS:
        ops.extend(
            [
                migrations.AddField(
                    model_name=model_name,
                    name='source',
                    field=models.CharField(
                        choices=[
                            ('manual', 'Manual'),
                            ('api', 'API'),
                            ('import', 'Import'),
                            ('seed', 'Seed'),
                        ],
                        default='seed',
                        max_length=16,
                    ),
                ),
                migrations.AddField(
                    model_name=model_name,
                    name='created_at',
                    field=models.DateTimeField(
                        auto_now_add=True,
                        default=django.utils.timezone.now,
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name=model_name,
                    name='updated_at',
                    field=models.DateTimeField(
                        auto_now=True,
                        default=django.utils.timezone.now,
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name=model_name,
                    name='updated_by',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ]
        )
    return ops


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0002_alert_export_field_fuelconsumptionbaseline_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        *audit_field_operations(),
        migrations.CreateModel(
            name='OperationalTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_key', models.CharField(db_index=True, max_length=64)),
                (
                    'scope_type',
                    models.CharField(
                        choices=[
                            ('national', 'National'),
                            ('field', 'Field'),
                            ('refinery', 'Refinery'),
                            ('facility', 'Facility'),
                        ],
                        default='national',
                        max_length=20,
                    ),
                ),
                ('scope_code', models.CharField(blank=True, default='', max_length=100)),
                (
                    'period_type',
                    models.CharField(
                        choices=[('daily', 'Daily'), ('monthly', 'Monthly')],
                        default='daily',
                        max_length=20,
                    ),
                ),
                ('period_start', models.DateField(db_index=True)),
                ('period_end', models.DateField(blank=True, null=True)),
                ('target_value', models.DecimalField(decimal_places=4, max_digits=18)),
                ('unit', models.CharField(blank=True, max_length=24)),
                ('label_ar', models.CharField(blank=True, max_length=200)),
                ('label_en', models.CharField(blank=True, max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-period_start', 'metric_key'],
            },
        ),
        migrations.AddConstraint(
            model_name='operationaltarget',
            constraint=models.UniqueConstraint(
                fields=('metric_key', 'scope_type', 'scope_code', 'period_type', 'period_start'),
                name='oil_gas_unique_operational_target',
            ),
        ),
        migrations.AddIndex(
            model_name='operationaltarget',
            index=models.Index(fields=['scope_type', 'scope_code', 'period_start'], name='oil_gas_oper_scope_idx'),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_export_revenue_usd',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_gas_supply_to_power_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_gasoline_stock_days',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_total_export_bbl',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_total_gas_production_mmscf',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='kpidailysnapshot',
            name='target_total_oil_production_bpd',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True),
        ),
    ]
