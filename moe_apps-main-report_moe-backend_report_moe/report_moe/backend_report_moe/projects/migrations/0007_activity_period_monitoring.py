import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0006_project_monitoring'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectactivity',
            name='planned_budget_usd',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='projectactivity',
            name='weight_pct',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.CreateModel(
            name='ProjectActivityPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_date', models.DateField()),
                ('planned_physical_pct', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('actual_physical_pct', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('planned_cumulative_spend_usd', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('actual_cumulative_spend_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='projects.projectactivity')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_periods', to='projects.developmentproject')),
            ],
            options={
                'ordering': ['period_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='projectactivityperiod',
            constraint=models.UniqueConstraint(fields=('activity', 'period_date'), name='projects_unique_activity_period'),
        ),
    ]
