"""Orchestrate electricity daily-report cleanup, PDF import, and XLSX export."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from django.db import transaction

from .models import (
    DailyMetric,
    DailyReport,
    FuelTankReading,
    GenerationIncident,
    GenerationUnitReading,
    GovernorateLoad,
    GridLineIncident,
    HydroDamReading,
)
from .pdf_extract import extract_pdf, parse_report_date_from_path
from .report_export import write_electricity_report_xlsx
from .services import build_report_detail_payload, import_extracted_row

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF_DIR = REPO_ROOT / 'DOSC' / 'electricity' / 'electricity'
DEFAULT_XLSX_DIR = REPO_ROOT / 'DOSC' / 'electricity' / 'xlsx'

RELATED_TABLE_LABELS: tuple[tuple[str, type], ...] = (
    ('DailyReport', DailyReport),
    ('DailyMetric', DailyMetric),
    ('GovernorateLoad', GovernorateLoad),
    ('HydroDamReading', HydroDamReading),
    ('GenerationIncident', GenerationIncident),
    ('GridLineIncident', GridLineIncident),
    ('FuelTankReading', FuelTankReading),
    ('GenerationUnitReading', GenerationUnitReading),
)


@dataclass(slots=True)
class TableCounts:
    before: dict[str, int] = field(default_factory=dict)
    deleted: int = 0


@dataclass(slots=True)
class ImportResult:
    report_date: str
    source_file: str
    peak_mw: int | None
    net_mwh_24h: int | None
    fuel_reserve_t: int | None


@dataclass(slots=True)
class ExportResult:
    report_date: str
    output_file: str


@dataclass(slots=True)
class PipelineSummary:
    cleaned: TableCounts | None = None
    imported: list[ImportResult] = field(default_factory=list)
    exported: list[ExportResult] = field(default_factory=list)
    purged_xlsx: int = 0
    errors: list[str] = field(default_factory=list)


def collect_table_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for label, model in RELATED_TABLE_LABELS:
        counts[label] = model.objects.count()
    return counts


def clean_daily_report_tables() -> TableCounts:
    """Delete all DailyReport rows (CASCADE to related tables)."""
    before = collect_table_counts()
    if before['DailyReport'] == 0:
        return TableCounts(before=before, deleted=0)

    with transaction.atomic():
        deleted_total, _deleted_by_model = DailyReport.objects.all().delete()

    after = collect_table_counts()
    for label, count in after.items():
        if count:
            raise RuntimeError(
                f'Expected 0 {label} rows after cleanup, found {count}.')

    return TableCounts(before=before, deleted=deleted_total)


def collect_pdf_files(pdf_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in pdf_dir.glob('*.pdf')
        if not path.name.startswith('.') and '__MACOSX' not in path.parts
    )


def import_pdf_folder(pdf_dir: Path, *, publish: bool = True) -> list[ImportResult]:
    if not pdf_dir.is_dir():
        raise FileNotFoundError(f'PDF folder not found: {pdf_dir}')

    results: list[ImportResult] = []
    for pdf_path in collect_pdf_files(pdf_dir):
        report_date = parse_report_date_from_path(pdf_path)
        if report_date is None:
            continue
        row = extract_pdf(pdf_path)
        import_extracted_row(row, publish=publish)
        results.append(
            ImportResult(
                report_date=report_date.isoformat(),
                source_file=pdf_path.name,
                peak_mw=row.get('peak_mw'),
                net_mwh_24h=row.get('net_mwh_24h'),
                fuel_reserve_t=row.get('fuel_reserve_t'),
            ),
        )
    return results


def purge_xlsx_output(xlsx_dir: Path) -> int:
    if not xlsx_dir.is_dir():
        return 0
    removed = 0
    for path in xlsx_dir.glob('*.xlsx'):
        path.unlink(missing_ok=True)
        removed += 1
    return removed


def export_reports_to_xlsx(
    xlsx_dir: Path,
    *,
    report_dates: list[date] | None = None,
) -> list[ExportResult]:
    xlsx_dir.mkdir(parents=True, exist_ok=True)

    queryset = DailyReport.objects.order_by('report_date')
    if report_dates:
        queryset = queryset.filter(report_date__in=report_dates)

    results: list[ExportResult] = []
    for report in queryset:
        payload = build_report_detail_payload(report.report_date)
        if not payload:
            continue
        output_name = f'report_{report.report_date.isoformat()}.xlsx'
        output_path = xlsx_dir / output_name
        write_electricity_report_xlsx(payload, output_path)
        results.append(
            ExportResult(
                report_date=report.report_date.isoformat(),
                output_file=output_name,
            ),
        )
    return results


def run_pipeline(
    *,
    pdf_dir: Path = DEFAULT_PDF_DIR,
    xlsx_dir: Path = DEFAULT_XLSX_DIR,
    clean: bool = True,
    import_pdfs: bool = True,
    export_xlsx: bool = True,
    purge_xlsx: bool = True,
    publish: bool = True,
) -> PipelineSummary:
    summary = PipelineSummary()

    if clean:
        summary.cleaned = clean_daily_report_tables()

    if import_pdfs:
        summary.imported = import_pdf_folder(pdf_dir, publish=publish)

    if export_xlsx:
        if purge_xlsx:
            summary.purged_xlsx = purge_xlsx_output(xlsx_dir)
        summary.exported = export_reports_to_xlsx(xlsx_dir)

    return summary
