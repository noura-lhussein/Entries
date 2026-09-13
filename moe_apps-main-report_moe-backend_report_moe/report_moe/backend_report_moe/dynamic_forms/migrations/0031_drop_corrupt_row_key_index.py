"""Drop the standalone row_key index — redundant, and physically corrupt.

`dyn_info_rowkey_attr_idx` is `(row_key, attribute_id)`, so row_key is already a
leading column and this second index only added write cost for 58 MB.

It also turned out to be damaged: any plan that used it failed with
`invalid page in block 737 of relation "base/16384/49574"`, which is what stopped
the projection backfill in the next migration. A forced full heap scan read all
2,695,512 rows cleanly, so the table itself is intact and dropping the index both
repairs the fault and removes a planned redundancy.

Must run before the trigger/backfill migration: the backfill's `GROUP BY row_key`
is exactly the plan that reaches for this index.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0030_info_row_projection"),
    ]

    operations = [
        migrations.AlterField(
            model_name="info",
            name="row_key",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
