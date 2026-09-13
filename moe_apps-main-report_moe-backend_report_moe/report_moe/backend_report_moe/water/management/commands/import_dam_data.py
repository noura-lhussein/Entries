from __future__ import annotations

import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from water.coordinates import utm_to_wgs84
from water.models import Dam, DamStorageReading

try:
    import xlrd
except ImportError as exc:
    xlrd = None
    _XLRD_IMPORT_ERROR = exc
else:
    _XLRD_IMPORT_ERROR = None


YEAR_PATTERN = re.compile(r'(20\d{2}|19\d{2})')
DATE_IN_TEXT = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')
GOV_PREFIX = re.compile(r'^محافظة\s*')

# File spelling → DB spelling (after _dam_match_key).
NAME_ALIASES = {
    'ابوالكهف': 'ابوكهف',
    'المعيزليه': 'معيزليه',
    'غديران': 'كديران',
    'السريحين': 'سريحين',
    'خلفالايوبي': 'خلفايوبي',
    'واديالبقر': 'البقر',
    'امجلود': 'امالجلود',
    'ابوالفياض': 'ابوفياضالجديد',
    'واديالعزيب': 'العزيب',
    'واديابيض': 'واديالابيض',
    'الدلابوز': 'الدلبوز',
    'الحفر': 'حفيرالحفر',
    'بيتالقصير': 'بيتقصير',
    'صلاحالدينالسفرقيه': 'صلاحالدين',
    'الغاريه': 'الغاريهالشرقيه',
    'خربهالجوزيه': 'خربهجوزيهبرمانه',
    'الجوزيه': 'جوزيهساقيهصادق',
    'الحسكهالجنزبي': 'الحسكهالجنزي',
    'سهوهالبلاطه': 'سهوهبلاطه',
    'ديرعطيهغربي': 'غربديرعطيه',
    'ديرعطيهشرقيالقلمون': 'القلمون',
    'غربيقاره': 'غربقاره',
    'خانالمنقوره': 'خانمنقوره',
    'الوغر': 'الوغرالنبك',
    # This name appeared twice in the table; Python kept this second mapping and
    # the earlier identity entry never applied. Only the effective one is kept.
    'كفرروحين': 'كفررويحين',
    'الزينهمصياف': 'مصيافالزينه',
}


def _normalize_text(value) -> str:
    return ' '.join(str(value or '').strip().split())


def _dam_match_key(value: str) -> str:
    text = _normalize_text(value).replace('\u0640', '')
    if text.startswith('سد '):
        text = text[3:].strip()
    for ch in 'أإآٱ':
        text = text.replace(ch, 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\s_\-/\\]+', '', text)
    return text


def _governorate_key(value: str) -> str:
    text = GOV_PREFIX.sub('', _normalize_text(value)).strip()
    for ch in 'أإآٱ':
        text = text.replace(ch, 'ا')
    return text


def _parse_date(value) -> date | None:
    if value is None or value == '':
        return None
    if isinstance(value, float):
        try:
            return xlrd.xldate_as_datetime(value, 0).date()
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    match = DATE_IN_TEXT.search(text)
    if match:
        try:
            return datetime.strptime(match.group(1), '%d/%m/%Y').date()
        except ValueError:
            return None
    return None


def _parse_decimal(value) -> Decimal | None:
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _parse_year_from_filename(path: Path) -> int | None:
    match = YEAR_PATTERN.search(path.stem)
    if not match:
        return None
    return int(match.group(1))


def _is_metadata_sheet(sheet) -> bool:
    if sheet.nrows < 2 or sheet.ncols < 10:
        return False
    header = [_normalize_text(sheet.cell_value(0, col)) for col in range(min(6, sheet.ncols))]
    return header[0] == 'السد' and 'المحافظة' in header


def _is_storage_sheet(sheet) -> bool:
    if sheet.nrows < 2 or sheet.ncols < 4:
        return False
    header = [_normalize_text(sheet.cell_value(0, col)) for col in range(min(5, sheet.ncols))]
    return header[0] == 'المحافظة' and header[1] == 'السد'


