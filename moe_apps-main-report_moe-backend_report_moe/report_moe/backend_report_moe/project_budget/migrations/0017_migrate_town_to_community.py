import uuid

from django.db import migrations


def _norm(value: str) -> str:
    return (value or "").strip().casefold()


def _match_governorate(Governorate, old_city_name: str):
    key = _norm(old_city_name)
    if not key:
        return None
    for gov in Governorate.objects.all():
        if key in (_norm(gov.name_ar), _norm(gov.name_en)):
            return gov
        if key in _norm(gov.name_ar) or key in _norm(gov.name_en):
            return gov
    for gov in Governorate.objects.all():
        for candidate in (_norm(gov.name_ar), _norm(gov.name_en)):
            if candidate and (candidate in key or key in candidate):
                return gov
    return None


def _match_district(District, governorate_id: int, old_district_name: str):
    key = _norm(old_district_name)
    qs = District.objects.filter(governorate_id=governorate_id)
    for dist in qs:
        if key in (_norm(dist.name_ar), _norm(dist.name_en)):
            return dist
    for dist in qs:
        for candidate in (_norm(dist.name_ar), _norm(dist.name_en)):
            if candidate and (candidate in key or key in candidate):
                return dist
    return qs.first()


def _default_subdistrict(SubDistrict, district):
    code = f"{district.code}-DEFAULT"
    sub, _created = SubDistrict.objects.get_or_create(
        code=code,
        defaults={
            "district": district,
            "uid": uuid.uuid4(),
            "name_ar": "ناحية عامة",
            "name_en": "General",
            "is_active": True,
        },
    )
    return sub


def migrate_towns_forward(apps, schema_editor):
    Town = apps.get_model("project_budget", "Town")
    Project = apps.get_model("project_budget", "Project")
    Governorate = apps.get_model("locations", "Governorate")
    District = apps.get_model("locations", "District")
    SubDistrict = apps.get_model("locations", "SubDistrict")
    Community = apps.get_model("locations", "Community")

    default_subdistricts: dict[int, object] = {}
    town_communities: dict[int, int] = {}

    for town in Town.objects.filter(deleted=False).select_related("district"):
        dist = town.district
        if dist is None:
            continue
        # Legacy dynamic_forms.District had .city and .name; locations.District uses name_ar/en + governorate.
        old_city_name = ""
        if hasattr(dist, "city_id") and dist.city_id:
            old_city_name = getattr(dist.city, "name", "") or ""
        elif getattr(dist, "governorate_id", None):
            gov = dist.governorate
            old_city_name = getattr(gov, "name_ar", "") or getattr(gov, "name_en", "") or ""
        old_district_name = (
            getattr(dist, "name", None)
            or getattr(dist, "name_ar", None)
            or getattr(dist, "name_en", None)
            or ""
        )
        governorate = _match_governorate(Governorate, old_city_name)
        if governorate is None and getattr(dist, "governorate_id", None):
            governorate = dist.governorate
        if governorate is None:
            governorate = Governorate.objects.order_by("id").first()
        if governorate is None:
            continue

        district = _match_district(District, governorate.id, old_district_name)
        if district is None:
            district = District.objects.filter(
                governorate_id=governorate.id).first()
        if district is None:
            continue

        if district.id not in default_subdistricts:
            default_subdistricts[district.id] = _default_subdistrict(
                SubDistrict, district)

        subdistrict = default_subdistricts[district.id]
        community_code = f"TOWN-{town.id}"
        community, _created = Community.objects.get_or_create(
            code=community_code,
            defaults={
                "subdistrict": subdistrict,
                "name_ar": town.name_ar or town.name_en or f"Town {town.id}",
                "name_en": town.name_en or "",
                "is_active": True,
            },
        )
        town_communities[town.id] = community.id

    for project in Project.objects.filter(deleted=False, town_id__isnull=False):
        community_id = town_communities.get(project.town_id)
        if not community_id:
            continue
        community = Community.objects.select_related(
            "subdistrict__district__governorate"
        ).get(pk=community_id)
        project.community_id = community_id
        project.subdistrict_id = community.subdistrict_id
        project.district_id = community.subdistrict.district_id
        project.governorate_id = community.subdistrict.district.governorate_id
        project.save(
            update_fields=[
                "community_id",
                "subdistrict_id",
                "district_id",
                "governorate_id",
            ]
        )


def migrate_towns_backward(apps, schema_editor):
    Project = apps.get_model("project_budget", "Project")
    Project.objects.update(
        community_id=None,
        subdistrict_id=None,
        district_id=None,
        governorate_id=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0001_initial"),
        ("project_budget", "0016_project_location_fks"),
    ]

    operations = [
        migrations.RunPython(migrate_towns_forward, migrate_towns_backward),
    ]
