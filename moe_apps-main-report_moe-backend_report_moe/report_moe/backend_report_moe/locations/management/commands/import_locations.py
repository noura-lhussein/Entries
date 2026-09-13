import csv
import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from locations.models import Community, District, Governorate, SubDistrict
from locations.translations import (
    translate_district,
    translate_governorate,
    translate_subdistrict,
)


def _parse_bool(value: str) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES"}


def _wkb_geometry(wkb_hex: str):
    if not wkb_hex or not str(wkb_hex).strip():
        return None
    hex_clean = wkb_hex.strip()
    if len(hex_clean) % 2:
        hex_clean = hex_clean[:-1]
    try:
        return GEOSGeometry(hex_clean, srid=4326)
    except Exception:
        try:
            return GEOSGeometry(
                memoryview(bytes.fromhex(hex_clean)), srid=4326)
        except Exception:
            return None


def _parse_geom(wkb_hex: str):
    geom = _wkb_geometry(wkb_hex)
    if geom is None:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if geom.geom_type == "Polygon":
        return MultiPolygon(geom)
    if geom.geom_type == "MultiPolygon":
        return geom
    return None


def _parse_point_coords(wkb_hex: str) -> tuple[Decimal, Decimal] | None:
    geom = _wkb_geometry(wkb_hex)
    if geom is None or geom.geom_type != "Point":
        return None
    return Decimal(str(round(geom.y, 6))), Decimal(str(round(geom.x, 6)))


def _read_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row.get("name", "").strip() and row.get("code", "").strip()
        ]


def _name_ar_from_row(row: dict, name_en: str, fallback) -> str:
    raw = row.get("name_ar", "").strip()
    if raw:
        return raw
    return fallback(name_en)


