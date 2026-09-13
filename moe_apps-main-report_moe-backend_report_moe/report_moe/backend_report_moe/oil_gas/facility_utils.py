from __future__ import annotations

import re

from .models import Facility


def slug_code(name: str) -> str:
    code = re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')
    return (code or 'facility')[:50]


def unique_facility_code(base: str) -> str:
    code = base
    suffix = 1
    while Facility.objects.filter(code=code).exists():
        suffix += 1
        code = f'{base}-{suffix}'[:50]
    return code


def get_facility(*, code: str | None = None, name: str | None = None) -> Facility:
    if code:
        try:
            return Facility.objects.get(code__iexact=code.strip())
        except Facility.DoesNotExist as exc:
            raise ValueError(f'Unknown facility code: {code}') from exc
    if name:
        try:
            return Facility.objects.get(name_en__iexact=name.strip())
        except Facility.DoesNotExist as exc:
            raise ValueError(f'Unknown facility: {name}') from exc
    raise ValueError('facility_code or facility_name is required')
