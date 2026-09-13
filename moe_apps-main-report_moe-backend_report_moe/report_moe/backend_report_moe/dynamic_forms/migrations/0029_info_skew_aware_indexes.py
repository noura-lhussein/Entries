"""Index surgery for dynamic_forms_info, driven by the live data skew.

Measured on 2,695,512 rows: `confirmed='accept'` on 2,695,143 of them and
`archived=False` on all of them. Both columns therefore lead the three largest
indexes (199 + 152 + 130 MB) while contributing no selectivity at all.

These four btree indexes move that pair out of the index KEY and into a partial
WHERE clause — same rows covered, two fewer columns stored — plus one tiny index
over the 369 rows that are *not* accepted, which is what the review queue reads.

The GIN trigram index serves the `value__icontains` search in
info_rows_views / export_report / info_views, which was a sequential scan over
2.7M rows. pg_trgm is already installed on this cluster.

Built CONCURRENTLY (hence `atomic = False`) so the table stays writable. If a
build is interrupted Postgres leaves an INVALID index behind; drop it by name and
re-run.
"""

from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("dynamic_forms", "0028_info_rows_list_index"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="info",
            index=models.Index(
                fields=["attribute", "row_key"],
                name="dyn_info_hot_attr_rk",
                condition=models.Q(archived=False, confirmed="accept"),
            ),
        ),
        AddIndexConcurrently(
            model_name="info",
            index=models.Index(
                fields=["attribute", "-created_at"],
                name="dyn_info_attr_created",
                condition=models.Q(archived=False, confirmed="accept"),
            ),
        ),
        AddIndexConcurrently(
            model_name="info",
            index=models.Index(
                fields=["sub_main", "-created_at"],
                name="dyn_info_sub_created",
                condition=models.Q(archived=False, confirmed="accept"),
            ),
        ),
        AddIndexConcurrently(
            model_name="info",
            index=models.Index(
                fields=["confirmed", "attribute", "-created_at"],
                name="dyn_info_pending",
                condition=~models.Q(confirmed="accept"),
            ),
        ),
        # The live database already had pg_trgm, but a freshly created test
        # database does not — create it here so the migration is self-contained.
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS dyn_info_value_trgm "
                "ON dynamic_forms_info USING gin (value gin_trgm_ops);"
            ),
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS dyn_info_value_trgm;",
        ),
    ]
