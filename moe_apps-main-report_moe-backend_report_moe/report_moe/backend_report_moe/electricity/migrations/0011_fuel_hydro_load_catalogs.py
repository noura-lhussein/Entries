from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0010_dailyreport_maintenance_groups_ar'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuelTankStation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name_ar', models.CharField(max_length=200)),
                ('name_en', models.CharField(max_length=200)),
                ('max_capacity_tons', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ],
            options={'ordering': ['name_ar', 'id']},
        ),
        migrations.CreateModel(
            name='HydroDam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name_ar', models.CharField(max_length=200)),
                ('name_en', models.CharField(max_length=200)),
            ],
            options={'ordering': ['name_ar', 'id']},
        ),
        migrations.CreateModel(
            name='LoadGovernorate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name_ar', models.CharField(max_length=200)),
                ('name_en', models.CharField(max_length=200)),
            ],
            options={'ordering': ['name_ar', 'id']},
        ),
    ]
