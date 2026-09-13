"""Budget and project code formatting helpers."""

from __future__ import annotations


def budget_code(year: int, letter_index: int) -> str:
    """Build annual budget code like B26A."""
    yy = year % 100
    letter = chr(ord("A") + letter_index)
    return f"B{yy:02d}{letter}"


def parse_budget_letter(code: str, year: int) -> int | None:
    """Return 0-based letter index from a budget code, or None if invalid."""
    prefix = f"B{year % 100:02d}"
    if not code.startswith(prefix) or len(code) != len(prefix) + 1:
        return None
    letter = code[-1]
    if letter < "A" or letter > "Z":
        return None
    return ord(letter) - ord("A")


def next_budget_letter_index(year: int, existing_codes: list[str]) -> int:
    max_index = -1
    for code in existing_codes:
        letter_index = parse_budget_letter(code, year)
        if letter_index is not None:
            max_index = max(max_index, letter_index)
    return max_index + 1


def project_suffix(index: int) -> str:
    """Build project sequence like 00A."""
    letter = chr(ord("A") + (index % 26))
    number = index // 26
    return f"{number:02d}{letter}"


def parse_project_suffix(suffix: str) -> int | None:
    """Parse 00A-style suffix to 0-based index."""
    if len(suffix) != 3:
        return None
    try:
        number = int(suffix[:2])
        letter = suffix[2].upper()
    except ValueError:
        return None
    if letter < "A" or letter > "Z":
        return None
    return number * 26 + (ord(letter) - ord("A"))


def project_code_prefix(
    budget_code: str,
    subdistrict_code: str,
    community_code: str,
) -> str:
    """Prefix shared by projects in the same budget and OCHA location."""
    return f"{budget_code}-{subdistrict_code}-{community_code}-P"


def project_code(
    budget_code: str,
    subdistrict_code: str,
    community_code: str,
    index: int,
) -> str:
    """Build full project code like B26A-SY020206-C8380-P00A."""
    return f"{project_code_prefix(budget_code, subdistrict_code, community_code)}{project_suffix(index)}"


def next_project_index(existing_project_codes: list[str], code_prefix: str) -> int:
    prefix = code_prefix if code_prefix.endswith("-P") else f"{code_prefix}-P"
    max_index = -1
    for code in existing_project_codes:
        if not code.startswith(prefix):
            continue
        suffix = code[len(prefix):]
        parsed = parse_project_suffix(suffix)
        if parsed is not None:
            max_index = max(max_index, parsed)
    return max_index + 1
