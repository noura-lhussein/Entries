"""Budget / project-flow domain models."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from .codes import (
    budget_code,
    next_budget_letter_index,
    next_project_index,
    project_code,
    project_code_prefix,
)


def _has_parent_cycle(instance, parent_attr: str = "parent") -> bool:
    """Return True if a self-referencing parent chain loops back to instance."""
    instance_pk = instance.pk
    if not instance_pk:
        return False

    seen: set[int] = set()
    parent = getattr(instance, parent_attr)
    while parent is not None:
        if parent.pk == instance_pk or parent.pk in seen:
            return True
        seen.add(parent.pk)
        parent = getattr(parent, parent_attr)
    return False


class AuditFieldsMixin(models.Model):
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
    )

    class Meta:
        abstract = True


class ProjectCategory(AuditFieldsMixin):
    """Single tree of project categories; replaces separate category/sub-category tables."""

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    code = models.CharField(max_length=20, blank=True,
                            default="", db_index=True)
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name_plural = "project categories"

    def clean(self):
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                {"parent": "لا يمكن أن تكون الفئة تابعة لنفسها."})
        if _has_parent_cycle(self):
            raise ValidationError(
                {"parent": "لا يمكن إنشاء حلقة داخل شجرة الفئات."})

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        child_count = self.children.filter(deleted=False).count()
        if child_count:
            blockers.append(f"فئات فرعية ({child_count})")
        milestone_count = self.milestones.filter(deleted=False).count()
        if milestone_count:
            blockers.append(f"بنود ({milestone_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "الفئة")

    def __str__(self):
        return self.name_ar


class Foundation(AuditFieldsMixin):
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        project_count = self.projects.filter(deleted=False).count()
        if project_count:
            blockers.append(f"مشاريع ({project_count})")
        responsible_count = self.responsibles.filter(deleted=False).count()
        if responsible_count:
            blockers.append(f"مسؤولين ({responsible_count})")
        budget_user_count = self.budget_users.count()
        if budget_user_count:
            blockers.append(f"مستخدمي ميزانية ({budget_user_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "المؤسسة")

    def __str__(self):
        return self.name_ar


class BudgetUserScope(models.Model):
    """Links an auth user to exactly one foundation for project-budget data scope."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budget_scope",
    )
    foundation = models.ForeignKey(
        Foundation,
        on_delete=models.PROTECT,
        related_name="budget_users",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.user} → {self.foundation}"


class ProjectUserAssignment(models.Model):
    """Links a budget user to a project within the same foundation."""

    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="user_assignments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_assignments_made",
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="project_budget_unique_project_user_assignment",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        scope = getattr(self.user, "budget_scope", None)
        if scope is None:
            raise ValidationError(
                {"user": "المستخدم يجب أن يكون مرتبطاً بمؤسسة ميزانية."}
            )
        if self.project.foundation_id != scope.foundation_id:
            raise ValidationError(
                {"user": "المستخدم والمشروع يجب أن يكونا في نفس المؤسسة."}
            )

    def __str__(self):
        return f"{self.user} → {self.project}"


