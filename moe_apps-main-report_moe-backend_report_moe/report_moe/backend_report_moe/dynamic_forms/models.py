from django.conf import settings
from django.db import models

# AUTH_USER_MODEL is accounts.User (shared with moeds).


class SoftDeleteFieldsMixin(models.Model):
    """Soft-delete flags shared by structure models (Title / sections)."""

    deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
    )

    class Meta:
        abstract = True


class TitleCategory(models.Model):
    """Admin-managed free category for grouping Titles and assigning users."""

    name = models.CharField(max_length=255, unique=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "title categories"

    def __str__(self):
        return self.name


class Title(SoftDeleteFieldsMixin):
    name = models.CharField(max_length=255)
    # Stable, ASCII, machine identifier a consumer (moeds) can rely on. `name` is
    # free-text Arabic and may be renamed at any time — never match on `name`.
    # Blank only for titles no external consumer reads yet.
    code = models.CharField(max_length=128, blank=True, default='')
    # Display order is scoped per category (same numbers allowed across categories).
    order = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(
        TitleCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="titles",
    )
    subtitle = models.CharField(max_length=255, blank=True, default='')
    # Entry UX: single_record | multi_record (metadata-driven; no per-title UI code).
    entry_mode = models.CharField(max_length=32, default='single_record')
    # [{id, title_ar, order, collapsed_by_default}]
    field_groups = models.JSONField(default=list, blank=True)
    # Attribute labels (or keys) shown as primary columns in previous-records table.
    preview_field_keys = models.JSONField(default=list, blank=True)
    # Set by seed_*_info_forms commands. Blocks delete and code changes from the
    # admin UI (structure_serializers.py) — display fields (name, subtitle, order,
    # field_groups) stay fully editable. Seeded rows are protected from edits for
    # the same "protect the machine contract, keep the human-facing parts free"
    # pattern applied to table ownership instead of form structure.
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ["category_id", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=~models.Q(code=""),
                name="dynamic_forms_title_code_unique",
            ),
        ]

    def __str__(self):
        return self.name


