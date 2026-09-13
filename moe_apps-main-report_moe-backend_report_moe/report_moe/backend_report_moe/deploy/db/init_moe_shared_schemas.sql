-- Runs inside the already-created POSTGRES_DB (moe_shared) on first container init.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS report_moe;
CREATE SCHEMA IF NOT EXISTS moeds;
