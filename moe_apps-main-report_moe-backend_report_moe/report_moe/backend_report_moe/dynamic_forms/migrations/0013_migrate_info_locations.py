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


def _display_name(obj) -> str:
    return (getattr(obj, "name_ar", None) or getattr(obj, "name_en", None) or "").strip()


def migrate_info_locations_forward(apps, schema_editor):
    Info = apps.get_model("dynamic_forms", "Info")
    Attribute = apps.get_model("dynamic_forms", "Attribute")
    Governorate = apps.get_model("locations", "Governorate")
    District = apps.get_model("locations", "District")
    SubDistrict = apps.get_model("locations", "SubDistrict")
    Community = apps.get_model("locations", "Community")

    location_types = {"city", "district", "sub_district", "community"}
    attrs_by_id = {
        row.id: row.type
        for row in Attribute.objects.filter(type__in=location_types).only("id", "type")
    }
    if not attrs_by_id:
        return

    rows_by_key: dict[str | None, list] = {}
    qs = (
        Info.objects.filter(attribute_id__in=attrs_by_id.keys())
        .select_related("sub_main", "sub_main__location_district")
        .order_by("row_key", "id")
    )
    for info in qs.iterator(chunk_size=500):
        rows_by_key.setdefault(info.row_key, []).append(info)

    for infos in rows_by_key.values():
        context = {"governorate_id": None,
                   "district_id": None, "subdistrict_id": None}
        if infos and infos[0].sub_main_id:
            sub = infos[0].sub_main
            if sub.location_district_id:
                dist = District.objects.filter(
                    pk=sub.location_district_id).first()
                if dist:
                    context["governorate_id"] = dist.governorate_id

        type_order = {"city": 0, "district": 1,
                      "sub_district": 2, "community": 3}
        infos.sort(key=lambda row: type_order.get(
            attrs_by_id.get(row.attribute_id, ""), 99))

        for info in infos:
            attr_type = attrs_by_id.get(info.attribute_id)
            if not attr_type:
                continue
            raw = info.value or ""
            parsed_id = int(raw) if str(raw).strip().isdigit() else None

            if attr_type == "city":
                gov = Governorate.objects.filter(
                    pk=parsed_id).first() if parsed_id else None
                if gov is None:
                    gov = _match_by_name(Governorate.objects.all(), raw)
                if gov:
                    info.loc_governorate_id = gov.id
                    info.value = _display_name(gov) or raw
                    context["governorate_id"] = gov.id
                    info.save(update_fields=["loc_governorate_id", "value"])
                continue

            if attr_type == "district":
                dist_qs = District.objects.all()
                if context["governorate_id"]:
                    dist_qs = dist_qs.filter(
                        governorate_id=context["governorate_id"])
                dist = dist_qs.filter(
                    pk=parsed_id).first() if parsed_id else None
                if dist is None:
                    dist = _match_by_name(dist_qs, raw)
                if dist is None:
                    dist = _match_by_name(District.objects.all(), raw)
                if dist:
                    info.loc_district_id = dist.id
                    info.loc_governorate_id = dist.governorate_id
                    info.value = _display_name(dist) or raw
                    context["district_id"] = dist.id
                    context["governorate_id"] = dist.governorate_id
                    info.save(
                        update_fields=["loc_district_id",
                                       "loc_governorate_id", "value"]
                    )
                continue

            if attr_type == "sub_district":
                sub_qs = SubDistrict.objects.all()
                if context["district_id"]:
                    sub_qs = sub_qs.filter(district_id=context["district_id"])
                sub = sub_qs.filter(
                    pk=parsed_id).first() if parsed_id else None
                if sub is None:
                    sub = _match_by_name(sub_qs, raw)
                if sub:
                    info.loc_subdistrict_id = sub.id
                    info.loc_district_id = sub.district_id
                    parent_dist = District.objects.filter(
                        pk=sub.district_id).first()
                    if parent_dist:
                        info.loc_governorate_id = parent_dist.governorate_id
                    info.value = _display_name(sub) or raw
                    context["subdistrict_id"] = sub.id
                    context["district_id"] = sub.district_id
                    info.save(
                        update_fields=[
                            "loc_subdistrict_id",
                            "loc_district_id",
                            "loc_governorate_id",
                            "value",
                        ]
                    )
                continue

            if attr_type == "community":
                comm_qs = Community.objects.all()
                if context["subdistrict_id"]:
                    comm_qs = comm_qs.filter(
                        subdistrict_id=context["subdistrict_id"])
                comm = comm_qs.filter(
                    pk=parsed_id).first() if parsed_id else None
                if comm is None:
                    comm = _match_by_name(comm_qs, raw)
                if comm:
                    info.loc_community_id = comm.id
                    info.loc_subdistrict_id = comm.subdistrict_id
                    parent_sub = SubDistrict.objects.filter(
                        pk=comm.subdistrict_id).first()
                    if parent_sub:
                        info.loc_district_id = parent_sub.district_id
                        parent_dist = District.objects.filter(
                            pk=parent_sub.district_id).first()
                        if parent_dist:
                            info.loc_governorate_id = parent_dist.governorate_id
                    info.value = _display_name(comm) or raw
                    info.save(
                        update_fields=[
                            "loc_community_id",
                            "loc_subdistrict_id",
                            "loc_district_id",
                            "loc_governorate_id",
                            "value",
                        ]
                    )


def migrate_submain_districts_forward(apps, schema_editor):
    SubMainSection = apps.get_model("dynamic_forms", "SubMainSection")
    LegacyDistrict = apps.get_model("dynamic_forms", "District")
    LegacyCity = apps.get_model("dynamic_forms", "City")
    LocationDistrict = apps.get_model("locations", "District")
    Governorate = apps.get_model("locations", "Governorate")

    for sub in SubMainSection.objects.filter(district_id__isnull=False):
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


def migrate_locations_backward(apps, schema_editor):
    Info = apps.get_model("dynamic_forms", "Info")
    SubMainSection = apps.get_model("dynamic_forms", "SubMainSection")
    Info.objects.update(
        loc_governorate_id=None,
        loc_district_id=None,
        loc_subdistrict_id=None,
        loc_community_id=None,
    )
    SubMainSection.objects.update(location_district_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0012_info_location_fks"),
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_info_locations_forward,
                             migrate_locations_backward),
        migrations.RunPython(
            migrate_submain_districts_forward, migrations.RunPython.noop),
    ]