class Responsible(AuditFieldsMixin):
    foundation = models.ForeignKey(
        Foundation,
        on_delete=models.PROTECT,
        related_name="responsibles",
    )
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        milestone_count = self.milestones.filter(deleted=False).count()
        if milestone_count:
            blockers.append(f"بنود جزئية ({milestone_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "المسؤول")

    def __str__(self):
        return self.name_ar


class ProjectType(AuditFieldsMixin):
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        budget_count = self.annual_budgets.count()
        if budget_count:
            blockers.append(f"ميزانيات سنوية ({budget_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "نوع المشروع")

    def __str__(self):
        return self.name_ar


class Currency(AuditFieldsMixin):
    code = models.CharField(max_length=10, unique=True)
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True, default="")
    symbol = models.CharField(max_length=10, blank=True, default="")
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=1)

    class Meta:
        ordering = ["code", "name_ar", "id"]
        verbose_name_plural = "currencies"

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        budget_count = self.annual_budgets.count()
        if budget_count:
            blockers.append(f"ميزانيات سنوية ({budget_count})")
        project_txn_count = self.project_transactions.count()
        if project_txn_count:
            blockers.append(f"حركات مشاريع ({project_txn_count})")
        milestone_txn_count = self.milestone_transactions.count()
        if milestone_txn_count:
            blockers.append(f"حركات بنود ({milestone_txn_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "العملة")

    def __str__(self):
        return self.code


class AnnualBudget(models.Model):
    """Approved budget for one project type in one year."""

    project_type = models.ForeignKey(
        ProjectType,
        on_delete=models.PROTECT,
        related_name="annual_budgets",
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="annual_budgets",
    )
    year = models.PositiveIntegerField()
    code = models.CharField(max_length=20, unique=True, blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True, default="")
    approved_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_budget_annualbudgets_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_budget_annualbudgets_updated",
    )

    class Meta:
        ordering = ["-year", "project_type_id", "id"]
        unique_together = ("project_type", "year")

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        project_count = self.projects.filter(deleted=False).count()
        if project_count:
            blockers.append(f"مشاريع ({project_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "الميزانية السنوية")

    def build_code(self) -> str:
        existing_codes = list(
            AnnualBudget.objects.filter(year=self.year)
            .exclude(pk=self.pk)
            .values_list("code", flat=True)
        )
        letter_index = next_budget_letter_index(self.year, existing_codes)
        if letter_index > 25:
            raise ValidationError(
                {"code": "لا يمكن إنشاء أكثر من 26 موازنة سنوية لنفس السنة."})
        return budget_code(self.year, letter_index)

    def save(self, *args, **kwargs):
        if not self.code and self.year and self.project_type_id:
            self.code = self.build_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_type} - {self.year} ({self.amount} {self.currency.code})"


