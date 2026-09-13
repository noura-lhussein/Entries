"""Project completion derived from milestone statuses."""

from __future__ import annotations

from decimal import Decimal

from .models import Milestone, Project

MILESTONE_STATUS_WEIGHT: dict[str, Decimal] = {
    Milestone.Status.DRAFT: Decimal("0"),
    Milestone.Status.ACTIVE: Decimal("50"),
    Milestone.Status.ON_HOLD: Decimal("25"),
    Milestone.Status.COMPLETED: Decimal("100"),
}


def completion_milestones(project: Project):
    """Non-deleted milestones that count toward project completion."""
    return project.milestones.filter(deleted=False).exclude(
        status=Milestone.Status.CANCELLED
    )


def calculate_project_completion(project: Project) -> Decimal:
    milestones = list(completion_milestones(project).only("status"))
    if not milestones:
        return Decimal("0")

    total = sum(
        MILESTONE_STATUS_WEIGHT.get(milestone.status, Decimal("0"))
        for milestone in milestones
    )
    return (total / len(milestones)).quantize(Decimal("0.01"))


def update_project_completion(project_id: int, *, force: bool = False) -> Decimal:
    project = Project.objects.filter(pk=project_id).first()
    if not project:
        return Decimal("0")

    # Manual override: keep the user-entered value unless a recalc is forced.
    if project.completion_is_manual and not force:
        return project.percentage_completion

    percentage = calculate_project_completion(project)
    Project.objects.filter(pk=project_id).update(
        percentage_completion=percentage)
    return percentage
