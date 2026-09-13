from __future__ import annotations

from django.db import models
from django.utils import timezone


class Sector(models.TextChoices):
    OIL_GAS = 'oil-gas', 'Petroleum'
    WATER = 'water-resources', 'Water Resources'
    ELECTRICITY = 'electricity', 'Electricity'
    MINERAL = 'mineral-resources', 'Mineral Resources'
    MULTI = 'multi-sector', 'Multi-sector'


class ProjectStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    PLANNED = 'planned', 'Planned'
    COMPLETED = 'completed', 'Completed'
    SUSPENDED = 'suspended', 'Suspended'


class ProjectGovernorate(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    pcode = models.CharField(max_length=16, blank=True)
    name_en = models.CharField(max_length=128)
    name_ar = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.name_en


class ProjectOrganization(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    slug = models.CharField(max_length=64)
    acronym = models.CharField(max_length=32, blank=True)
    name_en = models.CharField(max_length=255)
    governorate = models.ForeignKey(
        ProjectGovernorate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
    )

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return self.acronym or self.name_en

    @property
    def governorate_name_en(self) -> str:
        return self.governorate.name_en if self.governorate_id else ''

    @property
    def governorate_name_ar(self) -> str:
        return (self.governorate.name_ar or self.governorate.name_en) if self.governorate_id else ''


class DevelopmentProject(models.Model):
    code = models.CharField(max_length=32, unique=True)
    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    sector = models.CharField(max_length=32, db_index=True)
    status = models.CharField(max_length=16, default=ProjectStatus.ACTIVE)
    budget_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_spent_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    reporting_through = models.DateField(null=True, blank=True)
    start_year = models.PositiveSmallIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    governorate = models.ForeignKey(
        ProjectGovernorate,
        on_delete=models.PROTECT,
        related_name='projects',
    )
    organization = models.ForeignKey(
        ProjectOrganization,
        on_delete=models.PROTECT,
        related_name='projects',
    )
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='projects/logos/', blank=True, null=True)

    class Meta:
        ordering = ['code']
        db_table = 'projects_developmentproject'

    def __str__(self) -> str:
        return self.code

    @property
    def remaining_usd(self) -> float:
        return float(max(self.budget_usd - self.amount_spent_usd, 0))

    @property
    def utilization_pct(self) -> float:
        budget = float(self.budget_usd)
        if budget <= 0:
            return 0.0
        return round(float(self.amount_spent_usd) / budget * 100, 1)

    @property
    def sector_display(self) -> str:
        try:
            return Sector(self.sector).label
        except ValueError:
            return self.sector.replace('-', ' ').title()

    @property
    def status_display(self) -> str:
        try:
            return ProjectStatus(self.status).label
        except ValueError:
            return self.status.replace('-', ' ').title()

    @property
    def governorate_pcode(self) -> str:
        return self.governorate.pcode

    @property
    def governorate_name_en(self) -> str:
        return self.governorate.name_en

    @property
    def governorate_name_ar(self) -> str:
        return self.governorate.name_ar

    @property
    def organization_slug(self) -> str:
        return self.organization.slug

    @property
    def organization_acronym(self) -> str:
        return self.organization.acronym

    @property
    def organization_name_en(self) -> str:
        return self.organization.name_en


class MilestoneType(models.TextChoices):
    DELIVERABLE = 'deliverable', 'Deliverable'
    FINANCIAL = 'financial', 'Financial'
    PHYSICAL = 'physical', 'Physical'


class MilestoneStatus(models.TextChoices):
    PLANNED = 'planned', 'Planned'
    IN_PROGRESS = 'in_progress', 'In progress'
    COMPLETED = 'completed', 'Completed'
    DELAYED = 'delayed', 'Delayed'


class ActivityStatus(models.TextChoices):
    NOT_STARTED = 'not_started', 'Not started'
    IN_PROGRESS = 'in_progress', 'In progress'
    COMPLETED = 'completed', 'Completed'
    DELAYED = 'delayed', 'Delayed'
    ON_HOLD = 'on_hold', 'On hold'


class ProjectProgressPeriod(models.Model):
    project = models.ForeignKey(
        DevelopmentProject,
        on_delete=models.CASCADE,
        related_name='progress_periods',
    )
    period_date = models.DateField()
    planned_physical_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    actual_physical_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    planned_cumulative_spend_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cumulative_spend_usd = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['period_date']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'period_date'],
                name='projects_unique_progress_period',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.project.code} @ {self.period_date}'


class ProjectMilestone(models.Model):
    project = models.ForeignKey(
        DevelopmentProject,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    code = models.CharField(max_length=32, blank=True)
    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    milestone_type = models.CharField(
        max_length=16,
        choices=MilestoneType.choices,
        default=MilestoneType.DELIVERABLE,
    )
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    weight_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    planned_value_usd = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    actual_value_usd = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.PLANNED,
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sort_order', 'planned_date', 'id']

    def __str__(self) -> str:
        return self.title_en


class ProjectActivity(models.Model):
    project = models.ForeignKey(
        DevelopmentProject,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=64, blank=True)
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    weight_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    planned_budget_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    progress_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(
        max_length=16,
        choices=ActivityStatus.choices,
        default=ActivityStatus.NOT_STARTED,
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sort_order', 'planned_start', 'id']
        verbose_name_plural = 'project activities'

    def __str__(self) -> str:
        return self.title_en


class ProjectActivityPeriod(models.Model):
    project = models.ForeignKey(
        DevelopmentProject,
        on_delete=models.CASCADE,
        related_name='activity_periods',
    )
    activity = models.ForeignKey(
        ProjectActivity,
        on_delete=models.CASCADE,
        related_name='periods',
    )
    period_date = models.DateField()
    planned_physical_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    actual_physical_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    planned_cumulative_spend_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cumulative_spend_usd = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['period_date']
        constraints = [
            models.UniqueConstraint(
                fields=['activity', 'period_date'],
                name='projects_unique_activity_period',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.activity.title_en} @ {self.period_date}'
