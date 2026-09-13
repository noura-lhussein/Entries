from __future__ import annotations

from django.db import migrations, models
from django.utils import timezone


def copy_source_files_to_resources(apps, schema_editor):
    Dataset = apps.get_model('datasets', 'Dataset')
    DatasetResource = apps.get_model('datasets', 'DatasetResource')

    for dataset in Dataset.objects.filter(source_file__isnull=False).exclude(source_file=''):
        source_name = (dataset.source_file.name or '').strip()
        if not source_name:
            continue
        if DatasetResource.objects.filter(dataset_id=dataset.id, file=source_name).exists():
            continue
        DatasetResource.objects.create(
            dataset_id=dataset.id,
            file=source_name,
            sort_order=0,
            created_at=dataset.updated_at or timezone.now(),
        )


class Migration(migrations.Migration):
    dependencies = [
        ('datasets', '0003_backfill_resource_formats'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='datasets/files/')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                (
                    'dataset',
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name='resources',
                        to='datasets.dataset',
                    ),
                ),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.RunPython(copy_source_files_to_resources, migrations.RunPython.noop),
    ]
