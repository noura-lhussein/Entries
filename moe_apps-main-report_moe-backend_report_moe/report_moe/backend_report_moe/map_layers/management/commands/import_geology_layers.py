from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from map_layers.geology_layer_catalog import (
    DEFAULT_GEOLOGY_DIR,
    GEOLOGY_LAYER_SPECS,
    GEOLOGY_SOURCE_FILE,
    geology_feature_name,
    normalize_geology_properties,
)
from map_layers.shapefile_utils import iter_shapefile_features
from map_layers.water_services import (
    clear_water_layer_features,
    insert_water_feature,
    upsert_water_layer_catalog,
)


class Command(BaseCommand):
    help = 'Import Syria geology shapefile into PostGIS map layers (water sector sidebar).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_GEOLOGY_DIR),
            help='Directory containing geology_1-500000.shp.',
        )
        parser.add_argument(
            '--layer',
            type=str,
            default='',
            help='Import a single layer id (e.g. geology-official).',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        file_path = source_dir / GEOLOGY_SOURCE_FILE
        if not file_path.is_file():
            raise CommandError(f'Geology shapefile not found: {file_path}')

        upsert_water_layer_catalog()

        layers = GEOLOGY_LAYER_SPECS
        if options['layer']:
            layers = [layer for layer in GEOLOGY_LAYER_SPECS if layer.id == options['layer']]
            if not layers:
                raise CommandError(f'Unknown layer id: {options["layer"]}')

        features: list[tuple[dict, dict]] = []
        for _field_names, raw_props, geometry in iter_shapefile_features(file_path):
            properties = normalize_geology_properties(raw_props)
            features.append((properties, geometry))

        total = 0
        for layer in layers:
            clear_water_layer_features(layer.id)
            imported = 0

            for properties, geometry in features:
                if not layer.include_feature(properties):
                    continue
                name = geology_feature_name(properties)
                insert_water_feature(layer.id, name, properties, geometry)
                imported += 1

            total += imported
            self.stdout.write(
                self.style.SUCCESS(
                    f'{layer.id}: imported {imported} features from {GEOLOGY_SOURCE_FILE}'
                )
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {total} geology features total.'))
