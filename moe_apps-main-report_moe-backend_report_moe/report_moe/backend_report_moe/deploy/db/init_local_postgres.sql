-- Run as PostgreSQL superuser (e.g. psql -U postgres -f scripts/init_local_postgres.sql)
-- Creates shared DB used by moeds and report_moe.

SELECT 'CREATE DATABASE moe_shared'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'moe_shared')\gexec

\connect moe_shared

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS report_moe;
CREATE SCHEMA IF NOT EXISTS moeds;
