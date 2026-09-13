"""Shared PDF typeface resolution (Qomra Arabic + Latin fallbacks)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
QOMRA_DIR = BACKEND_ROOT / 'static' / 'fonts' / 'qomra'
QOMRA_REGULAR = QOMRA_DIR / 'itfQomraArabic-Regular.ttf'
QOMRA_BOLD = QOMRA_DIR / 'itfQomraArabic-Bold.ttf'

_FONT_AR_CANDIDATES = (
    str(QOMRA_REGULAR),
    'C:/Windows/Fonts/tahoma.ttf',
    '/System/Library/Fonts/Supplemental/Tahoma.ttf',
    '/Library/Fonts/Arial Unicode.ttf',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
)
_FONT_AR_BOLD_CANDIDATES = (
    str(QOMRA_BOLD),
    'C:/Windows/Fonts/tahomabd.ttf',
    '/System/Library/Fonts/Supplemental/Tahoma Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/Library/Fonts/Arial Unicode.ttf',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
)
_FONT_EN_CANDIDATES = (
    str(QOMRA_REGULAR),
    'C:/Windows/Fonts/arial.ttf',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/Library/Fonts/Arial Unicode.ttf',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
)


def resolve_font(*candidates: str) -> str:
    for path in candidates:
        if Path(path).is_file():
            return path
    raise FileNotFoundError(
        'PDF fonts not found. Tried: ' + ', '.join(candidates)
    )


@lru_cache(maxsize=1)
def font_ar_path() -> str:
    return resolve_font(*_FONT_AR_CANDIDATES)


@lru_cache(maxsize=1)
def font_ar_bold_path() -> str:
    return resolve_font(*_FONT_AR_BOLD_CANDIDATES)


@lru_cache(maxsize=1)
def font_en_path() -> str:
    return resolve_font(*_FONT_EN_CANDIDATES)


def font_ar_face() -> str:
    return Path(font_ar_path()).name


def font_ar_bold_face() -> str:
    return Path(font_ar_bold_path()).name


def qomra_available() -> bool:
    return QOMRA_REGULAR.is_file() and QOMRA_BOLD.is_file()


def font_archive_dirs() -> list[str]:
    """Unique parent directories of resolved PDF fonts (for MuPDF Archive)."""
    seen: list[str] = []
    if qomra_available():
        seen.append(str(QOMRA_DIR))
    for resolver in (font_ar_path, font_ar_bold_path, font_en_path):
        parent = str(Path(resolver()).parent)
        if parent not in seen:
            seen.append(parent)
    return seen
