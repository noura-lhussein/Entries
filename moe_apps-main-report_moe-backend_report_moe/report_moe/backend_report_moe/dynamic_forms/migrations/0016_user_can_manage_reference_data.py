from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0015_remove_legacy_location_models"),
    ]

    operations = [
        # can_manage_reference_data moved to accounts.User
    ]
