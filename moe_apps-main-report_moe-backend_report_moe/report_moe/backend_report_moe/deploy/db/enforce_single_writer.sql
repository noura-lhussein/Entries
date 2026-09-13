-- Enforce the single-writer rule for moe_shared at the database level.
--
-- moeds and report_moe integrate through this database, not through an API between them.
-- That model is only sound if each table has exactly one writer. Application code alone
-- cannot guarantee it — a forgotten management command or a new endpoint silently breaks
-- the rule. These grants make PostgreSQL the enforcer: a stray write fails loudly with
-- InsufficientPrivilege instead of corrupting the other project's data.
--
-- Ownership split:
--   report_moe owns the 24 master/catalog tables listed below (schema `moeds`).
--   moeds owns everything else in schema `moeds` (operational: daily reports, metrics,
--   readings, snapshots, GIS admin boundaries).
--   Each also owns its own auth tables (accounts_user, sessions, content types,
--   permissions) inside its own schema; both read `public` (PostGIS catalog).
--
-- Run as a superuser:
--   psql -U postgres -d moe_shared -v moeds_pw='...' -v report_pw='...' \
--        -f enforce_single_writer.sql
--
-- MIGRATIONS still run as the owner (postgres). These roles are runtime-only and
-- deliberately have no DDL rights — see README notes.
--
-- Re-runnable: safe to apply repeatedly.

\set ON_ERROR_STOP on

BEGIN;

-- ── Roles ────────────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'moeds_app') THEN
        CREATE ROLE moeds_app LOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'report_app') THEN
        CREATE ROLE report_app LOGIN;
    END IF;
END
$$;

ALTER ROLE moeds_app  WITH PASSWORD :'moeds_pw';
ALTER ROLE report_app WITH PASSWORD :'report_pw';

-- ── The ownership table ──────────────────────────────────────────────────────
-- Generated from master_data.MASTER_ORM_MODELS + master_data.gis.LAYER_TABLE, plus the
-- two GIS layer-catalog tables.
--
-- The catalogs are here even though `master_data/gis.py` only writes features at runtime:
-- a layer's catalog row and its features are one unit, written together by the importers
-- that populate them (`upsert_water_layer_catalog` then `insert_water_feature`). Splitting
-- them across roles would leave that sequence impossible for either side to complete.
-- `gis_admin_layer` / `gis_admin_feature` stay with moeds — administrative boundaries are
-- not part of the master-data registry.
--
-- Keep in step with the Python side; `check_master_data_schema` covers the same tables.

CREATE TEMP TABLE _report_owned (table_name text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO _report_owned VALUES
    ('datasets_dataset'),
    ('datasets_datasetresource'),
    ('electricity_fueltankstation'),
    ('electricity_hydrodam'),
    ('electricity_loadgovernorate'),
    ('electricity_powerplant'),
    ('electricity_substation'),
    ('electricity_transmissionline'),
    ('gis_electricity_feature'),
    ('gis_electricity_layer'),
    ('geology_oreproduct'),
    ('gis_water_feature'),
    ('gis_water_layer'),
    ('oil_gas_facility'),
    ('oil_gas_field'),
    ('oil_gas_pipeline'),
    ('oil_gas_refinery'),
    ('oil_gas_well'),
    ('projects_projectgovernorate'),
    ('projects_projectorganization'),
    ('water_dam'),
    ('water_drinkingwaterstation'),
    ('water_rainfallbasin'),
    ('water_rainfallstation');

-- Fail early if the list drifted from reality rather than granting a wrong set.
DO $$
DECLARE
    missing text;
BEGIN
    SELECT string_agg(r.table_name, ', ') INTO missing
    FROM _report_owned r
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_tables t
        WHERE t.schemaname = 'moeds' AND t.tablename = r.table_name
    );
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'Tables listed but not present in schema moeds: %', missing;
    END IF;
END
$$;

-- ── Schema access ────────────────────────────────────────────────────────────

GRANT USAGE ON SCHEMA moeds, report_moe, public TO moeds_app, report_app;

