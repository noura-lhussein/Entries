from datetime import date

from django.db import migrations, models


def backfill_project_dates(apps, schema_editor):
    DevelopmentProject = apps.get_model('projects', 'DevelopmentProject')
    for project in DevelopmentProject.objects.all().iterator():
        changed = False
        if project.start_year and not project.start_date:
            project.start_date = date(int(project.start_year), 1, 1)
            changed = True
        if project.reporting_through and not project.end_date:
            project.end_date = project.reporting_through
            changed = True
        if changed:
            project.save(update_fields=['start_date', 'end_date'])


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0004_developmentproject_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='developmentproject',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='developmentproject',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_project_dates, migrations.RunPython.noop),
    ]
