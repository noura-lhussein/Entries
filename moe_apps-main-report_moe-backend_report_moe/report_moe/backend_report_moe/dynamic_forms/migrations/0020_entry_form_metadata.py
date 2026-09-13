from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic_forms', '0019_structure_soft_delete_and_info_archive'),
    ]

    operations = [
        migrations.AddField(
            model_name='title',
            name='subtitle',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='title',
            name='entry_mode',
            field=models.CharField(default='single_record', max_length=32),
        ),
        migrations.AddField(
            model_name='title',
            name='field_groups',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='title',
            name='preview_field_keys',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='attribute',
            name='key',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='attribute',
            name='order',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='attribute',
            name='group',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='attribute',
            name='unit_ar',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='attribute',
            name='help_ar',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='attribute',
            name='readonly',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attribute',
            name='computed_from',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='attribute',
            name='min_value',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='max_value',
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='attribute',
            name='max_field',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='attribute',
            name='warn_if_gt_field',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='attribute',
            name='message_ar',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='attribute',
            name='decimals',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterModelOptions(
            name='attribute',
            options={'ordering': ['order', 'id']},
        ),
    ]
