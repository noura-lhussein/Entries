from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Download and install OSGeo4W (GDAL + GEOS) via osgeo4w-installer. '
        'Requires admin rights and network access. Restart the terminal after install.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--root',
            default='C:\\OSGeo4W64',
            help='OSGeo4W installation directory (default: C:\\OSGeo4W64)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print the install plan without downloading or installing',
        )

    def handle(self, *args, **options):
        try:
            from osgeo4w_installer import osgeo4w_install
        except ImportError as exc:
            raise CommandError(
                'osgeo4w-installer is not installed. Run: pip install osgeo4w-installer'
            ) from exc

        root = options['root']
        setup_dir = Path(settings.BASE_DIR) / 'tools' / 'osgeo4w-setup'
        packages = [
            'gdal',
            'libgeos-devel',
            'proj',
        ]

        self.stdout.write(f'OSGeo4W root: {root}')
        self.stdout.write(f'Setup cache: {setup_dir}')
        self.stdout.write(f'Packages: {", ".join(packages)}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry run — no install performed.'))
            return

        self.stdout.write('Downloading OSGeo4W setup and installing (may take several minutes)…')
        code = osgeo4w_install(
            osgeo4w_setup_exe_dir=str(setup_dir),
            osgeo4w_root=root,
            local_package_dir=str(setup_dir),
            is64=True,
            osgeo4w_packages=packages,
            python_packages=[],
            batch_evn={'py3': False, 'qt5': False, 'pycharm': False},
            quiet_mode=True,
        )
        if code != 0:
            raise CommandError(f'OSGeo4W installer exited with code {code}')

        self.stdout.write(self.style.SUCCESS('OSGeo4W install finished.'))
        self.stdout.write('Add to your .env (adjust gdal DLL name if needed):')
        self.stdout.write(f'  OSGEO4W_ROOT={root}')
        self.stdout.write(f'  GDAL_LIBRARY_PATH={root}\\bin\\gdal310.dll')
        self.stdout.write(f'  GEOS_LIBRARY_PATH={root}\\bin\\geos_c.dll')
        self.stdout.write('  USE_GEODJANGO=true')
        self.stdout.write('Then run: python manage.py check_gdal')
