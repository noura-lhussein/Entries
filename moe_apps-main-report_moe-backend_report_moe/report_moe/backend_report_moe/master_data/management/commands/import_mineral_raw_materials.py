"""
Import mineral deposits and Geomillion geology layers from the MOE
"ملفات الخامات" package into gis_water_feature (schema `moeds`).

report_moe owns these tables (see moeds/moe-backend/scripts/enforce_single_writer.sql),
so this importer — unlike moeds's old copy of the same command — is the correct
place for this write to live.

Usage:
  python manage.py import_mineral_raw_materials --path "C:\\path\\to\\ملفات الخامات"
  python manage.py import_mineral_raw_materials --path "..." --layer geology-minerals
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from master_data.geology_raw_materials import (
    RAW_MATERIAL_LAYER_BY_ID,
    RAW_MATERIAL_LAYER_SPECS,
    geology_feature_name,
    normalize_geomillion_properties,
    normalize_mineral_deposit_properties,
    normalize_structure_properties,
)
from master_data.gis import (
    bulk_insert_water_feature,
    clear_water_layer_features,
    upsert_water_layer_catalog,
)
from master_data.shapefile_utils import iter_shapefile_features

# Relative paths under the MOE "ملفات الخامات" package root.
LAYER_SOURCES: dict[str, tuple[str, Callable[[dict[str, Any]], dict[str, Any]]]] = {
    'geology-minerals': ('shapfile/miniral1.shp', normalize_mineral_deposit_properties),
    'geology-geomillion': (
        'shapfile/Geomillion/GeologicalBoundariesFixedatPlace.shp',
        normalize_geomillion_properties,
    ),
    'geology-faults': ('shapfile/Geomillion/Faults.shp', normalize_structure_properties),
    'geology-extinct-volcanoes': (
        'shapfile/Geomillion/ExtinctVolcano.shp',
        normalize_structure_properties,
    ),
}


class Command(BaseCommand):
    help = (
        'Import mineral deposits and Geomillion geology layers from the MOE '
        '"ملفات الخامات" package into PostGIS map layers (report_moe-owned tables).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Root folder of the raw-materials package (contains shapfile/).',
        )
        parser.add_argument(
            '--layer',
            type=str,
            default='',
            help='Import a single layer id (e.g. geology-minerals).',
        )
        parser.add_argument(
            '--flat-minerals',
            action='store_true',
            help=(
                'Treat --path as a flat folder of one .shp file per mineral product '
                '(each with a "نوع" field), instead of the shapfile/ package layout. '
                'Imports everything found into geology-minerals.'
            ),
        )

    def handle(self, *args, **options):
        source_root = Path(options['path'])
        if not source_root.is_dir():
            raise CommandError(f'Raw materials folder not found: {source_root}')

        if options['flat_minerals']:
            self._import_flat_minerals(source_root)
            return

        layer_ids = list(LAYER_SOURCES)
        if options['layer']:
            layer_id = options['layer']
            if layer_id not in LAYER_SOURCES:
                raise CommandError(
                    f'Unknown mineral raw-materials layer id: {layer_id}. '
                    f'Choose from: {", ".join(sorted(LAYER_SOURCES))}'
                )
            layer_ids = [layer_id]

        upsert_water_layer_catalog(RAW_MATERIAL_LAYER_SPECS)

        total = 0
        for layer_id in layer_ids:
            if layer_id not in RAW_MATERIAL_LAYER_BY_ID:
                raise CommandError(f'Layer {layer_id} is missing from RAW_MATERIAL_LAYER_SPECS.')

            relative_path, normalize = LAYER_SOURCES[layer_id]
            file_path = source_root / relative_path
            if not file_path.is_file():
                raise CommandError(f'Shapefile not found for {layer_id}: {file_path}')

            clear_water_layer_features(layer_id)
            imported = 0
            skipped = 0
            for _field_names, raw_props, geometry in iter_shapefile_features(file_path):
                if geometry is None:
                    skipped += 1
                    continue
                # Geomillion carries a handful of non-geological filler polygons
                # (neighboring countries, the sea) with no Legend classification —
                # exclude them so the layer matches the intended geology-only map.
                if layer_id == 'geology-geomillion' and not str(raw_props.get('Legend') or '').strip():
                    skipped += 1
                    continue
                properties = normalize(raw_props)
                name = geology_feature_name(properties)
                bulk_insert_water_feature(layer_id, name, properties, geometry)
                imported += 1

            total += imported
            message = f'{layer_id}: imported {imported} features from {relative_path}'
            if skipped:
                message += f' (skipped {skipped} empty geometries)'
            self.stdout.write(self.style.SUCCESS(message))

        self.stdout.write(
            self.style.SUCCESS(f'Done. Imported {total} mineral/geology features total.')
        )

    def _import_flat_minerals(self, source_root: Path) -> None:
        layer_id = 'geology-minerals'
        shp_files = sorted(source_root.glob('*.shp'))
        if not shp_files:
            raise CommandError(f'No .shp files found in {source_root}')

        upsert_water_layer_catalog([RAW_MATERIAL_LAYER_BY_ID[layer_id]])
        clear_water_layer_features(layer_id)

        total = 0
        for shp_path in shp_files:
            imported = 0
            skipped = 0
            for _field_names, raw_props, geometry in iter_shapefile_features(shp_path):
                if geometry is None:
                    skipped += 1
                    continue
                properties = normalize_mineral_deposit_properties(raw_props)
                name = geology_feature_name(properties)
                bulk_insert_water_feature(layer_id, name, properties, geometry)
                imported += 1
            total += imported
            message = f'{shp_path.name}: imported {imported} features'
            if skipped:
                message += f' (skipped {skipped} empty geometries)'
            self.stdout.write(self.style.SUCCESS(message))

        self.stdout.write(
            self.style.SUCCESS(f'Done. Imported {total} mineral deposit features total.')
        )