class Project(AuditFieldsMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On hold"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    annual_budget = models.ForeignKey(
        AnnualBudget,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    foundation = models.ForeignKey(
        Foundation,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    governorate = models.ForeignKey(
        "locations.Governorate",
        on_delete=models.PROTECT,
        related_name="budget_projects",
    )
    district = models.ForeignKey(
        "locations.District",
        on_delete=models.PROTECT,
        related_name="budget_projects",
    )
    subdistrict = models.ForeignKey(
        "locations.SubDistrict",
        on_delete=models.PROTECT,
        related_name="budget_projects",
    )
    community = models.ForeignKey(
        "locations.Community",
        on_delete=models.PROTECT,
        related_name="budget_projects",
    )
    previous_project = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renewed_projects",
    )
    target = models.ForeignKey(
        "Target",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="projects",
    )
    policy = models.ForeignKey(
        "Policy",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="projects",
    )
    quantitative_target_value = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )
    quantitative_target_unit = models.ForeignKey(
        "MeasureUnit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="projects",
    )
    is_round = models.BooleanField(default=False)
    code = models.CharField(max_length=50, unique=True, blank=True, default="")
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    latitude = models.DecimalField(
        max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True)
    percentage_completion = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    completion_is_manual = models.BooleanField(default=False)
    proposed_budget = models.DecimalField(
        max_digits=14, decimal_places=2, default=0)
    approved_budget = models.DecimalField(
        max_digits=14, decimal_places=2, default=0)
    budget_expenditure = models.DecimalField(
        max_digits=14, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT)
    description = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-created_at", "id"]

    @property
    def project_type(self):
        return self.annual_budget.project_type

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        milestone_count = self.milestones.filter(deleted=False).count()
        if milestone_count:
            blockers.append(f"بنود جزئية ({milestone_count})")
        project_txn_count = self.project_transactions.count()
        if project_txn_count:
            blockers.append(f"حركات مشاريع ({project_txn_count})")
        renewed_count = self.renewed_projects.filter(deleted=False).count()
        if renewed_count:
            blockers.append(f"مشاريع مرتبطة ({renewed_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "المشروع")

    def allocate_code(self) -> str:
        from locations.models import Community

        with transaction.atomic():
            budget = AnnualBudget.objects.select_for_update().get(
                pk=self.annual_budget_id)
            if not budget.code:
                budget.save()
            community = Community.objects.select_related("subdistrict").get(
                pk=self.community_id)
            subdistrict_code = (community.subdistrict.code or "").strip()
            community_code = (community.code or "").strip()
            if not subdistrict_code or not community_code:
                raise ValidationError(
                    "لا يمكن توليد رمز المشروع بدون رموز OCHA للناحية والمجتمع.")
            prefix = project_code_prefix(
                budget.code, subdistrict_code, community_code)
            existing_codes = list(
                Project.objects.filter(
                    annual_budget_id=budget.id,
                    community_id=self.community_id,
                )
                .exclude(pk=self.pk)
                .values_list("code", flat=True)
            )
            next_index = next_project_index(existing_codes, prefix)
            return project_code(
                budget.code, subdistrict_code, community_code, next_index)

    def sync_location_from_community(self) -> None:
        if not self.community_id:
            return
        subdistrict = self.community.subdistrict
        district = subdistrict.district
        self.subdistrict_id = subdistrict.pk
        self.district_id = district.pk
        self.governorate_id = district.governorate_id

    def save(self, *args, **kwargs):
        if self.community_id:
            self.sync_location_from_community()
        if not self.code and self.annual_budget_id:
            self.code = self.allocate_code()
        super().save(*args, **kwargs)

    def recalculate_completion(self) -> None:
        from .completion import update_project_completion

        update_project_completion(self.pk)

    def clean(self):
        super().clean()
        if self.previous_project_id and self.previous_project_id == self.pk:
            raise ValidationError(
                {"previous_project": "لا يمكن ربط المشروع بنفسه."})
        if self.previous_project_id and self.annual_budget_id:
            previous = (
                Project.objects.select_related("annual_budget")
                .filter(pk=self.previous_project_id)
                .first()
            )
            current_year = getattr(self.annual_budget, "year", None)
            if current_year is None:
                current_year = (
                    AnnualBudget.objects.filter(pk=self.annual_budget_id)
                    .values_list("year", flat=True)
                    .first()
                )
            if (
                previous
                and current_year is not None
                and previous.annual_budget.year >= current_year
            ):
                raise ValidationError(
                    {
                        "previous_project": (
                            "المشروع السابق يجب أن يكون من سنة سابقة على الأقل."
                        )
                    }
                )
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "تاريخ النهاية يجب أن يكون بعد تاريخ البداية."})
        if self.percentage_completion < 0 or self.percentage_completion > 100:
            raise ValidationError(
                {"percentage_completion": "نسبة الإنجاز يجب أن تكون بين 0 و 100."})
        has_qt_value = self.quantitative_target_value is not None
        has_qt_unit = self.quantitative_target_unit_id is not None
        if has_qt_value != has_qt_unit:
            raise ValidationError(
                {
                    "quantitative_target_value": (
                        "يجب إدخال قيمة المستهدف الكمي ووحدته معاً."
                    )
                }
            )
        if (
            self.quantitative_target_value is not None
            and self.quantitative_target_value < 0
        ):
            raise ValidationError(
                {"quantitative_target_value": "المستهدف الكمي يجب أن يكون صفراً أو أكبر."}
            )

    def __str__(self):
        return self.name_ar or self.code


