from __future__ import annotations

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from water.euphrates_import import import_euphrates_folder


class Command(BaseCommand):
    help = 'Import Euphrates cascade daily readings from سدود الفرات or المعلومات المائية workbooks (.xlsx/.xls).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=os.getenv('DAM_DATA_DIR', str(Path(__file__).resolve().parents[4] / 'السدود')),
            help='Folder containing Euphrates cascade workbooks.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing Euphrates cascade readings before import.',
        )

    def handle(self, *args, **options):
        root = Path(options['path'])
        try:
            stats = import_euphrates_folder(root, clear=options['clear'])
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Done — {stats["rows"]:,} daily readings from {stats["files"]} workbook(s).',
            ),
        )
