"""Add name_ar column to location CSV files and fill Arabic names."""

import csv
import json
import re
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from locations.translations import (
    translate_district,
    translate_governorate,
    translate_subdistrict,
)

try:
    from deep_translator import GoogleTranslator
except ImportError as exc:
    GoogleTranslator = None  # type: ignore[misc, assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
CACHE_FILENAME = "_translation_cache.json"


def _has_arabic(text: str) -> bool:
    return bool(ARABIC_RE.search(text or ""))


class Command(BaseCommand):
    help = "Add name_ar to location CSV files (dictionary + Google Translate fallback)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=settings.LOCATIONS_DATA_DIR,
            help="Directory containing location CSV files.",
        )
        parser.add_argument(
            "--only",
            choices=("governorates", "districts",
                     "subdistricts", "communities"),
            help="Process a single CSV file.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.12,
            help="Seconds between online translation requests (communities/subdistricts).",
        )

    def handle(self, *args, **options):
        data_dir = Path(options["data_dir"])
        if not data_dir.is_dir():
            raise CommandError(f"Data directory not found: {data_dir}")

        cache_path = data_dir / CACHE_FILENAME
        cache = self._load_cache(cache_path)
        online = self._online_translator(options["delay"])

        jobs = [
            ("governorates.csv", self._translate_governorate),
            ("districts.csv", self._translate_district),
            ("subdistricts.csv", lambda name: self._translate_with_fallback(
                name, translate_subdistrict, online, cache)),
            ("communities.csv", lambda name: self._translate_online(
                name, online, cache)),
        ]
        job_by_file = {filename: fn for filename, fn in jobs}
        only = options.get("only")
        if only:
            jobs = [(f"{only}.csv", job_by_file[f"{only}.csv"])]

        batch_online = self._batch_online_translator(
            options["delay"],
            cache,
            on_batch=lambda: self._save_cache(cache_path, cache),
        )

        for filename, translator in jobs:
            path = data_dir / filename
            if not path.is_file():
                raise CommandError(f"Missing file: {path}")
            active = batch_online if filename == "communities.csv" else translator
            count = self._process_file(path, active)
            self.stdout.write(self.style.SUCCESS(
                f"Updated {filename}: {count} row(s) with name_ar."))
            self._save_cache(cache_path, cache)

        if batch_online.requests or online.requests:
            self.stdout.write(
                f"Online translations this run: "
                f"{batch_online.requests + online.requests} "
                f"(cache size: {len(cache)})."
            )

    def _batch_online_translator(self, delay: float, cache: dict[str, str], *, on_batch=None):
        if GoogleTranslator is None:
            raise CommandError(
                "deep-translator is required for communities. "
                f"Install with: pip install deep-translator ({_IMPORT_ERROR})"
            )
        return _BatchOnlineTranslator(delay=delay, cache=cache, on_batch=on_batch)

    def _load_cache(self, path: Path) -> dict[str, str]:
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_cache(self, path: Path, cache: dict[str, str]) -> None:
        path.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _online_translator(self, delay: float):
        if GoogleTranslator is None:
            raise CommandError(
                "deep-translator is required for sub-districts and communities. "
                f"Install with: pip install deep-translator ({_IMPORT_ERROR})"
            )
        return _OnlineTranslator(delay=delay)

    @staticmethod
    def _translate_governorate(name: str) -> str:
        return translate_governorate(name)

    @staticmethod
    def _translate_district(name: str) -> str:
        return translate_district(name)

    @staticmethod
    def _translate_with_fallback(name, offline_fn, online, cache):
        ar = offline_fn(name)
        if _has_arabic(ar) and ar.strip().lower() != name.strip().lower():
            return ar
        return online.translate(name, cache)

    @staticmethod
    def _translate_online(name, online, cache):
        return online.translate(name, cache)

    def _process_file(self, path: Path, translator) -> int:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise CommandError(f"Empty CSV: {path}")
            fieldnames = list(reader.fieldnames)
            if "name_ar" not in fieldnames:
                if "name" in fieldnames:
                    idx = fieldnames.index("name") + 1
                    fieldnames.insert(idx, "name_ar")
                else:
                    fieldnames.insert(0, "name_ar")
            rows = list(reader)

        names = [(row.get("name") or "").strip() for row in rows]
        if isinstance(translator, _BatchOnlineTranslator):
            arabic_names = translator.translate_many(names)
        else:
            arabic_names = [translator(name) if name else "" for name in names]

        updated = 0
        for row, name_en, name_ar in zip(rows, names, arabic_names, strict=True):
            if not name_en:
                continue
            row["name_ar"] = name_ar
            updated += 1

        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)
        return updated


class _OnlineTranslator:
    def __init__(self, *, delay: float):
        self._translator = GoogleTranslator(source="en", target="ar")
        self.delay = delay
        self.requests = 0

    def translate(self, name_en: str, cache: dict[str, str]) -> str:
        key = name_en.strip()
        if not key:
            return ""
        cached = cache.get(key)
        if cached:
            return cached
        for attempt in range(4):
            try:
                if self.requests and self.delay:
                    time.sleep(self.delay)
                result = self._translator.translate(key) or key
                self.requests += 1
                cache[key] = result.strip()
                return cache[key]
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        cache[key] = key
        return key


class _BatchOnlineTranslator:
    BATCH_SIZE = 100

    def __init__(self, *, delay: float, cache: dict[str, str], on_batch=None):
        self._translator = GoogleTranslator(source="en", target="ar")
        self.delay = delay
        self.cache = cache
        self.on_batch = on_batch
        self.requests = 0

    def translate_many(self, names: list[str]) -> list[str]:
        results: list[str] = []
        pending: list[tuple[int, str]] = []
        cached_count = 0

        for index, name in enumerate(names):
            key = name.strip()
            if not key:
                results.append("")
                continue
            cached = self.cache.get(key)
            if cached:
                results.append(cached)
                cached_count += 1
                continue
            results.append("")
            pending.append((index, key))

        if cached_count:
            print(
                f"  cache hit: {cached_count}/{len(names)} names", flush=True)
        if not pending:
            return results

        for start in range(0, len(pending), self.BATCH_SIZE):
            chunk = pending[start:start + self.BATCH_SIZE]
            texts = [text for _, text in chunk]
            translated = self._translate_batch(texts)
            for (index, key), ar in zip(chunk, translated, strict=True):
                value = (ar or key).strip()
                self.cache[key] = value
                results[index] = value
            done = min(start + self.BATCH_SIZE, len(pending))
            print(
                f"  translated {done}/{len(pending)} new names...", flush=True)
            if self.on_batch:
                self.on_batch()
            if self.delay:
                time.sleep(self.delay)

        return results

    def _translate_batch(self, texts: list[str]) -> list[str]:
        for attempt in range(4):
            try:
                self.requests += 1
                return self._translator.translate_batch(texts)
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        return texts
