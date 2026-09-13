"""Assert dynamic_forms_inforow still agrees with dynamic_forms_info.

The projection is maintained by triggers (migration 0032), so drift should be
structurally impossible — this command is what proves that claim rather than
assuming it. Run it in CI, after any bulk data command, and on a schedule.

    python manage.py check_info_row_projection            # report
    python manage.py check_info_row_projection --strict   # exit 1 on drift
    python manage.py check_info_row_projection --repair   # recompute drifted keys

Cost is one full aggregate over the cell table (~2 s at 2.7M rows), so it is a
maintenance check, not something to call per request.
"""

from django.core.management.base import BaseCommand
from django.db import connection

# The same aggregate the trigger uses, so a disagreement means the trigger
# missed a write rather than that the two definitions drifted apart.
EXPECTED_SQL = """
SELECT
    i.row_key,
    min(a.title_id)                                        AS title_id,
    min(t.category_id)                                     AS title_category_id,
    min(i.sub_main_id)                                     AS sub_main_id,
    min(s.main_section_id)                                 AS main_section_id,
    min(i.user_id)                                         AS user_id,
    min(i.created_at)                                      AS first_created_at,
    max(i.created_at)                                      AS latest_created_at,
    count(*)                                               AS field_count,
    count(*) FILTER (WHERE i.confirmed = 'accept')         AS accepted_count,
    bool_and(i.confirmed = 'accept')                       AS all_accepted,
    bool_and(i.archived)                                   AS archived,
    max(CASE WHEN i.is_report_date THEN dyn_safe_date(i.value) END) AS report_date,
    coalesce(max(nullif(i.entity_type, '')), '')           AS entity_type,
    max(i.entity_id)                                       AS entity_id
FROM dynamic_forms_info i
JOIN dynamic_forms_attribute a ON a.id = i.attribute_id
LEFT JOIN dynamic_forms_title t ON t.id = a.title_id
LEFT JOIN dynamic_forms_submainsection s ON s.id = i.sub_main_id
WHERE i.row_key IS NOT NULL
GROUP BY i.row_key
HAVING min(a.title_id) IS NOT NULL
"""

DIFF_SQL = f"""
WITH expected AS ({EXPECTED_SQL})
SELECT
    coalesce(e.row_key, r.row_key) AS row_key,
    CASE
        WHEN r.row_key IS NULL THEN 'missing'
        WHEN e.row_key IS NULL THEN 'orphan'
        ELSE 'mismatch'
    END AS kind
FROM expected e
FULL OUTER JOIN dynamic_forms_inforow r ON r.row_key = e.row_key
WHERE r.row_key IS NULL
   OR e.row_key IS NULL
   OR r.title_id           IS DISTINCT FROM e.title_id
   OR r.title_category_id  IS DISTINCT FROM e.title_category_id
   OR r.sub_main_id        IS DISTINCT FROM e.sub_main_id
   OR r.main_section_id    IS DISTINCT FROM e.main_section_id
   OR r.user_id            IS DISTINCT FROM e.user_id
   OR r.first_created_at   IS DISTINCT FROM e.first_created_at
   OR r.latest_created_at  IS DISTINCT FROM e.latest_created_at
   OR r.field_count        IS DISTINCT FROM e.field_count
   OR r.accepted_count     IS DISTINCT FROM e.accepted_count
   OR r.all_accepted       IS DISTINCT FROM e.all_accepted
   OR r.archived           IS DISTINCT FROM e.archived
   OR r.report_date        IS DISTINCT FROM e.report_date
   OR r.entity_type        IS DISTINCT FROM e.entity_type
   OR r.entity_id          IS DISTINCT FROM e.entity_id
"""


class Command(BaseCommand):
    help = "Verify the InfoRow projection matches Info (triggers are working)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict", action="store_true",
            help="Exit 1 when any row disagrees.",
        )
        parser.add_argument(
            "--repair", action="store_true",
            help="Recompute the disagreeing row_keys through the trigger's own function.",
        )
        parser.add_argument(
            "--limit", type=int, default=20,
            help="How many disagreeing keys to print (default 20).",
        )

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(DIFF_SQL)
            rows = cursor.fetchall()

        if not rows:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM dynamic_forms_inforow")
                total = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(
                f"OK: projection matches Info on all {total} logical rows."
            ))
            return

        kinds: dict[str, int] = {}
        for _key, kind in rows:
            kinds[kind] = kinds.get(kind, 0) + 1

        self.stderr.write(self.style.ERROR(
            f"DRIFT: {len(rows)} logical row(s) disagree — " +
            ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
        ))
        for key, kind in rows[: options["limit"]]:
            self.stderr.write(f"  {kind:9} {key}")
        if len(rows) > options["limit"]:
            self.stderr.write(f"  … and {len(rows) - options['limit']} more")

        if options["repair"]:
            keys = [str(key) for key, _kind in rows]
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT dyn_info_row_refresh(%s::uuid[])", [keys]
                )
            self.stdout.write(self.style.SUCCESS(
                f"Repaired {len(keys)} row(s). Re-run to confirm."
            ))
            return

        if options["strict"]:
            raise SystemExit(1)
