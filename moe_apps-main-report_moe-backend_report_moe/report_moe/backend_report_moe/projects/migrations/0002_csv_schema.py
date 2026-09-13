from __future__ import annotations

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def clear_legacy_projects(apps, schema_editor):
    DevelopmentProject = apps.get_model('projects', 'DevelopmentProject')
    DevelopmentProject.objects.all().delete()


def seed_placeholder_refs(apps, schema_editor):
    ProjectGovernorate = apps.get_model('projects', 'ProjectGovernorate')
    ProjectOrganization = apps.get_model('projects', 'ProjectOrganization')
    ProjectGovernorate.objects.get_or_create(
        id=1,
        defaults={'pcode': 'SY08', 'name_en': 'Al-Hasakeh', 'name_ar': 'الحسكة'},
    )
    ProjectOrganization.objects.get_or_create(
        id=1,
        defaults={'slug': 'org-1', 'acronym': 'O1', 'name_en': 'Institution 1'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectGovernorate',
            fields=[
                ('id', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('pcode', models.CharField(blank=True, max_length=16)),
                ('name_en', models.CharField(max_length=128)),
                ('name_ar', models.CharField(blank=True, max_length=128)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ProjectOrganization',
            fields=[
                ('id', models.PositiveSmallIntegerField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=64)),
                ('acronym', models.CharField(blank=True, max_length=32)),
                ('name_en', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.RunPython(clear_legacy_projects, migrations.RunPython.noop),
        migrations.RunPython(seed_placeholder_refs, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='developmentproject',
            name='governorate_name_ar',
        ),
        migrations.RemoveField(
            model_name='developmentproject',
            name='governorate_name_en',
        ),
        migrations.RemoveField(
            model_name='developmentproject',
            name='governorate_pcode',
        ),
        migrations.RemoveField(
            model_name='developmentproject',
            name='organization_acronym',
        ),
        migrations.RemoveField(
            model_name='developmentproject',
            name='organization_name_en',
        ),
        migrations.RemoveField(
            model_name='developmentproject',
            name='organization_slug',
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='location',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='developmentproject',
            name='sector',
            field=models.CharField(db_index=True, max_length=32),
        ),
        migrations.AlterField(
            model_name='developmentproject',
            name='status',
            field=models.CharField(default='active', max_length=16),
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='governorate',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='projects',
                to='projects.projectgovernorate',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='organization',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='projects',
                to='projects.projectorganization',
            ),
            preserve_default=False,
        ),
    ]
