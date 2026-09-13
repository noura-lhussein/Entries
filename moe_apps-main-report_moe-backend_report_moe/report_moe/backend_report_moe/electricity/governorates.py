from __future__ import annotations

GOVERNORATES: tuple[tuple[str, str, str], ...] = (
    ('damascus', 'Damascus', 'دمشق'),
    ('rif_damascus', 'Rif Damascus', 'ريف دمشق'),
    ('sweida', 'Sweida', 'السويداء'),
    ('daraa', 'Daraa', 'درعا'),
    ('quneitra', 'Quneitra', 'القنيطرة'),
    ('homs', 'Homs', 'حمص'),
    ('hama', 'Hama', 'حماه'),
    ('tartous', 'Tartous', 'طرطوس'),
    ('latakia', 'Latakia', 'اللاذقية'),
    ('aleppo', 'Aleppo', 'حلب'),
    ('deir_ez_zor', 'Deir ez-Zor', 'دير الزور'),
    ('raqqa', 'Raqqa', 'الرقة'),
    ('hasakah', 'Hasakah', 'الحسكة'),
)

GOVERNORATE_BY_CODE = {code: (en, ar) for code, en, ar in GOVERNORATES}
