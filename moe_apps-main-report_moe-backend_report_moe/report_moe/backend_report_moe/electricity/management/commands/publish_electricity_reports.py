from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from electricity.pipeline import (
    DEFAULT_PDF_DIR,
    DEFAULT_XLSX_DIR,
    clean_daily_report_tables,
    collect_table_counts,
    export_reports_to_xlsx,
    import_pdf_folder,
    purge_xlsx_output,
)


class Command(BaseCommand):
    help = (
        'Clean electricity daily-report tables, re-import PDFs, and export final XLSX files.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--pdf-dir',
            type=Path,
            default=DEFAULT_PDF_DIR,
            help=f'Folder with source PDF reports (default: {DEFAULT_PDF_DIR})',
        )
        parser.add_argument(
            '--xlsx-dir',
            type=Path,
            default=DEFAULT_XLSX_DIR,
            help=f'Output folder for final XLSX files (default: {DEFAULT_XLSX_DIR})',
        )
        parser.add_argument(
            '--skip-clean',
            action='store_true',
            help='Do not delete existing daily report rows before import.',
        )
        parser.add_argument(
            '--skip-import',
            action='store_true',
            help='Skip PDF import (export only from current database).',
        )
        parser.add_argument(
            '--skip-export',
            action='store_true',
            help='Skip XLSX export after import.',
        )
        parser.add_argument(
            '--keep-xlsx',
            action='store_true',
            help='Do not delete existing *.xlsx files before export.',
        )
        parser.add_argument(
            '--draft',
            action='store_true',
            help='Import reports as draft instead of published.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show table counts only; do not clean, import, or export.',
        )

    def handle(self, *args, **options):
        pdf_dir: Path = options['pdf_dir']
        xlsx_dir: Path = options['xlsx_dir']
        publish = not options['draft']

        if options['dry_run']:
            self._print_counts('Current rows')
            self.stdout.write(f'PDF source : {pdf_dir}')
            self.stdout.write(f'XLSX output: {xlsx_dir}')
            return

        if not options['skip_import'] and not pdf_dir.is_dir():
            raise CommandError(f'PDF folder not found: {pdf_dir}')

        if options['skip_clean'] and options['skip_import'] and options['skip_export']:
            raise CommandError('Nothing to do: all steps were skipped.')

        if not options['skip_clean']:
            self.stdout.write('Step 1/3 — cleaning daily report tables…')
            counts = collect_table_counts()
            self._print_counts('Before cleanup', counts)
            cleaned = clean_daily_report_tables()
            if cleaned.deleted:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Deleted {cleaned.deleted} row(s) across related tables.',
                    ),
                )
            else:
                self.stdout.write('Tables were already empty.')

        if not options['skip_import']:
            self.stdout.write('Step 2/3 — importing PDF reports…')
            imported = import_pdf_folder(pdf_dir, publish=publish)
            if not imported:
                raise CommandError(f'No PDF reports imported from {pdf_dir}')
            for row in imported:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{row.report_date}: peak={row.peak_mw} net={row.net_mwh_24h} '
                        f'fuel={row.fuel_reserve_t} [{row.source_file}]',
                    ),
                )
            self.stdout.write(self.style.SUCCESS(
                f'Imported {len(imported)} report(s).'))

        if not options['skip_export']:
            step = '2/2' if options['skip_import'] and options['skip_clean'] else '3/3'
            self.stdout.write(f'Step {step} — exporting final XLSX files…')
            if not options['keep_xlsx']:
                removed = purge_xlsx_output(xlsx_dir)
                if removed:
                    self.stdout.write(f'Removed {removed} old XLSX file(s).')
            exported = export_reports_to_xlsx(xlsx_dir)
            if not exported:
                raise CommandError(
                    'No reports exported — database has no daily reports.')
            for row in exported:
                self.stdout.write(f'  {row.output_file}')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Exported {len(exported)} file(s) -> {xlsx_dir.as_posix()}',
                ),
            )

        self.stdout.write(self.style.SUCCESS('Pipeline complete.'))

    def _print_counts(self, title: str, counts: dict[str, int] | None = None) -> None:
        if counts is None:
            counts = collect_table_counts()
        self.stdout.write(title + ':')
        for label, count in counts.items():
            self.stdout.write(f'  {label}: {count}')
