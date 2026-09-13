from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from map_layers.layer_catalog import (
    ADMIN_LAYER_SPECS,
    DEFAULT_BOUNDARIES_DIR,
    extract_feature_fields,
)
from map_layers.services import clear_layer_features, insert_feature, upsert_layer_catalog


class Command(BaseCommand):
    help = 'Import Syria administrative boundary GeoJSON files into PostGIS.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_BOUNDARIES_DIR),
            help='Directory containing syr_admin*.geojson files.',
        )
        parser.add_argument(
            '--layer',
            type=str,
            default='',
            help='Import a single layer id (e.g. governorate).',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        if not source_dir.is_dir():
            raise CommandError(f'Boundaries directory not found: {source_dir}')

        upsert_layer_catalog()

        layers = ADMIN_LAYER_SPECS
        if options['layer']:
            layers = [layer for layer in ADMIN_LAYER_SPECS if layer.id == options['layer']]
            if not layers:
                raise CommandError(f'Unknown layer id: {options["layer"]}')

        total = 0
        for layer in layers:
            file_path = source_dir / layer.file
            if not file_path.is_file():
                raise CommandError(f'Missing GeoJSON file: {file_path}')

            with file_path.open(encoding='utf-8') as handle:
                payload = json.load(handle)

            features = payload.get('features') or []
            clear_layer_features(layer.id)
            imported = 0

            for feature in features:
                geometry = feature.get('geometry')
                if not geometry:
                    continue
                props = feature.get('properties') or {}
                fields = extract_feature_fields(layer.id, props)
                insert_feature(layer.id, fields, geometry, props)
                imported += 1

            total += imported
            self.stdout.write(
                self.style.SUCCESS(f'{layer.id}: imported {imported} features from {layer.file}')
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {total} features total.'))
