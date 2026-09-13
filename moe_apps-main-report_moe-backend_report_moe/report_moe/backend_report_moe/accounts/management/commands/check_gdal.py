import os
import sys

from config.gis import configure_geodjango, discover_osgeo4w_bin, use_geodjango
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Report GeoDjango / GDAL configuration (and how to fix missing libraries on Windows).'

    def handle(self, *args, **options):
        self.stdout.write(f'USE_GEODJANGO={use_geodjango()}')
        self.stdout.write(f'Database engine: {settings.DATABASES["default"]["ENGINE"]}')

        if not use_geodjango():
            self.stdout.write(
                self.style.WARNING(
                    'GeoDjango is disabled (USE_GEODJANGO=false). '
                    'PostGIS in PostgreSQL still works; ORM geometry fields need GDAL.'
                )
            )
            return

        paths = configure_geodjango({})
        gdal = getattr(settings, 'GDAL_LIBRARY_PATH', None) or paths.get('GDAL_LIBRARY_PATH')
        geos = getattr(settings, 'GEOS_LIBRARY_PATH', None) or paths.get('GEOS_LIBRARY_PATH')

        if gdal and geos:
            self.stdout.write(self.style.SUCCESS(f'GDAL_LIBRARY_PATH={gdal}'))
            self.stdout.write(self.style.SUCCESS(f'GEOS_LIBRARY_PATH={geos}'))
            return

        bin_dir = discover_osgeo4w_bin()
        self.stdout.write(self.style.ERROR('GDAL/GEOS libraries were not found.'))
        if sys.platform == 'win32':
            self.stdout.write('')
            self.stdout.write('Option A — install OSGeo4W (recommended for spatial ORM):')
            self.stdout.write('  1. Download: https://trac.osgeo.org/osgeo4w/')
            self.stdout.write('  2. Express install → include GDAL + GEOS')
            self.stdout.write('  3. Add to .env (adjust DLL version if needed):')
            self.stdout.write('     GDAL_LIBRARY_PATH=C:\\OSGeo4W64\\bin\\gdal310.dll')
            self.stdout.write('     GEOS_LIBRARY_PATH=C:\\OSGeo4W64\\bin\\geos_c.dll')
            self.stdout.write('  4. python manage.py check_gdal')
            self.stdout.write('')
            self.stdout.write('Option B — run API in Docker (includes GDAL):')
            self.stdout.write('  docker compose up -d --build')
            self.stdout.write('')
            self.stdout.write('Option C — skip GDAL for now (auth/API only):')
            self.stdout.write('  Add to .env: USE_GEODJANGO=false')
            if bin_dir:
                self.stdout.write(f'  (Found bin dir but no gdal3*.dll: {bin_dir})')
        else:
            self.stdout.write('Install GDAL/GEOS via your OS package manager, or set GDAL_LIBRARY_PATH in .env.')
        if os.getenv('GDAL_LIBRARY_PATH'):
            self.stdout.write(f"GDAL_LIBRARY_PATH env={os.getenv('GDAL_LIBRARY_PATH')} (file missing?)")
