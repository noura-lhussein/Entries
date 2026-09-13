from __future__ import annotations

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from electricity.pdf_extract import extract_pdf, parse_report_date_from_path
from electricity.services import import_extracted_row, list_available_dates
from electricity.xlsx_extract import extract_xlsx

ARABIC_COORDINATION_PREFIX = 'تقرير صالة التنسيق'


class Command(BaseCommand):
    help = 'Import electricity daily reports from PDF or executive XLSX files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default='',
            help='Folder containing *.pdf or *.xlsx reports',
        )
        parser.add_argument(
            '--file',
            type=str,
            default='',
            help='Single PDF or XLSX file to import',
        )
        parser.add_argument(
            '--recursive',
            action='store_true',
            help='Search subfolders for PDF/XLSX files',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Do not overwrite report dates already in the database',
        )
        parser.add_argument(
            '--draft',
            action='store_true',
            help='Import as draft instead of published',
        )

    def handle(self, *args, **options):
        publish = not options['draft']
        skip_existing = options['skip_existing']
        existing_dates = set(list_available_dates()) if skip_existing else set()

        file_opt = options['file'].strip()
        if file_opt:
            path = Path(file_opt)
            if not path.is_file():
                raise CommandError(f'File not found: {path}')
            self._import_file(path, publish=publish, skip_existing=skip_existing, existing_dates=existing_dates)
            return

        folder_opt = options['folder'].strip()
        if folder_opt:
            folder = Path(folder_opt)
        else:
            folder = Path(__file__).resolve().parents[4] / 'electricity'

        if not folder.is_dir():
            raise CommandError(f'Folder not found: {folder}')

        files = self._collect_files(folder, recursive=options['recursive'])
        if not files:
            raise CommandError(f'No PDF/XLSX files found in {folder}')

        selected = self._pick_best_per_date(files)
        if not selected:
            raise CommandError(f'No importable report files found in {folder}')

        imported = 0
        skipped = 0
        for path in sorted(selected, key=self._sort_key):
            report_date = self._report_date_for_path(path)
            if skip_existing and report_date and report_date.isoformat() in existing_dates:
                skipped += 1
                self.stdout.write(f'Skip existing {report_date}: {path.name}')
                continue
            self._import_file(path, publish=publish, skip_existing=False, existing_dates=existing_dates)
            imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Imported {imported} report(s) from {folder}'
                + (f' ({skipped} skipped)' if skipped else ''),
            ),
        )

    def _collect_files(self, folder: Path, *, recursive: bool) -> list[Path]:
        if recursive:
            pdfs = list(folder.rglob('*.pdf'))
            xlsx = list(folder.rglob('*.xlsx'))
        else:
            pdfs = list(folder.glob('*.pdf'))
            xlsx = list(folder.glob('*.xlsx'))
        return [*pdfs, *xlsx]

    def _report_date_for_path(self, path: Path) -> date | None:
        if path.suffix.lower() == '.pdf':
            return parse_report_date_from_path(path)
        try:
            row = extract_xlsx(path)
            return date.fromisoformat(row['report_date'])
        except Exception:
            return None

    def _file_preference_score(self, path: Path) -> int:
        if path.suffix.lower() == '.xlsx':
            return 100
        name = path.name
        if name.startswith(ARABIC_COORDINATION_PREFIX):
            return 30
        if ARABIC_COORDINATION_PREFIX in name:
            return 20
        return 10

    def _pick_best_per_date(self, files: list[Path]) -> list[Path]:
        best_by_date: dict[str, tuple[int, Path]] = {}
        for path in files:
            if path.suffix.lower() == '.pdf' and parse_report_date_from_path(path) is None:
                continue
            report_date = self._report_date_for_path(path)
            if report_date is None:
                continue
            key = report_date.isoformat()
            score = self._file_preference_score(path)
            current = best_by_date.get(key)
            if current is None or score > current[0]:
                best_by_date[key] = (score, path)
        return [entry[1] for entry in best_by_date.values()]

    def _sort_key(self, path: Path) -> date:
        return self._report_date_for_path(path) or date.min

    def _import_file(
        self,
        path: Path,
        *,
        publish: bool,
        skip_existing: bool,
        existing_dates: set[str],
    ) -> None:
        report_date = self._report_date_for_path(path)
        if skip_existing and report_date and report_date.isoformat() in existing_dates:
            self.stdout.write(f'Skip existing {report_date}: {path.name}')
            return

        if path.suffix.lower() == '.xlsx':
            row = extract_xlsx(path)
        else:
            row = extract_pdf(path)
        report = import_extracted_row(row, publish=publish)
        if report_date:
            existing_dates.add(report_date.isoformat())
        self.stdout.write(
            self.style.SUCCESS(
                f'{report.report_date}: peak={row.get("peak_mw")} '
                f'net={row.get("net_mwh_24h")} fuel={row.get("fuel_reserve_t")} '
                f'[{path.name}]',
            ),
        )
