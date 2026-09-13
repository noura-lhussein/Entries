from django.db import migrations


def seed_project_activities(apps, schema_editor):
    from projects.activity_provisioning import provision_project_activities
    from projects.models import DevelopmentProject

    for project in DevelopmentProject.objects.all().iterator():
        provision_project_activities(project, with_example_actuals=True, force=True)


def unseed_project_activities(apps, schema_editor):
    ProjectActivityPeriod = apps.get_model('projects', 'ProjectActivityPeriod')
    ProjectActivity = apps.get_model('projects', 'ProjectActivity')
    ProjectProgressPeriod = apps.get_model('projects', 'ProjectProgressPeriod')

    ProjectActivityPeriod.objects.all().delete()
    ProjectActivity.objects.all().delete()
    ProjectProgressPeriod.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0007_activity_period_monitoring'),
    ]

    operations = [
        migrations.RunPython(seed_project_activities, unseed_project_activities),
    ]
