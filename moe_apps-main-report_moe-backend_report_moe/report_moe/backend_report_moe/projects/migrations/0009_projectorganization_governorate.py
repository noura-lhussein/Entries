import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_seed_project_activities'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectorganization',
            name='governorate',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='organizations',
                to='projects.projectgovernorate',
            ),
        ),
    ]