def _is_snapshot_workbook(workbook) -> bool:
    names = workbook.sheet_names()
    if any('القطر' in name for name in names):
        return True
    for idx in range(min(3, workbook.nsheets)):
        sheet = workbook.sheet_by_index(idx)
        for row_idx in range(min(5, sheet.nrows)):
            cells = [
                _normalize_text(sheet.cell_value(row_idx, col))
                for col in range(min(sheet.ncols, 7))
            ]
            joined = ' '.join(cells)
            if 'اسم السد' in joined.replace('\u0640', '') or 'اسـم السـد' in joined:
                if any('تخزين' in cell for cell in cells):
                    return True
    return False


def _header_looks_like_dam_table(cells: list[str]) -> bool:
    joined = ' '.join(cells).replace('\u0640', '')
    has_name = 'اسم السد' in joined or 'اسـم السـد' in joined
    has_storage = any('تخزين' in cell and 'حالي' in cell for cell in cells) or any(
        'التخزين الحالي' in cell.replace('\u0640', '') for cell in cells
    )
    return has_name and (has_storage or any('تخزين' in cell for cell in cells))


class Command(BaseCommand):
    help = 'Import Syrian dam metadata and storage XLS files into the water database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=os.getenv('DAM_DATA_DIR', str(Path(__file__).resolve().parents[4] / 'السدود')),
            help='Root folder containing dam .xls files.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing dam storage readings before import.',
        )

    def handle(self, *args, **options):
        if xlrd is None:
            raise CommandError(f'xlrd is required: {_XLRD_IMPORT_ERROR}')

        root = Path(options['path'])
        if not root.is_dir():
            raise CommandError(f'Dam data folder not found: {root}')

        files = sorted(
            path
            for path in root.rglob('*.xls')
            if path.is_file() and not path.name.startswith('~$')
        )
        if not files:
            raise CommandError(f'No .xls files found under {root}')

        metadata_files: list[Path] = []
        flat_storage_files: list[Path] = []
        snapshot_files: list[Path] = []

        for path in files:
            workbook = xlrd.open_workbook(str(path))
            if _is_metadata_sheet(workbook.sheet_by_index(0)):
                metadata_files.append(path)
            elif _is_snapshot_workbook(workbook):
                snapshot_files.append(path)
            elif _is_storage_sheet(workbook.sheet_by_index(0)):
                flat_storage_files.append(path)
            else:
                self.stdout.write(self.style.WARNING(f'Skip (unknown format): {path.name}'))

        if not metadata_files and not flat_storage_files and not snapshot_files:
            raise CommandError(
                'No recognized dam workbooks found. Expected معلومات السدود.xls, '
                'yearly storage sheets, or تخازين السدود مع المقابل محافظات*.xls.'
            )

        if options['clear']:
            self.stdout.write('Clearing existing dam storage readings…')
            DamStorageReading.objects.all().delete()

        self._dam_index = self._build_dam_index()

        if metadata_files:
            meta_rows = 0
            for file_path in metadata_files:
                meta_rows += self._import_metadata(file_path)
            self.stdout.write(f'Imported metadata for {meta_rows:,} dams')
            self._dam_index = self._build_dam_index()
        else:
            self.stdout.write('No metadata workbook — matching storage rows to existing dams.')

        total_rows = 0
        for file_path in flat_storage_files:
            rows = self._import_storage_file(file_path)
            total_rows += rows
            year = _parse_year_from_filename(file_path)
            self.stdout.write(f'Imported {rows:,} flat storage rows ({year or file_path.stem})')

        for file_path in snapshot_files:
            rows = self._import_snapshot_file(file_path)
            total_rows += rows
            self.stdout.write(f'Imported {rows:,} snapshot rows ({file_path.stem})')

        self.stdout.write(self.style.SUCCESS(f'Done — {total_rows:,} storage rows processed.'))

    @staticmethod
    def _build_dam_index() -> dict[str, list[Dam]]:
        index: dict[str, list[Dam]] = {}
        for dam in Dam.objects.all():
            key = _dam_match_key(dam.name)
            index.setdefault(key, []).append(dam)
            if key.startswith('ال') and len(key) > 2:
                index.setdefault(key[2:], []).append(dam)
        return index

    def _resolve_dam(self, *, name: str, governorate: str) -> Dam | None:
        display_name = _normalize_text(name)
        if display_name.startswith('سد '):
            display_name = display_name[3:].strip()
        gov = _normalize_text(governorate)
        gov_key = _governorate_key(gov)

        key = NAME_ALIASES.get(_dam_match_key(name), _dam_match_key(name))
        candidates = list(self._dam_index.get(key, []))
        if not candidates and key.startswith('ال') and len(key) > 2:
            candidates = list(self._dam_index.get(key[2:], []))

        if not candidates:
            for dam_key, dams in self._dam_index.items():
                if len(key) >= 4 and (key in dam_key or dam_key in key):
                    candidates.extend(dams)

        if candidates:
            # Prefer same governorate when known.
            if gov_key:
                for dam in candidates:
                    if _governorate_key(dam.governorate) == gov_key:
                        return dam
            return candidates[0]

        # Dam is a master catalog owned by report_moe — moeds cannot create rows here.
        # Unmatched readings are skipped; add the dam via report_moe's catalog seeder first.
        return None

    def _import_metadata(self, file_path: Path) -> int:
        workbook = xlrd.open_workbook(str(file_path))
        sheet = workbook.sheet_by_index(0)
        processed = 0

        for row_idx in range(1, sheet.nrows):
            name = _normalize_text(sheet.cell_value(row_idx, 0))
            if not name:
                continue
            governorate = _normalize_text(sheet.cell_value(row_idx, 1))
            utm_x = _parse_decimal(sheet.cell_value(row_idx, 2))
            utm_y = _parse_decimal(sheet.cell_value(row_idx, 3))
            lat, lon = utm_to_wgs84(
                float(utm_x) if utm_x is not None else None,
                float(utm_y) if utm_y is not None else None,
            )
            status_note = _normalize_text(sheet.cell_value(row_idx, 4))
            dam_type = _normalize_text(sheet.cell_value(row_idx, 5))
            height_m = _parse_decimal(sheet.cell_value(row_idx, 6))
            length_m = _parse_decimal(sheet.cell_value(row_idx, 7))
            max_storage = _parse_decimal(sheet.cell_value(row_idx, 8))
            dead_storage = _parse_decimal(sheet.cell_value(row_idx, 9))
            built_year_raw = sheet.cell_value(row_idx, 10)
            built_year = int(float(built_year_raw)) if built_year_raw not in ('', None) else None
            purpose = _normalize_text(sheet.cell_value(row_idx, 11))

            dam, created = Dam.objects.get_or_create(
                governorate=governorate,
                name=name,
                defaults={
                    'utm_x': utm_x,
                    'utm_y': utm_y,
                    'latitude': lat,
                    'longitude': lon,
                    'status_note': status_note,
                    'dam_type': dam_type,
                    'height_m': height_m,
                    'length_m': length_m,
                    'max_storage_mcm': max_storage,
                    'dead_storage_mcm': dead_storage,
                    'built_year': built_year,
                    'purpose': purpose,
                },
            )
            if not created:
                updated_fields: list[str] = []
                field_map = {
                    'utm_x': utm_x,
                    'utm_y': utm_y,
                    'latitude': lat,
                    'longitude': lon,
                    'status_note': status_note,
                    'dam_type': dam_type,
                    'height_m': height_m,
                    'length_m': length_m,
                    'max_storage_mcm': max_storage,
                    'dead_storage_mcm': dead_storage,
                    'built_year': built_year,
                    'purpose': purpose,
                }
                for field, value in field_map.items():
                    if value in (None, ''):
                        continue
                    if getattr(dam, field) != value:
                        setattr(dam, field, value)
                        updated_fields.append(field)
                if updated_fields:
                    dam.save(update_fields=updated_fields)
            processed += 1

        return processed

    def _import_storage_file(self, file_path: Path) -> int:
        workbook = xlrd.open_workbook(str(file_path))
        sheet = workbook.sheet_by_index(0)
        if not _is_storage_sheet(sheet):
            self.stdout.write(self.style.WARNING(f'Skip (unknown format): {file_path.name}'))
            return 0

        batch: list[DamStorageReading] = []
        processed = 0

        for row_idx in range(1, sheet.nrows):
            governorate = _normalize_text(sheet.cell_value(row_idx, 0))
            dam_name = _normalize_text(sheet.cell_value(row_idx, 1))
            if not governorate or not dam_name:
                continue
            reading_date = _parse_date(sheet.cell_value(row_idx, 2))
            if not reading_date:
                continue
            storage = _parse_decimal(sheet.cell_value(row_idx, 3)) or Decimal('0')
            notes = _normalize_text(sheet.cell_value(row_idx, 4)) if sheet.ncols > 4 else ''

            dam = self._resolve_dam(name=dam_name, governorate=governorate)
            batch.append(
                DamStorageReading(
                    dam=dam,
                    reading_date=reading_date,
                    storage_mcm=storage,
                    notes=notes,
                ),
            )
            processed += 1

            if len(batch) >= 3000:
                self._flush_batch(batch)
                batch.clear()

        if batch:
            self._flush_batch(batch)

        return processed

    def _import_snapshot_file(self, file_path: Path) -> int:
        workbook = xlrd.open_workbook(str(file_path))
        batch: list[DamStorageReading] = []
        processed = 0

        for sheet_idx, sheet_name in enumerate(workbook.sheet_names()):
            if 'القطر' in sheet_name:
                continue
            sheet = workbook.sheet_by_index(sheet_idx)
            governorate = self._default_governorate_for_sheet(sheet_name)
            reading_date: date | None = None
            in_table = False

            for row_idx in range(sheet.nrows):
                cells = [
                    _normalize_text(sheet.cell_value(row_idx, col))
                    for col in range(sheet.ncols)
                ]
                first = cells[0] if cells else ''

                if first.startswith('محافظة'):
                    governorate = GOV_PREFIX.sub('', first).strip()
                    in_table = False
                    continue

                if _header_looks_like_dam_table(cells):
                    in_table = True
                    reading_date = None
                    for cell in cells:
                        parsed = _parse_date(cell)
                        if parsed:
                            reading_date = parsed
                            break
                    continue

                if not in_table or reading_date is None:
                    continue

                dam_name = cells[1] if len(cells) > 1 else ''
                if not dam_name or dam_name == 'المجموع':
                    continue
                if dam_name.startswith('محافظة') or 'تسلسل' in dam_name:
                    continue

                storage = _parse_decimal(cells[3] if len(cells) > 3 else None)
                if storage is None:
                    continue
                notes = cells[6] if len(cells) > 6 else (cells[5] if len(cells) > 5 else '')

                # الفرات sheet has no محافظة rows — keep sheet default / name-based resolve.
                gov = governorate
                if not gov and sheet_name == 'الفرات':
                    gov = {
                        'الفرات': 'الرقة',
                        'تشرين': 'حلب',
                        'غديران': 'الرقة',
                        'كديران': 'الرقة',
                    }.get(dam_name, 'الرقة')

                dam = self._resolve_dam(name=dam_name, governorate=gov or '')
                if dam is None:
                    self.stdout.write(self.style.WARNING(
                        f'No catalog match for dam "{dam_name}" ({gov or "?"}) — skipped. '
                        'Add it via report_moe master_data first.'
                    ))
                    continue

                batch.append(
                    DamStorageReading(
                        dam=dam,
                        reading_date=reading_date,
                        storage_mcm=storage,
                        notes=notes,
                    ),
                )
                processed += 1

                if len(batch) >= 3000:
                    self._flush_batch(batch)
                    batch.clear()

        if batch:
            self._flush_batch(batch)

        return processed

    @staticmethod
    def _default_governorate_for_sheet(sheet_name: str) -> str:
        name = _normalize_text(sheet_name)
        if name == 'الفرات':
            return ''
        if name in {'حماة', 'حمص', 'السويداء', 'ريف دمشق'}:
            return name
        return ''

    @staticmethod
    def _flush_batch(batch: list[DamStorageReading]) -> None:
        # Collapse duplicates within the same flush (fuzzy name matches / repeated rows).
        deduped: dict[tuple[int, date], DamStorageReading] = {}
        for row in batch:
            deduped[(row.dam_id, row.reading_date)] = row
        rows = list(deduped.values())
        if not rows:
            return
        with transaction.atomic():
            DamStorageReading.objects.bulk_create(
                rows,
                update_conflicts=True,
                unique_fields=['dam', 'reading_date'],
                update_fields=['storage_mcm', 'notes'],
            )
