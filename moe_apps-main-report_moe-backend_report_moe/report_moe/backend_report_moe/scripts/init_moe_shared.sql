-- Bootstrap shared PostgreSQL database for moeds + report_moe.
-- Run as a superuser against the cluster (not inside moe_shared yet):
--   psql -U postgres -f init_moe_shared.sql

SELECT 'CREATE DATABASE moe_shared'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'moe_shared')\gexec

\connect moe_shared

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS report_moe;
CREATE SCHEMA IF NOT EXISTS moeds;

GRANT ALL ON SCHEMA common TO CURRENT_USER;
GRANT ALL ON SCHEMA report_moe TO CURRENT_USER;
GRANT ALL ON SCHEMA moeds TO CURRENT_USER;
GRANT ALL ON SCHEMA public TO CURRENT_USER;
