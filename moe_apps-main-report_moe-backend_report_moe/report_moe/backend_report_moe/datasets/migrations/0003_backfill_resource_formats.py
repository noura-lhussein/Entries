from django.db import migrations


def backfill_resource_formats(apps, schema_editor):
    from datasets.services import backfill_resource_formats as sync_formats

    sync_formats()


class Migration(migrations.Migration):
    dependencies = [
        ('datasets', '0002_dataset_external_url_dataset_source_file'),
    ]

    operations = [
        migrations.RunPython(backfill_resource_formats, migrations.RunPython.noop),
    ]