class MeasureUnit(AuditFieldsMixin):
    """Reference table of measurement units for quantitative project targets."""

    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    symbol = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name = "measure unit"
        verbose_name_plural = "measure units"

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        project_count = self.projects.filter(deleted=False).count()
        if project_count:
            blockers.append(f"مشاريع ({project_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "وحدة القياس")

    def __str__(self):
        return self.name_ar or f"MeasureUnit #{self.pk}"


class Milestone(AuditFieldsMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On hold"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="milestones")
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    responsible = models.ForeignKey(
        Responsible,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestones",
    )
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="milestones",
    )
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    latitude = models.DecimalField(
        max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True)
    percentage_completion = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["order", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        child_count = self.children.filter(deleted=False).count()
        if child_count:
            blockers.append(f"بنود فرعية ({child_count})")
        txn_count = self.milestone_transactions.count()
        if txn_count:
            blockers.append(f"حركات بنود ({txn_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "البند")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.project_id:
            from .completion import update_project_completion

            update_project_completion(self.project_id)

    def clean(self):
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(
                {"parent": "لا يمكن أن يكون البند تابعاً لنفسه."})
        if self.parent_id and self.parent.project_id != self.project_id:
            raise ValidationError(
                {"parent": "البند الأب يجب أن يكون من نفس المشروع."})
        if _has_parent_cycle(self):
            raise ValidationError(
                {"parent": "لا يمكن إنشاء حلقة داخل شجرة البنود."})
        if (
            self.responsible_id
            and self.project_id
            and self.responsible.foundation_id != self.project.foundation_id
        ):
            raise ValidationError(
                {"responsible": "المسؤول يجب أن يتبع نفس مؤسسة المشروع."})
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "تاريخ النهاية يجب أن يكون بعد تاريخ البداية."})
        if self.percentage_completion < 0 or self.percentage_completion > 100:
            raise ValidationError(
                {"percentage_completion": "نسبة الإنجاز يجب أن تكون بين 0 و 100."})

    def __str__(self):
        return self.name_ar


class Transaction(AuditFieldsMixin):
    """Reference transaction type."""

    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    disabled = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def __str__(self):
        return self.name_ar


class ProjectTransaction(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_transactions")
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="project_transactions",
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="project_transactions",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, default="")
    transaction_date = models.DateField()
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_budget_projecttransactions_created",
    )

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return self.reference or f"Project txn #{self.pk}"


class MilestoneTransaction(models.Model):
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name="milestone_transactions",
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="milestone_transactions",
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="milestone_transactions",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, default="")
    transaction_date = models.DateField()
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_budget_milestonetransactions_created",
    )

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return self.reference or f"Milestone txn #{self.pk}"


class Target(AuditFieldsMixin):
    """Reference table of project targets (managed like categories)."""

    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        project_count = self.projects.filter(deleted=False).count()
        if project_count:
            blockers.append(f"مشاريع ({project_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "الهدف")

    def __str__(self):
        return self.name_ar or f"Target #{self.pk}"


class Policy(AuditFieldsMixin):
    """Reference table of project policies (managed like categories)."""

    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name_ar", "id"]

    def deletion_blockers(self) -> list[str]:
        blockers: list[str] = []
        project_count = self.projects.filter(deleted=False).count()
        if project_count:
            blockers.append(f"مشاريع ({project_count})")
        return blockers

    def assert_can_delete(self) -> None:
        from .protected_delete import raise_if_blocked

        raise_if_blocked(self.deletion_blockers(), "السياسة")

    def __str__(self):
        return self.name_ar or f"Policy #{self.pk}"


class ProjectChangeLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    batch_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=10, choices=Action.choices)
    field_name = models.CharField(max_length=64)
    field_label = models.CharField(max_length=128)
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_change_logs",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    client_latitude = models.DecimalField(
        max_digits=10, decimal_places=8, null=True, blank=True
    )
    client_longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    user_agent = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["-changed_at", "-id"]
        indexes = [
            models.Index(fields=["project", "-changed_at"]),
        ]

    def __str__(self):
        return f"{self.project_id} · {self.field_label} · {self.changed_at}"
