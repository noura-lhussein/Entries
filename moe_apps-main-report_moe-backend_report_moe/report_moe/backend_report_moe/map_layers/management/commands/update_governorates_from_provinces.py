from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

DEFAULT_PROVINCES_FILE = (
    Path(__file__).resolve().parents[2] / 'data' / 'syria_provinces.geojson'
)

# province_name in syria_provinces.geojson → existing gis_admin_feature pcode
PROVINCE_NAME_TO_PCODE: dict[str, str] = {
    'Aleppo': 'SY02',
    'Al Ḥasakah': 'SY08',
    'Al Hasakah': 'SY08',
    'Ar Raqqah': 'SY11',
    'As Suwayda': 'SY13',
    'Damascus': 'SY01',
    'Dar`a': 'SY12',
    "Dar'a": 'SY12',
    'Daraa': 'SY12',
    'Dayr Az Zawr': 'SY09',
    'Hamah': 'SY05',
    'Hama': 'SY05',
    'Homs': 'SY04',
    'Idlib': 'SY07',
    'Idleb': 'SY07',
    'Lattakia': 'SY06',
    'Latakia': 'SY06',
    'Quneitra': 'SY14',
    'Rif Dimashq': 'SY03',
    'Tartus': 'SY10',
    'Tartous': 'SY10',
}


class Command(BaseCommand):
    help = (
        'Replace governorate polygons from syria_provinces.geojson, then clip '
        'district/subdistrict geometries to the updated parent governorates.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_PROVINCES_FILE),
            help='Path to syria_provinces.geojson',
        )
        parser.add_argument(
            '--skip-clip',
            action='store_true',
            help='Only update governorates; do not clip district/subdistrict.',
        )

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.is_file():
            raise CommandError(f'File not found: {path}')

        payload = json.loads(path.read_text(encoding='utf-8'))
        features = payload.get('features') or []
        if not features:
            raise CommandError('No features in GeoJSON.')

        updated = 0
        missing: list[str] = []
        with connection.cursor() as cursor:
            for feature in features:
                props = feature.get('properties') or {}
                geometry = feature.get('geometry')
                name = str(props.get('province_name') or '').strip()
                if not name or not geometry:
                    continue
                pcode = PROVINCE_NAME_TO_PCODE.get(name)
                if not pcode:
                    missing.append(name)
                    continue

                cursor.execute(
                    """
                    UPDATE gis_admin_feature
                    SET geom = ST_Multi(ST_CollectionExtract(ST_MakeValid(
                            ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                        ), 3)),
                        properties = properties || %s::jsonb
                    WHERE layer_id = 'governorate' AND pcode = %s
                    """,
                    [
                        json.dumps(geometry, ensure_ascii=False),
                        json.dumps({'source': 'syria_provinces.geojson', 'province_name': name}),
                        pcode,
                    ],
                )
                if cursor.rowcount:
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f'Updated {pcode} ({name})'))
                else:
                    self.stdout.write(self.style.WARNING(f'No DB row for {pcode} ({name})'))

            if not options['skip_clip']:
                clipped_districts = self._clip_children(cursor, 'district', 'adm1_pcode')
                clipped_subdistricts = self._clip_children(cursor, 'subdistrict', 'adm1_pcode')
                coastal = self._inherit_coastline(cursor)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Clipped districts={clipped_districts}, '
                        f'subdistricts={clipped_subdistricts}, '
                        f'coastal districts refreshed={coastal}'
                    )
                )

        if missing:
            raise CommandError(f'Unmapped province names: {", ".join(missing)}')

        self.stdout.write(self.style.SUCCESS(f'Done. Updated {updated} governorates.'))

    def _clip_children(self, cursor, layer_id: str, parent_field: str) -> int:
        cursor.execute(
            f"""
            UPDATE gis_admin_feature child
            SET geom = ST_Multi(ST_CollectionExtract(ST_MakeValid(
                    ST_Intersection(child.geom, parent.geom)
                ), 3))
            FROM gis_admin_feature parent
            WHERE child.layer_id = %s
              AND parent.layer_id = 'governorate'
              AND child.{parent_field} = parent.pcode
              AND child.geom IS NOT NULL
              AND parent.geom IS NOT NULL
              AND ST_Intersects(child.geom, parent.geom)
              AND NOT ST_IsEmpty(ST_Intersection(child.geom, parent.geom))
            """,
            [layer_id],
        )
        return cursor.rowcount

    def _inherit_coastline(self, cursor) -> int:
        """Pull coastal districts to the detailed province shoreline (Lattakia/Tartous)."""
        cursor.execute(
            """
            UPDATE gis_admin_feature d
            SET geom = ST_Multi(ST_CollectionExtract(ST_MakeValid(
                    ST_Intersection(ST_Buffer(d.geom::geography, 1800)::geometry, g.geom)
                ), 3))
            FROM gis_admin_feature g
            WHERE d.layer_id = 'district'
              AND g.layer_id = 'governorate'
              AND d.adm1_pcode = g.pcode
              AND d.adm1_pcode IN ('SY06', 'SY10')
            """
        )
        return cursor.rowcount
