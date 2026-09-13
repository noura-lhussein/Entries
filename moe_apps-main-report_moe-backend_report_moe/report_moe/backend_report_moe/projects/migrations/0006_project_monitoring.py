import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0005_developmentproject_dates'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectProgressPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_date', models.DateField()),
                ('planned_physical_pct', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('actual_physical_pct', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('planned_cumulative_spend_usd', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('actual_cumulative_spend_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_periods', to='projects.developmentproject')),
            ],
            options={
                'ordering': ['period_date'],
            },
        ),
        migrations.CreateModel(
            name='ProjectMilestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=32)),
                ('title_en', models.CharField(max_length=255)),
                ('title_ar', models.CharField(blank=True, max_length=255)),
                ('milestone_type', models.CharField(choices=[('deliverable', 'Deliverable'), ('financial', 'Financial'), ('physical', 'Physical')], default='deliverable', max_length=16)),
                ('planned_date', models.DateField()),
                ('actual_date', models.DateField(blank=True, null=True)),
                ('weight_pct', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('planned_value_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('actual_value_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('in_progress', 'In progress'), ('completed', 'Completed'), ('delayed', 'Delayed')], default='planned', max_length=16)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='projects.developmentproject')),
            ],
            options={
                'ordering': ['sort_order', 'planned_date', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProjectActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_en', models.CharField(max_length=255)),
                ('title_ar', models.CharField(blank=True, max_length=255)),
                ('category', models.CharField(blank=True, max_length=64)),
                ('planned_start', models.DateField()),
                ('planned_end', models.DateField()),
                ('actual_start', models.DateField(blank=True, null=True)),
                ('actual_end', models.DateField(blank=True, null=True)),
                ('progress_pct', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('status', models.CharField(choices=[('not_started', 'Not started'), ('in_progress', 'In progress'), ('completed', 'Completed'), ('delayed', 'Delayed'), ('on_hold', 'On hold')], default='not_started', max_length=16)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='projects.developmentproject')),
            ],
            options={
                'verbose_name_plural': 'project activities',
                'ordering': ['sort_order', 'planned_start', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='projectprogressperiod',
            constraint=models.UniqueConstraint(fields=('project', 'period_date'), name='projects_unique_progress_period'),
        ),
    ]