class MainSection(SoftDeleteFieldsMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SubMainSection(SoftDeleteFieldsMixin):
    main_section = models.ForeignKey(
        MainSection, on_delete=models.CASCADE, related_name='sub_sections')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    location_district = models.ForeignKey(
        'locations.District',
        on_delete=models.SET_NULL,
        related_name='report_sub_sections',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return self.name

    @property
    def is_leaf(self) -> bool:
        return not self.children.filter(deleted=False).exists()

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError(
                    {'parent': 'لا يمكن أن يكون القسم الفرعي أباً لنفسه.'})
            if self.parent.main_section_id != self.main_section_id:
                raise ValidationError(
                    {'parent': 'الأب يجب أن يكون ضمن نفس القسم الرئيسي.'})
            # Walk ancestors to detect cycles when updating.
            seen: set[int] = set()
            node = self.parent
            while node is not None:
                if self.pk and node.pk == self.pk:
                    raise ValidationError(
                        {'parent': 'لا يمكن إنشاء حلقة في شجرة الأقسام.'})
                if node.pk in seen:
                    break
                seen.add(node.pk)
                node = node.parent


class UserSubMain(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_sub_mains')
    sub_main = models.ForeignKey(
        SubMainSection, on_delete=models.CASCADE, related_name='user_sub_mains')

    def __str__(self):
        return f"{self.user} - {self.sub_main}"


class UserTitle(models.Model):
    """Per-title assignment (optional subset within UserTitleCategory)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_titles')
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='user_titles')

    def __str__(self):
        return f"{self.user} - {self.title}"


class UserTitleCategory(models.Model):
    """Assign a whole TitleCategory to a user (all titles in that category)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_title_categories',
    )
    category = models.ForeignKey(
        TitleCategory,
        on_delete=models.CASCADE,
        related_name='user_assignments',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category'],
                name='dynamic_forms_unique_user_title_category',
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.category}"


# ── Dynamic Form Builder ──────────────────────────────────────────────────────

class Attribute(models.Model):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='attributes', null=True, blank=True)
    label = models.CharField(max_length=255)

    TYPE_CHOICES = [
        ('text',     'Text'),
        ('textarea', 'Text Area'),
        ('number',   'Number'),
        ('date',     'Date'),
        ('boolean',  'Boolean/Checkbox'),
        ('select',   'Dropdown'),
        ('city',         'City / Governorate'),
        ('district',     'District'),
        ('sub_district', 'Sub-district'),
        ('community',    'Community'),
        ('image',    'Image upload'),
        ('file',     'File upload'),
        # Entity pickers (dropdown from master tables / GIS in moeds schema)
        ('drinking_station', 'Drinking water station'),
        ('dam', 'Dam'),
        ('rainfall_station', 'Rainfall station'),
        ('rainfall_basin', 'Rainfall basin'),
        ('spring', 'Spring'),
        ('lake', 'Lake'),
        ('river', 'River'),
        ('stream', 'Stream'),
        ('geology_unit', 'Geology unit'),
        ('ore_product', 'Ore product'),
        ('power_plant', 'Power plant'),
        ('substation', 'Substation'),
        ('transmission_line', 'Transmission line'),
        ('power_gis_substation_66', 'GIS substation 66 kV'),
        ('power_gis_substation_230', 'GIS substation 230 kV'),
        ('power_gis_substation_400', 'GIS substation 400 kV'),
        ('power_gis_renewable', 'Renewable energy site (GIS)'),
        ('fuel_tank_station', 'Fuel tank station'),
        ('hydro_dam', 'Hydro dam (daily report)'),
        ('load_governorate', 'Load governorate'),
        ('oil_field', 'Oil/gas field'),
        ('oil_well', 'Oil/gas well'),
        ('oil_refinery', 'Refinery'),
        ('fuel_station', 'Fuel station'),
        ('storage_depot', 'Storage depot'),
        ('pipeline', 'Pipeline'),
    ]
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    required = models.BooleanField(default=False)
    # Stable key for computed/warn refs (never shown in UI). Empty → use id as string.
    key = models.CharField(max_length=128, blank=True, default='')
    order = models.PositiveIntegerField(default=1)
    # Field group id matching Title.field_groups[].id; empty → «أخرى».
    group = models.CharField(max_length=64, blank=True, default='')
    unit_ar = models.CharField(max_length=64, blank=True, default='')
    help_ar = models.CharField(max_length=500, blank=True, default='')
    readonly = models.BooleanField(default=False)
    computed_from = models.CharField(max_length=255, blank=True, default='')
    min_value = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    max_field = models.CharField(max_length=128, blank=True, default='')
    warn_if_gt_field = models.CharField(max_length=128, blank=True, default='')
    message_ar = models.CharField(max_length=255, blank=True, default='')
    decimals = models.PositiveSmallIntegerField(null=True, blank=True)

    # ── Measure catalog (dashboard-metadata layer) ──────────────────────────
    # A "direct" dashboard measure needs zero moeds code to add: seed it here
    # with is_measure=True and moeds picks it up automatically. Computed/derived
    # indicators (ratios, trends, cross-entity aggregates) stay hand-written in
    # moeds — this only covers values that go straight from Info to a KPI card.
    is_measure = models.BooleanField(default=False, db_index=True)
    measure_order = models.PositiveIntegerField(default=1)
    label_en = models.CharField(max_length=255, blank=True, default='')
    unit_en = models.CharField(max_length=64, blank=True, default='')
    # ok | warning | critical threshold rule, interpreted by moeds' generic KPI
    # renderer (mirrors MetricSpec.kpi_status_rule). Free-form on purpose — this
    # is presentation logic, not something the contract check enforces.
    measure_status_rule = models.CharField(
        max_length=64, blank=True, default='')
    # Marks THE date that identifies one report of a daily-report title, so at most
    # one row may exist per (sub_main, date, entity). It cannot be inferred from the
    # label: "تسجيل حوادث التوليد" also calls its field تاريخ التقرير, yet several
    # incidents a day are legitimate. Off by default — event logs, targets and
    # alerts leave it off.
    is_report_date = models.BooleanField(default=False, db_index=True)

    # Same protection as Title.is_system: set by seed_*_info_forms commands,
    # blocks delete and key changes; label/order/group/unit_* stay free to edit.
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label} ({self.type})"

    @property
    def stable_key(self) -> str:
        return (self.key or '').strip() or str(self.pk)


class Option(models.Model):
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label


# ── Report Request Models ─────────────────────────────────────────────────────

