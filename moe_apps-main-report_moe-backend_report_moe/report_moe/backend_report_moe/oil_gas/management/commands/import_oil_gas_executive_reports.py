from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from oil_gas.models import DailyReport
from oil_gas.pdf_extract import extract_pdf
from oil_gas.services import upsert_metric


class Command(BaseCommand):
    help = 'Import executive oil & gas daily reports from PDF files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            help='Folder containing executive report PDFs.',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Single PDF file to import.',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Delete all existing oil & gas daily reports before import.',
        )
        parser.add_argument(
            '--keep-date',
            type=str,
            help='When purging, keep this report date (YYYY-MM-DD). Ignored without --purge.',
        )

    def handle(self, *args, **options):
        if options['purge']:
            qs = DailyReport.objects.all()
            keep_date = options.get('keep_date')
            if keep_date:
                qs = qs.exclude(report_date=keep_date)
            deleted, _ = qs.delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} related row(s).'))

        paths: list[Path] = []
        if options['file']:
            paths.append(Path(options['file']))
        elif options['folder']:
            folder = Path(options['folder'])
            if not folder.is_dir():
                raise CommandError(f'Folder not found: {folder}')
            paths.extend(sorted(folder.glob('*.pdf')))
        else:
            raise CommandError('Provide --folder or --file.')

        if not paths:
            raise CommandError('No PDF files found.')

        imported = 0
        for path in paths:
            try:
                payload = extract_pdf(path)
            except (ValueError, OSError) as exc:
                self.stdout.write(self.style.ERROR(f'Skip {path.name}: {exc}'))
                continue

            report_date = payload['report_date']
            report, _ = DailyReport.objects.update_or_create(
                report_date=report_date,
                defaults={
                    'status': DailyReport.Status.PUBLISHED,
                    'notes_ar': payload['notes_ar'],
                    'notes_en': payload['notes_en'],
                },
            )
            report.metrics.all().delete()
            for key, value in payload['metrics'].items():
                upsert_metric(report, key, value)

            imported += 1
            peak = payload['metrics'].get('total_oil_production_bbl')
            gas = payload['metrics'].get('total_clean_gas_mm3')
            self.stdout.write(
                self.style.SUCCESS(
                    f'{report_date}: oil={peak} gas={gas} ({len(payload["metrics"])} metrics) ← {path.name}',
                ),
            )

        self.stdout.write(self.style.SUCCESS(f'Imported {imported} executive report(s).'))