-- ── Baseline: both roles may read everything ─────────────────────────────────
-- Cross-schema reads are the whole point of the shared database; only writes are split.

GRANT SELECT ON ALL TABLES IN SCHEMA moeds      TO moeds_app, report_app;
GRANT SELECT ON ALL TABLES IN SCHEMA report_moe TO moeds_app, report_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public     TO moeds_app, report_app;

-- ── Writes ───────────────────────────────────────────────────────────────────

DO $$
DECLARE
    t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'moeds'
    LOOP
        IF EXISTS (SELECT 1 FROM _report_owned r WHERE r.table_name = t.tablename) THEN
            -- report_moe writes; moeds reads only.
            EXECUTE format(
                'GRANT INSERT, UPDATE, DELETE ON moeds.%I TO report_app', t.tablename);
            EXECUTE format(
                'REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON moeds.%I FROM moeds_app',
                t.tablename);
        ELSE
            -- moeds writes; report_moe reads only.
            EXECUTE format(
                'GRANT INSERT, UPDATE, DELETE ON moeds.%I TO moeds_app', t.tablename);
            EXECUTE format(
                'REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON moeds.%I FROM report_app',
                t.tablename);
        END IF;
    END LOOP;
END
$$;

-- Narrow exception: datasets_dataset is report_moe-owned (title, files, status, ...),
-- but view_count/download_count are non-critical portal-usage counters that moeds
-- bumps on every view/download. Column-level GRANT lets moeds_app touch only these
-- two columns; every other column on this table stays report_app-only per the loop
-- above, which already REVOKEd table-level UPDATE for moeds_app on this table.
GRANT UPDATE (view_count, download_count) ON moeds.datasets_dataset TO moeds_app;

-- report_moe's own schema: its data, its writes.
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA report_moe TO report_app;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA report_moe FROM moeds_app;

-- Each project now owns its auth tables (accounts_user, django_session,
-- django_content_type, auth_permission, django_admin_log) inside its own schema, so
-- they are covered by the per-schema write grants above -- no shared `common` grants.
--
-- django_migrations is per-deployment history; neither runtime role may touch it.
-- Migrations run as the schema owner (postgres), never as moeds_app/report_app.
--
-- Each project keeps its own (moeds.django_migrations / report_moe.django_migrations),
-- picked up for free by the ALL TABLES IN SCHEMA grants above - hence the explicit
-- revoke below. Revoke wherever it is actually found so this script does not fail when
-- one of the two does not exist.
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT schemaname FROM pg_tables
        WHERE tablename = 'django_migrations'
          AND schemaname IN ('moeds', 'report_moe')
    LOOP
        EXECUTE format(
            'REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON %I.django_migrations FROM moeds_app, report_app',
            r.schemaname
        );
    END LOOP;
END
$$;

-- ── Sequences ────────────────────────────────────────────────────────────────
-- Only three explicit sequences exist; the rest are IDENTITY columns, covered by the
-- table INSERT grant. Two of these three back tables report_moe writes via raw SQL —
-- without USAGE, every INSERT into gis_*_feature fails.

GRANT USAGE, SELECT ON moeds.gis_water_feature_id_seq       TO report_app;
GRANT USAGE, SELECT ON moeds.gis_electricity_feature_id_seq TO report_app;
GRANT USAGE, SELECT ON moeds.gis_admin_feature_id_seq       TO moeds_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA report_moe   TO report_app;

-- ── Future tables ────────────────────────────────────────────────────────────
-- A table added later by a migration would otherwise be unreachable until someone
-- remembers to re-run this script. Defaults keep reads working; writes on new `moeds`
-- tables still need an explicit decision here, which is the point.

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA moeds
    GRANT SELECT ON TABLES TO moeds_app, report_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA report_moe
    GRANT SELECT ON TABLES TO moeds_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA report_moe
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO report_app;

COMMIT;

\echo 'Single-writer grants applied. Verify with verify_single_writer.sql'
