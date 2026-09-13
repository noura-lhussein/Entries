from django.db import migrations


def _norm(value: str) -> str:
    return (value or "").strip().casefold()


def _match_by_name(candidates, raw: str):
    key = _norm(raw)
    if not key:
        return None
    for item in candidates:
        names = (_norm(getattr(item, "name_ar", "")),
                 _norm(getattr(item, "name_en", "")))
        if key in names:
            return item
    for item in candidates:
        for candidate in (_norm(getattr(item, "name_ar", "")), _norm(getattr(item, "name_en", ""))):
            if candidate and (candidate in key or key in candidate):
                return item
    return None


def backfill_location_district_forward(apps, schema_editor):
    SubMainSection = apps.get_model("dynamic_forms", "SubMainSection")
    LegacyDistrict = apps.get_model("dynamic_forms", "District")
    LegacyCity = apps.get_model("dynamic_forms", "City")
    LocationDistrict = apps.get_model("locations", "District")
    Governorate = apps.get_model("locations", "Governorate")

    for sub in SubMainSection.objects.filter(
        location_district_id__isnull=True,
        district_id__isnull=False,
    ):
        legacy = LegacyDistrict.objects.filter(pk=sub.district_id).first()
        if legacy is None:
            continue
        city_name = ""
        if legacy.city_id:
            city_name = (
                LegacyCity.objects.filter(pk=legacy.city_id)
                .values_list("name", flat=True)
                .first()
                or ""
            )
        gov = _match_by_name(Governorate.objects.all(), city_name)
        dist_qs = LocationDistrict.objects.all()
        if gov:
            dist_qs = dist_qs.filter(governorate_id=gov.id)
        match = _match_by_name(dist_qs, legacy.name)
        if match is None:
            match = _match_by_name(LocationDistrict.objects.all(), legacy.name)
        if match:
            sub.location_district_id = match.id
            sub.save(update_fields=["location_district_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0013_migrate_info_locations"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            backfill_location_district_forward,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="submainsection",
            name="district",
        ),
    ]
