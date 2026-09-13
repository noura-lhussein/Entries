"""Institution / meta helpers for datasets and the control panel (moeds tables)."""

from __future__ import annotations

import re
from typing import Any

from django.db.models import Max

from .models import ProjectGovernorate, ProjectOrganization, ProjectStatus, Sector

SECTOR_LABELS_AR = {
    Sector.OIL_GAS: 'البترول',
    Sector.WATER: 'المياه',
    Sector.ELECTRICITY: 'الكهرباء',
    Sector.MINERAL: 'التعدين',
    Sector.MULTI: 'متعدد القطاعات',
}

PROJECT_STATUS_LABELS_AR = {
    ProjectStatus.ACTIVE: 'نشط',
    ProjectStatus.PLANNED: 'مخطط',
    ProjectStatus.COMPLETED: 'مكتمل',
    ProjectStatus.SUSPENDED: 'موقوف',
}


def build_projects_meta() -> dict[str, Any]:
    return {
        'sectors': [
            {
                'value': value,
                'label_en': label,
                'label_ar': SECTOR_LABELS_AR.get(value, label),
            }
            for value, label in Sector.choices
        ],
        'statuses': [
            {
                'value': value,
                'label_en': label,
                'label_ar': PROJECT_STATUS_LABELS_AR.get(value, label),
            }
            for value, label in ProjectStatus.choices
        ],
        'governorates': list(ProjectGovernorate.objects.all()),
        'organizations': list(ProjectOrganization.objects.select_related('governorate').all()),
    }


def _slugify_organization(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')
    return (slug or 'institution')[:64]


def _unique_organization_slug(base: str) -> str:
    slug = base
    suffix = 1
    while ProjectOrganization.objects.filter(slug=slug).exists():
        suffix += 1
        slug = f'{base}-{suffix}'[:64]
    return slug


def _next_organization_id() -> int:
    max_id = ProjectOrganization.objects.aggregate(Max('id'))['id__max']
    return (max_id or 0) + 1


def list_organizations() -> list[ProjectOrganization]:
    return list(ProjectOrganization.objects.select_related('governorate').order_by('name_en'))


def get_organization(organization_id: int) -> ProjectOrganization:
    return ProjectOrganization.objects.select_related('governorate').get(pk=organization_id)


def create_organization(data: dict[str, Any]) -> ProjectOrganization:
    name_en = data['name_en'].strip()
    slug = (data.get('slug') or '').strip()
    if not slug:
        slug = _unique_organization_slug(_slugify_organization(name_en))
    elif ProjectOrganization.objects.filter(slug__iexact=slug).exists():
        raise ValueError('An institution with this code already exists.')
    return ProjectOrganization.objects.create(
        id=_next_organization_id(),
        slug=slug,
        acronym=(data.get('acronym') or '').strip(),
        name_en=name_en,
        governorate=data.get('governorate'),
    )


def update_organization(organization: ProjectOrganization, data: dict[str, Any]) -> ProjectOrganization:
    if 'name_en' in data:
        organization.name_en = data['name_en'].strip()
    if 'acronym' in data:
        organization.acronym = (data['acronym'] or '').strip()
    if 'slug' in data:
        slug = (data['slug'] or '').strip()
        if not slug:
            slug = _unique_organization_slug(_slugify_organization(organization.name_en))
        if ProjectOrganization.objects.filter(slug__iexact=slug).exclude(pk=organization.pk).exists():
            raise ValueError('An institution with this code already exists.')
        organization.slug = slug
    if 'governorate' in data:
        organization.governorate = data['governorate']
    organization.save()
    return organization


def delete_organization(organization: ProjectOrganization) -> None:
    from datasets.models import Dataset

    project_count = organization.projects.count()
    dataset_count = Dataset.objects.filter(organization=organization).count()
    if project_count or dataset_count:
        raise ValueError('Cannot delete institution with linked projects or datasets.')
    organization.delete()
