"""PostgreSQL triggers that keep dynamic_forms_inforow in step with Info.

Why triggers and not Django signals: `Info` is written from 27 places — eight
creation paths, thirteen management commands, six bulk-update endpoints — and
most of them use `bulk_create` or `queryset.update()`, which never call
`Info.save()` and emit no signal. Rows also disappear through FK CASCADE when an
Attribute or SubMainSection is hard-deleted, and `sector_info_writer` rewrites
`row_key` itself on re-import. A trigger is the only layer that sees all of it,
and being in the same transaction makes drift structurally impossible rather than
merely unlikely.

Statement-level with transition tables (`REFERENCING ... TABLE`), not row-level:
an Excel import inserting several thousand cells pays for one recompute pass
instead of several thousand.
"""

from django.db import migrations

# Recompute the projection for a set of row_keys, then drop the ones whose cells
# are gone. Both halves are set-based; `affected` is the distinct row_keys the
# triggering statement touched.
REFRESH_FN = r"""
CREATE OR REPLACE FUNCTION dyn_safe_date(txt text) RETURNS date AS $$
BEGIN
    RETURN substring(txt from 1 for 10)::date;
EXCEPTION WHEN others THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE SET search_path TO report_moe, public;

CREATE OR REPLACE FUNCTION dyn_info_row_refresh(affected uuid[]) RETURNS void AS $$
BEGIN
    IF affected IS NULL OR cardinality(affected) = 0 THEN
        RETURN;
    END IF;

    INSERT INTO dynamic_forms_inforow AS r (
        row_key, title_id, title_category_id, sub_main_id, main_section_id,
        user_id, first_created_at, latest_created_at, field_count,
        accepted_count, all_accepted, archived, report_date,
        entity_type, entity_id,
        loc_governorate_id, loc_district_id, loc_subdistrict_id, loc_community_id
    )
    SELECT
        i.row_key,
        -- Cells of one record share a title. min() is a deterministic pick if a
        -- rare attribute rewrite ever leaves a record straddling two.
        min(a.title_id),
        min(t.category_id),
        min(i.sub_main_id),
        min(s.main_section_id),
        min(i.user_id),
        min(i.created_at),
        max(i.created_at),
        count(*),
        count(*) FILTER (WHERE i.confirmed = 'accept'),
        bool_and(i.confirmed = 'accept'),
        bool_and(i.archived),
        max(CASE WHEN i.is_report_date THEN dyn_safe_date(i.value) END),
        coalesce(max(nullif(i.entity_type, '')), ''),
        max(i.entity_id),
        max(i.loc_governorate_id),
        max(i.loc_district_id),
        max(i.loc_subdistrict_id),
        max(i.loc_community_id)
    FROM dynamic_forms_info i
    JOIN dynamic_forms_attribute a ON a.id = i.attribute_id
    LEFT JOIN dynamic_forms_title t ON t.id = a.title_id
    LEFT JOIN dynamic_forms_submainsection s ON s.id = i.sub_main_id
    WHERE i.row_key = ANY(affected)
    GROUP BY i.row_key
    -- Attribute.title is nullable (shared attributes). A record with no title is
    -- not something any screen lists, and title_id is NOT NULL here.
    HAVING min(a.title_id) IS NOT NULL
    ON CONFLICT (row_key) DO UPDATE SET
        title_id           = EXCLUDED.title_id,
        title_category_id  = EXCLUDED.title_category_id,
        sub_main_id        = EXCLUDED.sub_main_id,
        main_section_id    = EXCLUDED.main_section_id,
        user_id            = EXCLUDED.user_id,
        first_created_at   = EXCLUDED.first_created_at,
        latest_created_at  = EXCLUDED.latest_created_at,
        field_count        = EXCLUDED.field_count,
        accepted_count     = EXCLUDED.accepted_count,
        all_accepted       = EXCLUDED.all_accepted,
        archived           = EXCLUDED.archived,
        report_date        = EXCLUDED.report_date,
        entity_type        = EXCLUDED.entity_type,
        entity_id          = EXCLUDED.entity_id,
        loc_governorate_id = EXCLUDED.loc_governorate_id,
        loc_district_id    = EXCLUDED.loc_district_id,
        loc_subdistrict_id = EXCLUDED.loc_subdistrict_id,
        loc_community_id   = EXCLUDED.loc_community_id;

    -- Cells gone (CASCADE delete, dedupe command, row_key rewritten away) or the
    -- record no longer resolves to a title: the projection row goes with them.
    DELETE FROM dynamic_forms_inforow r
    WHERE r.row_key = ANY(affected)
      AND NOT EXISTS (
          SELECT 1
          FROM dynamic_forms_info i
          JOIN dynamic_forms_attribute a ON a.id = i.attribute_id
          WHERE i.row_key = r.row_key AND a.title_id IS NOT NULL
      );
END;
$$ LANGUAGE plpgsql SET search_path TO report_moe, public;
"""

