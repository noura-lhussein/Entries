from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS gis_admin_layer (
                id VARCHAR(32) PRIMARY KEY,
                name_en VARCHAR(120) NOT NULL,
                name_ar VARCHAR(120) NOT NULL,
                geometry_type VARCHAR(16) NOT NULL,
                admin_level SMALLINT NULL,
                default_visible BOOLEAN NOT NULL DEFAULT FALSE,
                sort_order SMALLINT NOT NULL DEFAULT 0,
                filter_key VARCHAR(32) NULL
            );

            CREATE TABLE IF NOT EXISTS gis_admin_feature (
                id BIGSERIAL PRIMARY KEY,
                layer_id VARCHAR(32) NOT NULL REFERENCES gis_admin_layer(id) ON DELETE CASCADE,
                pcode VARCHAR(32),
                name_en VARCHAR(255),
                name_ar VARCHAR(255),
                adm0_pcode VARCHAR(32),
                adm1_pcode VARCHAR(32),
                adm2_pcode VARCHAR(32),
                adm3_pcode VARCHAR(32),
                properties JSONB NOT NULL DEFAULT '{}',
                geom geometry(Geometry, 4326) NOT NULL
            );

            CREATE INDEX IF NOT EXISTS gis_admin_feature_layer_idx
                ON gis_admin_feature(layer_id);
            CREATE INDEX IF NOT EXISTS gis_admin_feature_pcode_idx
                ON gis_admin_feature(pcode);
            CREATE INDEX IF NOT EXISTS gis_admin_feature_adm1_idx
                ON gis_admin_feature(adm1_pcode);
            CREATE INDEX IF NOT EXISTS gis_admin_feature_adm2_idx
                ON gis_admin_feature(adm2_pcode);
            CREATE INDEX IF NOT EXISTS gis_admin_feature_adm3_idx
                ON gis_admin_feature(adm3_pcode);
            CREATE INDEX IF NOT EXISTS gis_admin_feature_geom_idx
                ON gis_admin_feature USING GIST(geom);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS gis_admin_feature;
            DROP TABLE IF EXISTS gis_admin_layer;
            """,
        ),
    ]
