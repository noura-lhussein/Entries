import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dynamic_forms', '0017_nested_sections_and_info_entity'),
    ]

    operations = [
        migrations.CreateModel(
            name='TitleCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('order', models.PositiveIntegerField(default=1)),
            ],
            options={
                'verbose_name_plural': 'title categories',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='title',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='titles',
                to='dynamic_forms.titlecategory',
            ),
        ),
        migrations.CreateModel(
            name='UserTitleCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'category',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='user_assignments',
                        to='dynamic_forms.titlecategory',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='user_title_categories',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name='usertitlecategory',
            constraint=models.UniqueConstraint(
                fields=('user', 'category'),
                name='dynamic_forms_unique_user_title_category',
            ),
        ),
    ]
