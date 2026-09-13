from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('electricity', '0002_gridoutage'),
    ]

    operations = [
        migrations.DeleteModel(name='DailyReport'),

    ]