class ReqReportSubMain(models.Model):
    """Groups report requests by sub-section."""
    sub_main = models.ForeignKey(SubMainSection, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.sub_main)


class ReqReport(models.Model):
    """A report request: sub-section, submitting user, and date range."""
    req_report_sub_main = models.ForeignKey(
        ReqReportSubMain, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.req_report_sub_main} ({self.date_from} → {self.date_to})"


class ReqReportTitle(models.Model):
    """Which titles are included in a report request."""
    req_report = models.ForeignKey(
        ReqReport, on_delete=models.CASCADE, related_name='report_titles')
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('req_report', 'title')

    def __str__(self):
        return f"{self.req_report} / {self.title}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN',   'Login'),
        ('LOGOUT',  'Logout'),
        ('CREATE',  'Create'),
        ('UPDATE',  'Update'),
        ('DELETE',  'Delete'),
        ('CONFIRM', 'Confirm'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} | {self.action} | {self.model_name} #{self.object_id}"


class Info(models.Model):
    """A single submitted field value — standalone, no FK to a specific report."""

    # No db_index: `dyn_info_rowkey_attr_idx` is (row_key, attribute_id), so
    # row_key is already its leading column and a standalone index only doubled
    # the write cost for 58 MB. (The standalone one also turned out to be
    # physically corrupt — "invalid page in block 737" — which is how it was
    # noticed; the heap was intact and it was rebuilt away rather than reindexed.)
    row_key = models.UUIDField(null=True, blank=True)

    class ConfirmStatus(models.TextChoices):
        WAITING = "waiting", "Waiting"
        ACCEPT = "accept", "Accept"
        REJECT = "reject", "Reject"

    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE, related_name='infos')
    sub_main = models.ForeignKey(
        SubMainSection, on_delete=models.CASCADE, related_name='infos', null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='infos')
    value = models.TextField()
    loc_governorate = models.ForeignKey(
        'locations.Governorate',
        on_delete=models.SET_NULL,
        related_name='report_infos',
        null=True,
        blank=True,
    )
    loc_district = models.ForeignKey(
        'locations.District',
        on_delete=models.SET_NULL,
        related_name='report_infos',
        null=True,
        blank=True,
    )
    loc_subdistrict = models.ForeignKey(
        'locations.SubDistrict',
        on_delete=models.SET_NULL,
        related_name='report_infos',
        null=True,
        blank=True,
    )
    loc_community = models.ForeignKey(
        'locations.Community',
        on_delete=models.SET_NULL,
        related_name='report_infos',
        null=True,
        blank=True,
    )
    confirmed = models.CharField(
        max_length=10,
        choices=ConfirmStatus.choices,
        default=ConfirmStatus.WAITING,
    )
    confirm_note = models.TextField(blank=True, default='')
    # Reviewer follow-up without changing confirmed (separate from confirm_note).
    commit_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    # Indexed link to master entity (set from entity-type attributes on save).
    entity_type = models.CharField(
        max_length=64, blank=True, default='', db_index=True)
    entity_id = models.PositiveBigIntegerField(
        null=True, blank=True, db_index=True)
    # Copy of Attribute.is_report_date. Denormalised because a UniqueConstraint
    # cannot reach across to the attribute table; kept in step by
    # `sync_info_report_date_flag` and asserted by `check_report_date_flags`.
    is_report_date = models.BooleanField(default=False, db_index=True)
    # Soft-archive when parent Title / SubMain / MainSection is deleted.
    archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archive_reason = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        indexes = [
            # Serves the moeds read hot-path: filter(confirmed=..., row_key__in=[...],
            # attribute_id__in=[...]) in `_facts_for_row_keys`-style helpers across
            # every sector's info_dashboard.py. Replaces the (row_key, sub_main)
            # index dropped in migration 0009, which served the same query shape.
            models.Index(
                fields=['row_key', 'attribute'],
                name='dyn_info_rowkey_attr_idx',
            ),
            models.Index(
                fields=['attribute', 'sub_main'],
                name='dynamic_for_attribu_453392_idx',
            ),
            models.Index(
                fields=['confirmed', 'sub_main'],
                name='dynamic_for_confirm_8a1f2d_idx',
            ),
            models.Index(
                fields=['user', 'confirmed'],
                name='dynamic_for_user_id_4c9e21_idx',
            ),
            models.Index(
                fields=['created_at'],
                name='dynamic_for_created_2b7f90_idx',
            ),
            models.Index(
                fields=['entity_type', 'entity_id', 'confirmed', 'created_at'],
                name='dynamic_for_entity_lookup_idx',
            ),
            models.Index(
                fields=['archived', 'created_at'],
                name='dyn_info_arch_created_idx',
            ),
            # Search / portal / duplicate-date paths (keep count low for write cost).
            models.Index(
                fields=['confirmed', 'attribute', '-created_at'],
                name='dyn_info_conf_attr_created_idx',
            ),
            models.Index(
                fields=['sub_main', 'confirmed', '-created_at'],
                name='dyn_info_sub_conf_created_idx',
            ),
            models.Index(
                fields=['attribute', 'sub_main', 'confirmed'],
                name='dyn_info_attr_sub_conf_idx',
            ),
            # Hot path for GET /info-rows/ keyset pagination (title → attributes).
            models.Index(
                fields=['attribute', 'confirmed', 'row_key', '-created_at'],
                name='dyn_info_rows_list_idx',
                condition=models.Q(archived=False, row_key__isnull=False),
            ),
            # Below: the live table is 99.99% confirmed='accept' and 100%
            # archived=False, so those columns carry no selectivity as index
            # KEYS. Pushed into partial WHERE clauses instead: the index covers
            # the same rows, stores two fewer columns, and the rare states get
            # their own tiny index rather than bloating the hot ones.
            models.Index(
                fields=['attribute', 'row_key'],
                name='dyn_info_hot_attr_rk',
                condition=models.Q(archived=False, confirmed='accept'),
            ),
            models.Index(
                fields=['attribute', '-created_at'],
                name='dyn_info_attr_created',
                condition=models.Q(archived=False, confirmed='accept'),
            ),
            models.Index(
                fields=['sub_main', '-created_at'],
                name='dyn_info_sub_created',
                condition=models.Q(archived=False, confirmed='accept'),
            ),
            # The review queue: 369 rows out of 2.7M, so this index is tiny and
            # answers "what still needs confirming" without touching the rest.
            models.Index(
                fields=['confirmed', 'attribute', '-created_at'],
                name='dyn_info_pending',
                condition=~models.Q(confirmed='accept'),
            ),
            # NOTE: a GIN trigram index on `value` (dyn_info_value_trgm) also
            # exists for the ILIKE '%…%' search paths. It is created by raw SQL
            # in migration 0029 because it needs gin_trgm_ops, which Django
            # cannot express without django.contrib.postgres in INSTALLED_APPS.
        ]
        constraints = [
            # One report per (sub_main, date, entity) for daily-report titles.
            # nulls_distinct=False is essential: national rows carry entity_id NULL,
            # and under the default NULLs-distinct rule they would never collide.
            models.UniqueConstraint(
                fields=[
                    'attribute', 'sub_main', 'value', 'entity_type', 'entity_id',
                ],
                condition=models.Q(
                    is_report_date=True,
                    archived=False,
                    confirmed__in=['waiting', 'accept'],
                ),
                nulls_distinct=False,
                name='dyn_info_report_date_unique',
            ),
            # One value per (attribute, logical row). Lets bulk loaders use
            # bulk_create(..., ignore_conflicts=True) for idempotency instead of
            # a per-row .exists() check — and catches the retried-migrate-command
            # double-insert bug dedupe_infos_by_row_key.py cleaned up before this
            # constraint was added (19,507 rows, all exact duplicates).
            # row_key is nullable (some legacy/no-row-group rows have none) —
            # NULL row_key values don't participate in a UNIQUE constraint's
            # duplicate check, so those rows are unaffected.
            models.UniqueConstraint(
                fields=['attribute', 'row_key'],
                name='dyn_info_attr_rowkey_unique',
            ),
        ]

    def save(self, *args, **kwargs):
        """Keep the denormalised report-date flag in step with the attribute.

        Seventeen management commands write Info through objects.create(); deriving
        the flag here covers all of them, so only bulk_create callers have to set it
        themselves. A targeted update_fields save is left alone -- the caller is
        changing named columns, and `sync_info_report_date_flag` repairs any drift.
        """
        if self.attribute_id and kwargs.get("update_fields") is None:
            cached = self._state.fields_cache.get("attribute")
            attribute = cached if cached is not None else self.attribute
            self.is_report_date = attribute.is_report_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.label}: {self.value}"