TRIGGER_FNS = r"""
CREATE OR REPLACE FUNCTION dyn_info_row_tg_ins() RETURNS trigger AS $$
DECLARE keys uuid[];
BEGIN
    SELECT array_agg(DISTINCT row_key) INTO keys
    FROM new_rows WHERE row_key IS NOT NULL;
    PERFORM report_moe.dyn_info_row_refresh(keys);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path TO report_moe, public;

CREATE OR REPLACE FUNCTION dyn_info_row_tg_upd() RETURNS trigger AS $$
DECLARE keys uuid[];
BEGIN
    -- Union of old and new: `sector_info_writer._archive_row_key` reassigns
    -- row_key on re-import, so both the vacated and the arriving record change.
    SELECT array_agg(DISTINCT k) INTO keys FROM (
        SELECT row_key AS k FROM old_rows WHERE row_key IS NOT NULL
        UNION
        SELECT row_key FROM new_rows WHERE row_key IS NOT NULL
    ) u;
    PERFORM report_moe.dyn_info_row_refresh(keys);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path TO report_moe, public;

CREATE OR REPLACE FUNCTION dyn_info_row_tg_del() RETURNS trigger AS $$
DECLARE keys uuid[];
BEGIN
    SELECT array_agg(DISTINCT row_key) INTO keys
    FROM old_rows WHERE row_key IS NOT NULL;
    PERFORM report_moe.dyn_info_row_refresh(keys);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path TO report_moe, public;

CREATE OR REPLACE FUNCTION dyn_info_row_tg_trunc() RETURNS trigger AS $$
BEGIN
    -- config/data_transfer.py TRUNCATEs every table in the schema.
    TRUNCATE dynamic_forms_inforow;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SET search_path TO report_moe, public;
"""

TRIGGERS = r"""
DROP TRIGGER IF EXISTS dyn_info_row_ins ON dynamic_forms_info;
CREATE TRIGGER dyn_info_row_ins
    AFTER INSERT ON dynamic_forms_info
    REFERENCING NEW TABLE AS new_rows
    FOR EACH STATEMENT EXECUTE FUNCTION dyn_info_row_tg_ins();

DROP TRIGGER IF EXISTS dyn_info_row_upd ON dynamic_forms_info;
CREATE TRIGGER dyn_info_row_upd
    AFTER UPDATE ON dynamic_forms_info
    REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
    FOR EACH STATEMENT EXECUTE FUNCTION dyn_info_row_tg_upd();

DROP TRIGGER IF EXISTS dyn_info_row_del ON dynamic_forms_info;
CREATE TRIGGER dyn_info_row_del
    AFTER DELETE ON dynamic_forms_info
    REFERENCING OLD TABLE AS old_rows
    FOR EACH STATEMENT EXECUTE FUNCTION dyn_info_row_tg_del();

DROP TRIGGER IF EXISTS dyn_info_row_trunc ON dynamic_forms_info;
CREATE TRIGGER dyn_info_row_trunc
    AFTER TRUNCATE ON dynamic_forms_info
    FOR EACH STATEMENT EXECUTE FUNCTION dyn_info_row_tg_trunc();
"""

# Runs after the triggers exist, so anything written concurrently is already
# projected and simply loses the ON CONFLICT race harmlessly.
BACKFILL = r"""
INSERT INTO dynamic_forms_inforow (
    row_key, title_id, title_category_id, sub_main_id, main_section_id,
    user_id, first_created_at, latest_created_at, field_count,
    accepted_count, all_accepted, archived, report_date,
    entity_type, entity_id,
    loc_governorate_id, loc_district_id, loc_subdistrict_id, loc_community_id
)
SELECT
    i.row_key, min(a.title_id), min(t.category_id), min(i.sub_main_id),
    min(s.main_section_id), min(i.user_id), min(i.created_at), max(i.created_at),
    count(*), count(*) FILTER (WHERE i.confirmed = 'accept'),
    bool_and(i.confirmed = 'accept'), bool_and(i.archived),
    max(CASE WHEN i.is_report_date THEN dyn_safe_date(i.value) END),
    coalesce(max(nullif(i.entity_type, '')), ''), max(i.entity_id),
    max(i.loc_governorate_id), max(i.loc_district_id),
    max(i.loc_subdistrict_id), max(i.loc_community_id)
FROM dynamic_forms_info i
JOIN dynamic_forms_attribute a ON a.id = i.attribute_id
LEFT JOIN dynamic_forms_title t ON t.id = a.title_id
LEFT JOIN dynamic_forms_submainsection s ON s.id = i.sub_main_id
WHERE i.row_key IS NOT NULL
GROUP BY i.row_key
HAVING min(a.title_id) IS NOT NULL
ON CONFLICT (row_key) DO NOTHING;
"""

DROP_ALL = r"""
DROP TRIGGER IF EXISTS dyn_info_row_ins ON dynamic_forms_info;
DROP TRIGGER IF EXISTS dyn_info_row_upd ON dynamic_forms_info;
DROP TRIGGER IF EXISTS dyn_info_row_del ON dynamic_forms_info;
DROP TRIGGER IF EXISTS dyn_info_row_trunc ON dynamic_forms_info;
DROP FUNCTION IF EXISTS dyn_info_row_tg_ins();
DROP FUNCTION IF EXISTS dyn_info_row_tg_upd();
DROP FUNCTION IF EXISTS dyn_info_row_tg_del();
DROP FUNCTION IF EXISTS dyn_info_row_tg_trunc();
DROP FUNCTION IF EXISTS dyn_info_row_refresh(uuid[]);
DROP FUNCTION IF EXISTS dyn_safe_date(text);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0031_drop_corrupt_row_key_index"),
    ]

    operations = [
        migrations.RunSQL(sql=REFRESH_FN, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql=TRIGGER_FNS, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql=TRIGGERS, reverse_sql=DROP_ALL),
        migrations.RunSQL(
            sql=BACKFILL,
            reverse_sql="TRUNCATE dynamic_forms_inforow;",
        ),
    ]
