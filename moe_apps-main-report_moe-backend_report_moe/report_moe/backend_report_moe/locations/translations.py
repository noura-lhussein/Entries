"""English to Arabic names for official admin divisions."""

GOVERNORATE_AR = {
    'Al-Hasakeh': 'الحسكة',
    'Aleppo': 'حلب',
    'Ar-Raqqa': 'الرقة',
    'As-Sweida': 'السويداء',
    'Damascus': 'دمشق',
    "Dar'a": 'درعا',
    'Deir-ez-Zor': 'دير الزور',
    'Hama': 'حماة',
    'Homs': 'حمص',
    'Idleb': 'إدلب',
    'Lattakia': 'اللاذقية',
    'Quneitra': 'القنيطرة',
    'Rural Damascus': 'ريف دمشق',
    'Tartous': 'طرطوس',
}

DISTRICT_AR = {
    "A'zaz": 'عزاز',
    'Abu Kamal': 'البوكمال',
    'Afrin': 'عفرين',
    'Ain Al Arab': 'عين العرب',
    'Al Bab': 'الباب',
    'Al Fiq': 'الفيق',
    "Al Ma'ra": 'معرة النعمان',
    'Al Makhrim': 'المخرم',
    'Al Mayadin': 'الميادين',
    'Al Qutayfah': 'القطيفة',
    'Al-Haffa': 'الحفة',
    'Al-Hasakeh': 'الحسكة',
    'Al-Malikeyyeh': 'المالكية',
    'Al-Qardaha': 'القرداحة',
    'Al-Qusayr': 'القصير',
    'An Nabk': 'النبك',
    'Ar-Raqqa': 'الرقة',
    'Ar-Rastan': 'الرستن',
    'Ariha': 'أريحا',
    'As-Safira': 'السفيرة',
    'As-Salamiyeh': 'السلمية',
    'As-Sanamayn': 'الصنمين',
    'As-Suqaylabiyah': 'السقيلبية',
    'As-Sweida': 'السويداء',
    'At Tall': 'التل',
    'Ath-Thawrah': 'الثورة',
    'Az-Zabdani': 'الزبداني',
    'Banyas': 'بانياس',
    'Damascus': 'دمشق',
    "Dar'a": 'درعا',
    'Darayya': 'داريا',
    'Deir-ez-Zor': 'دير الزور',
    'Dreikish': 'دريكيش',
    'Duma': 'دوما',
    'Hama': 'حماة',
    'Harim': 'حارم',
    'Homs': 'حمص',
    'Idleb': 'إدلب',
    "Izra'": 'إزرع',
    'Jablah': 'جبلة',
    'Jarablus': 'جرابلس',
    'Jebel Saman': 'جبل سمعان',
    'Jisr-Ash-Shugur': 'جسر الشغور',
    'Lattakia': 'اللاذقية',
    'Masyaf': 'مصياف',
    'Menbij': 'منبج',
    'Muhradah': 'محردة',
    'Qadmous': 'القدموس',
    'Qatana': 'قطنة',
    'Quamishli': 'القامشلي',
    'Quneitra': 'القنيطرة',
    'Ras Al Ain': 'رأس العين',
    'Rural Damascus': 'ريف دمشق',
    'Safita': 'صافيتا',
    'Salkhad': 'صلخد',
    'Shahba': 'شهبا',
    'Sheikh Badr': 'الشيخ بدر',
    'Tadmor': 'تدمر',
    'Tall Kalakh': 'تل كلخ',
    'Tartous': 'طرطوس',
    'Tell Abiad': 'تل أبيض',
    'Yabroud': 'يبرود',
}

SUBDISTRICT_OVERRIDES: dict[str, str] = {}


def translate_governorate(name_en: str) -> str:
    return GOVERNORATE_AR.get(name_en.strip(), name_en.strip())


def translate_district(name_en: str) -> str:
    return DISTRICT_AR.get(name_en.strip(), name_en.strip())


def translate_subdistrict(name_en: str) -> str:
    key = name_en.strip()
    if key in SUBDISTRICT_OVERRIDES:
        return SUBDISTRICT_OVERRIDES[key]
    if key in DISTRICT_AR:
        return DISTRICT_AR[key]
    return _normalize_subdistrict_name(key)


def _normalize_subdistrict_name(name_en: str) -> str:
    normalized = name_en.strip()
    for prefix, arabic_prefix in (
        ("Al-", "ال"),
        ("As-", "ال"),
        ("Ar-", "ال"),
        ("An-", "ال"),
        ("At-", "ال"),
        ("Az-", "ال"),
        ("Abu ", "أبو "),
        ("Ain ", "عين "),
        ("Tell ", "تل "),
        ("Jebel ", "جبل "),
    ):
        if normalized.startswith(prefix):
            return f"{arabic_prefix}{normalized[len(prefix):]}"
    return normalized
