from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('map_layers', '0001_admin_boundaries'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS gis_water_layer (
                id VARCHAR(32) PRIMARY KEY,
                name_en VARCHAR(120) NOT NULL,
                name_ar VARCHAR(120) NOT NULL,
                geometry_type VARCHAR(16) NOT NULL,
                default_visible BOOLEAN NOT NULL DEFAULT FALSE,
                sort_order SMALLINT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS gis_water_feature (
                id BIGSERIAL PRIMARY KEY,
                layer_id VARCHAR(32) NOT NULL REFERENCES gis_water_layer(id) ON DELETE CASCADE,
                name VARCHAR(255),
                properties JSONB NOT NULL DEFAULT '{}',
                geom geometry(Geometry, 4326) NOT NULL
            );

            CREATE INDEX IF NOT EXISTS gis_water_feature_layer_idx
                ON gis_water_feature(layer_id);
            CREATE INDEX IF NOT EXISTS gis_water_feature_geom_idx
                ON gis_water_feature USING GIST(geom);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS gis_water_feature;
            DROP TABLE IF EXISTS gis_water_layer;
            """,
        ),
    ]