class Command(BaseCommand):
    help = (
        "Import governorates, districts, sub-districts, and communities "
        "from CSV files in LOCATIONS_DATA_DIR."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=settings.LOCATIONS_DATA_DIR,
            help="Directory containing location CSV files.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing location rows before import.",
        )
        parser.add_argument(
            "--skip-geom",
            action="store_true",
            help="Skip geometry import (names and hierarchy only).",
        )
        parser.add_argument(
            "--communities-only",
            action="store_true",
            help="Import communities.csv only (sub-districts must already exist).",
        )

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])
        if not data_dir.is_dir():
            raise CommandError(f"Data directory not found: {data_dir}")

        communities_path = data_dir / "communities.csv"
        communities_only = options["communities_only"]

        if communities_only:
            if not communities_path.is_file():
                raise CommandError(
                    f"Missing communities file: {communities_path}")
            subdistricts_path = data_dir / "subdistricts.csv"
            if not subdistricts_path.is_file():
                raise CommandError(
                    f"Missing subdistricts file (needed for parent mapping): "
                    f"{subdistricts_path}"
                )
            sub_by_csv_id = self._subdistrict_csv_id_map(subdistricts_path)
            skip_geom = options["skip_geom"]
            self.geom_skipped = 0
            if not skip_geom:
                try:
                    GEOSGeometry("POINT(0 0)")
                except Exception as exc:
                    raise CommandError(
                        "GeoDjango GEOS/GDAL is unavailable. "
                        "Use --skip-geom or run inside Docker with GDAL installed."
                    ) from exc
            with transaction.atomic():
                comm_count = self._import_communities(
                    communities_path, sub_by_csv_id, skip_geom=skip_geom)
            self.stdout.write(
                self.style.SUCCESS(f"Imported {comm_count} communities.")
            )
            if self.geom_skipped and not skip_geom:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped coordinates for {self.geom_skipped} "
                        "community row(s) (invalid WKB in CSV)."
                    )
                )
            return

        files = {
            "governorates": data_dir / "governorates.csv",
            "districts": data_dir / "districts.csv",
            "subdistricts": data_dir / "subdistricts.csv",
        }
        for label, path in files.items():
            if not path.is_file():
                raise CommandError(f"Missing {label} file: {path}")

        skip_geom = options["skip_geom"]
        self.geom_skipped = 0
        if not skip_geom:
            try:
                GEOSGeometry("POINT(0 0)")
            except Exception as exc:
                raise CommandError(
                    "GeoDjango GEOS/GDAL is unavailable. "
                    "Use --skip-geom or run inside Docker with GDAL installed."
                ) from exc

        with transaction.atomic():
            if options["clear"]:
                Community.objects.all().delete()
                SubDistrict.objects.all().delete()
                District.objects.all().delete()
                Governorate.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    "Cleared existing locations."))

            gov_by_csv_id = self._import_governorates(
                files["governorates"], skip_geom=skip_geom)
            dist_by_csv_id = self._import_districts(
                files["districts"], gov_by_csv_id, skip_geom=skip_geom)
            sub_by_csv_id = self._import_subdistricts(
                files["subdistricts"], dist_by_csv_id, skip_geom=skip_geom)
            comm_count = 0
            if communities_path.is_file():
                comm_count = self._import_communities(
                    communities_path, sub_by_csv_id, skip_geom=skip_geom)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(gov_by_csv_id)} governorates, "
                f"{len(dist_by_csv_id)} districts, "
                f"{len(sub_by_csv_id)} sub-districts, "
                f"{comm_count} communities."
            )
        )
        if self.geom_skipped and not skip_geom:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped geometry for {self.geom_skipped} row(s) "
                    "(invalid or truncated WKB in CSV)."
                )
            )

    def _geom_or_none(self, raw: str, *, skip_geom: bool):
        if skip_geom:
            return None
        geom = _parse_geom(raw)
        if raw and raw.strip() and geom is None:
            self.geom_skipped += 1
        return geom

    def _import_governorates(self, path: Path, *, skip_geom: bool) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for row in _read_csv_rows(path):
            csv_id = row["id"].strip()
            name_en = row["name"].strip()
            code = row["code"].strip()
            obj, _created = Governorate.objects.update_or_create(
                code=code,
                defaults={
                    "uid": uuid.UUID(row["uid"].strip()),
                    "name_en": name_en,
                    "name_ar": _name_ar_from_row(row, name_en, translate_governorate),
                    "is_active": _parse_bool(row.get("is_active", "TRUE")),
                    "geom": self._geom_or_none(row.get("geom", ""), skip_geom=skip_geom),
                },
            )
            mapping[csv_id] = obj.pk
        return mapping

    def _import_districts(
        self,
        path: Path,
        gov_by_csv_id: dict[str, int],
        *,
        skip_geom: bool,
    ) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for row in _read_csv_rows(path):
            csv_id = row["id"].strip()
            parent_id = row.get("governorate_id", "").strip()
            governorate_id = gov_by_csv_id.get(parent_id)
            if not governorate_id:
                raise CommandError(
                    f"District {row['code']} references unknown governorate_id={parent_id}"
                )
            name_en = row["name"].strip()
            code = row["code"].strip()
            obj, _created = District.objects.update_or_create(
                code=code,
                defaults={
                    "governorate_id": governorate_id,
                    "uid": uuid.UUID(row["uid"].strip()),
                    "name_en": name_en,
                    "name_ar": _name_ar_from_row(row, name_en, translate_district),
                    "is_active": _parse_bool(row.get("is_active", "TRUE")),
                    "geom": self._geom_or_none(row.get("geom", ""), skip_geom=skip_geom),
                },
            )
            mapping[csv_id] = obj.pk
        return mapping

    def _import_subdistricts(
        self,
        path: Path,
        dist_by_csv_id: dict[str, int],
        *,
        skip_geom: bool,
    ) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for row in _read_csv_rows(path):
            csv_id = row["id"].strip()
            parent_id = row.get("district_id", "").strip()
            district_id = dist_by_csv_id.get(parent_id)
            if not district_id:
                raise CommandError(
                    f"Sub-district {row['code']} references unknown district_id={parent_id}"
                )
            name_en = row["name"].strip()
            code = row["code"].strip()
            obj, _created = SubDistrict.objects.update_or_create(
                code=code,
                defaults={
                    "district_id": district_id,
                    "uid": uuid.UUID(row["uid"].strip()),
                    "name_en": name_en,
                    "name_ar": _name_ar_from_row(row, name_en, translate_subdistrict),
                    "is_active": _parse_bool(row.get("is_active", "TRUE")),
                    "geom": self._geom_or_none(row.get("geom", ""), skip_geom=skip_geom),
                },
            )
            mapping[csv_id] = obj.pk
        return mapping

    def _subdistrict_csv_id_map(self, path: Path) -> dict[str, int]:
        """Map CSV sub-district id → DB pk using codes already in the database."""
        mapping: dict[str, int] = {}
        for row in _read_csv_rows(path):
            csv_id = row["id"].strip()
            code = row["code"].strip()
            try:
                subdistrict = SubDistrict.objects.get(code=code, deleted=False)
            except SubDistrict.DoesNotExist as exc:
                raise CommandError(
                    f"Sub-district code {code} from CSV is missing in the database. "
                    "Import governorates/districts/sub-districts first."
                ) from exc
            mapping[csv_id] = subdistrict.pk
        return mapping

    def _import_communities(
        self,
        path: Path,
        sub_by_csv_id: dict[str, int],
        *,
        skip_geom: bool,
    ) -> int:
        count = 0
        for row in _read_csv_rows(path):
            parent_id = row.get("subdistrict_id", "").strip()
            subdistrict_id = sub_by_csv_id.get(parent_id)
            if not subdistrict_id:
                raise CommandError(
                    f"Community {row['code']} references unknown "
                    f"subdistrict_id={parent_id}"
                )
            name_en = row["name"].strip()
            code = row["code"].strip()
            uid_raw = row.get("uid", "").strip()
            defaults = {
                "subdistrict_id": subdistrict_id,
                "uid": uuid.UUID(uid_raw) if uid_raw else None,
                "name_en": name_en,
                "name_ar": _name_ar_from_row(row, name_en, translate_subdistrict),
                "is_active": _parse_bool(row.get("is_active", "TRUE")),
            }
            if not skip_geom:
                coords = _parse_point_coords(row.get("geom", ""))
                if coords:
                    defaults["latitude"], defaults["longitude"] = coords
                elif row.get("geom", "").strip():
                    self.geom_skipped += 1
            Community.objects.update_or_create(
                code=code,
                defaults=defaults,
            )
            count += 1
        return count
