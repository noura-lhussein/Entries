"""Point the sector tables' user foreign keys at the single user table.

Before the merge each project had its own `accounts_user`, one per schema, and the
sector tables in schema `moeds` referenced the copy that lived there. One backend
means one AUTH_USER_MODEL, so those keys have to reference `report_moe.accounts_user`
instead.

Django will not generate this. Every FK to the user model is recorded in the
migrations as the symbolic `settings.AUTH_USER_MODEL`, so pointing that setting at
one model changes what the ORM reads while leaving the physical constraints aimed
where they were; `makemigrations` correctly reports "no changes". The constraints
are therefore rebuilt here by hand.

Constraint names are discovered rather than hard-coded. They follow three different
patterns in this database — `..._fk_moe_accou` from when the table was called
`moe_accounts_user`, `..._fk_accounts_user` from after the rename, and one written
by hand in the auth-split scripts — so any list of literal names would break on a
database whose objects were created in a different order.

`pg_get_constraintdef` is reused rather than writing a fresh definition: the ON
DELETE rule and the deferrability of each key survive untouched, and only the
referenced table changes.

Left alone on purpose: `accounts_user` (its self-referencing parent key),
`accounts_user_groups`, `accounts_user_user_permissions`,
`accounts_outstandingrefreshtoken` and `django_admin_log` in schema `moeds`. Those
belong to the abandoned copy of the user table, which nothing reads any more.
"""

from django.db import migrations

# One statement, run twice with the direction reversed. `%(target)s` is the schema
# whose accounts_user the keys should point at; `%(source)s` is where they point now.
_REPOINT = """
DO $$
DECLARE
    r        record;
    newdef   text;
    orphans  bigint;
BEGIN
    -- Nothing to do when the old table is already gone (a database built fresh
    -- from these migrations never had one).
    IF to_regclass('%(source)s.accounts_user') IS NULL THEN
        RAISE NOTICE 'accounts_user not present in schema %(source)s — nothing to repoint';
        RETURN;
    END IF;

    FOR r IN
        SELECT n.nspname AS sch, t.relname AS tbl, c.conname AS cname,
               pg_get_constraintdef(c.oid) AS def,
               (SELECT a.attname
                  FROM pg_attribute a
                 WHERE a.attrelid = c.conrelid AND a.attnum = c.conkey[1]) AS col
        FROM pg_constraint c
        JOIN pg_class t      ON t.oid  = c.conrelid
        JOIN pg_namespace n  ON n.oid  = t.relnamespace
        JOIN pg_class rt     ON rt.oid = c.confrelid
        JOIN pg_namespace rn ON rn.oid = rt.relnamespace
        WHERE c.contype = 'f'
          AND rt.relname = 'accounts_user'
          AND rn.nspname = '%(source)s'
          AND n.nspname  = 'moeds'
          AND t.relname NOT LIKE 'accounts\\_%%'
          AND t.relname <> 'django_admin_log'
    LOOP
        -- A row pointing at a user that does not exist in the target table would
        -- be silently dropped or would fail the ALTER; stop and say which table.
        EXECUTE format(
            'SELECT count(*) FROM %%I.%%I c LEFT JOIN %(target)s.accounts_user u '
            'ON u.id = c.%%I WHERE c.%%I IS NOT NULL AND u.id IS NULL',
            r.sch, r.tbl, r.col, r.col
        ) INTO orphans;
        IF orphans > 0 THEN
            RAISE EXCEPTION
                '%%.%%.%% has %% row(s) referencing a user missing from %(target)s.accounts_user',
                r.sch, r.tbl, r.col, orphans;
        END IF;

        newdef := regexp_replace(r.def, 'REFERENCES [^ ]+\\(id\\)',
                                 'REFERENCES %(target)s.accounts_user(id)');
        EXECUTE format('ALTER TABLE %%I.%%I DROP CONSTRAINT %%I', r.sch, r.tbl, r.cname);
        EXECUTE format('ALTER TABLE %%I.%%I ADD CONSTRAINT %%I %%s', r.sch, r.tbl, r.cname, newdef);
        RAISE NOTICE 'repointed %%.%%.%%', r.sch, r.tbl, r.cname;
    END LOOP;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        # The reporting side must be fully built before anything points at it.
        ("dynamic_forms", "0027_info_report_date_unique"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_REPOINT % {"source": "moeds", "target": "report_moe"},
            reverse_sql=_REPOINT % {"source": "report_moe", "target": "moeds"},
        ),
    ]