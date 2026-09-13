from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from map_layers.shapefile_utils import iter_shapefile_features
from map_layers.water_layer_catalog import (
    DEFAULT_WATER_DIR,
    WATER_DB_SYNC_LAYER_IDS,
    WATER_LAYER_SPECS,
    normalize_water_properties,
    water_feature_name,
)
from map_layers.water_services import (
    clear_water_layer_features,
    insert_water_feature,
    upsert_water_layer_catalog,
)


class Command(BaseCommand):
    help = 'Import Syria water resource shapefiles from the Water/ directory into PostGIS.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_WATER_DIR),
            help='Directory containing lakes/, rivers/, streams/, dams/, springs/ shapefiles.',
        )
        parser.add_argument(
            '--layer',
            type=str,
            default='',
            help='Import a single layer id (e.g. water-lakes).',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        if not source_dir.is_dir():
            raise CommandError(f'Water directory not found: {source_dir}')

        upsert_water_layer_catalog()

        layers = WATER_LAYER_SPECS
        if options['layer']:
            layers = [layer for layer in WATER_LAYER_SPECS if layer.id == options['layer']]
            if not layers:
                raise CommandError(f'Unknown layer id: {options["layer"]}')

        total = 0
        for layer in layers:
            if layer.id in WATER_DB_SYNC_LAYER_IDS or not layer.file:
                self.stdout.write(
                    self.style.WARNING(
                        f'{layer.id}: skipped (synced from database — run sync_drinking_water_map_layer)',
                    ),
                )
                continue

            file_path = source_dir / layer.file
            if not file_path.is_file():
                raise CommandError(f'Missing shapefile: {file_path}')

            clear_water_layer_features(layer.id)
            imported = 0

            for _field_names, raw_props, geometry in iter_shapefile_features(file_path):
                properties = normalize_water_properties(layer.id, raw_props)
                name = water_feature_name(layer.id, properties)
                insert_water_feature(layer.id, name, properties, geometry)
                imported += 1

            total += imported
            self.stdout.write(
                self.style.SUCCESS(f'{layer.id}: imported {imported} features from {layer.file}')
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {total} water features total.'))