class InfoRow(models.Model):
    """One row per logical record — the shape every list and dashboard asks for.

    `Info` stores one row per *cell*: 2.7M rows that collapse to 669k records
    under `row_key`. Every screen paginates, counts and date-filters records, so
    each of those had to `GROUP BY row_key` over the cell table first, and
    `ORDER BY MAX(created_at)` is not something an index can answer — the records
    list spent 1.6 s aggregating 1.8M rows to return 20 of them.

    This table is that grouping, materialized. `report_date` is the other half of
    the win: the sector dashboards were range-scanning `Info.value` as *text*
    (`value >= '2026-01-01' AND value < '2026-02-01\\uffff'`), which no index can
    seek; here it is a real DATE column.

    READ-ONLY from Python. Every row is written by the PostgreSQL triggers in
    migration 0031 — that is the only mechanism that sees all 27 write paths into
    `Info`, including `bulk_create`, unbounded `.update()`, FK CASCADE deletes and
    the management commands, none of which go through `Info.save()` or any Django
    signal. `manage.py check_info_row_projection` asserts they agree.
    """

    row_key = models.UUIDField(primary_key=True)

    # db_constraint=False + DO_NOTHING: lifecycle belongs to the triggers, not to
    # Django's cascade machinery. A deleted Title cascades to Attribute, then to
    # Info, and the delete trigger drops the projection row from there.
    title = models.ForeignKey(
        Title, on_delete=models.DO_NOTHING, db_constraint=False,
        related_name="info_rows",
    )
    title_category_id = models.IntegerField(null=True, blank=True)
    sub_main = models.ForeignKey(
        SubMainSection, on_delete=models.DO_NOTHING, db_constraint=False,
        null=True, blank=True, related_name="info_rows",
    )
    main_section_id = models.IntegerField(null=True, blank=True)
    user_id = models.BigIntegerField(null=True, blank=True)

    first_created_at = models.DateTimeField()
    latest_created_at = models.DateTimeField()

    field_count = models.IntegerField(default=0)
    accepted_count = models.IntegerField(default=0)
    # True only when every cell in the record is accepted — what the dashboard
    # means by "a confirmed row".
    all_accepted = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    # Parsed from the cell whose attribute carries is_report_date. NULL for
    # titles that have no report-date field (and for unparseable values).
    report_date = models.DateField(null=True, blank=True)

    entity_type = models.CharField(max_length=64, blank=True, default="")
    entity_id = models.BigIntegerField(null=True, blank=True)

    loc_governorate_id = models.IntegerField(null=True, blank=True)
    loc_district_id = models.IntegerField(null=True, blank=True)
    loc_subdistrict_id = models.IntegerField(null=True, blank=True)
    loc_community_id = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            # The records list: filter by title, order by recency. Replaces the
            # GROUP BY + MAX(created_at) with a plain index range scan, and the
            # keyset cursor rides the same (latest_created_at, row_key) tuple.
            models.Index(
                fields=["title", "archived", "-latest_created_at", "-row_key"],
                name="dyn_inforow_list_idx",
            ),
            # Per-title logical-row counts (GET /infos/row-count/).
            models.Index(
                fields=["title"],
                name="dyn_inforow_title_idx",
                condition=models.Q(archived=False),
            ),
            # Sector dashboards: real date range instead of a text scan.
            models.Index(
                fields=["title", "-report_date"],
                name="dyn_inforow_title_date_idx",
            ),
            # Entity report-facts panels (~20 endpoints).
            models.Index(
                fields=["entity_type", "entity_id", "-report_date"],
                name="dyn_inforow_entity_idx",
                condition=~models.Q(entity_type=""),
            ),
            # Category-wide sector scope loads.
            models.Index(
                fields=["title_category_id", "-latest_created_at"],
                name="dyn_inforow_category_idx",
            ),
            models.Index(
                fields=["sub_main", "-latest_created_at"],
                name="dyn_inforow_submain_idx",
            ),
            # Admin dashboard confirmed/pending split.
            models.Index(
                fields=["archived"],
                name="dyn_inforow_accepted_idx",
                condition=models.Q(all_accepted=True),
            ),
        ]

    def __str__(self):
        return f"InfoRow {self.row_key} (title={self.title_id})"
