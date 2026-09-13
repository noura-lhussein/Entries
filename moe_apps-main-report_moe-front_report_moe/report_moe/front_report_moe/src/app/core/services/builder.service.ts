import { Injectable, inject } from '@angular/core';
import { Observable, of, tap, map } from 'rxjs';
import { ApiService } from './api.service';
import type { EntityAttributeType } from '../../features/builder/entity-attribute-types';

interface LocationOption {
  id: number;
  name: string;
  governorate?: number;
}

export interface MainSection {
  id: number;
  name: string;
}

export interface SubMainSection {
  id: number;
  name: string;
  main_section_id: number;
  main_section?: number;
  parent?: number | null;
  parent_name?: string | null;
  is_leaf?: boolean;
  children_count?: number;
}

export interface TitleCategory {
  id: number;
  name: string;
  order: number;
}

export interface Title {
  id: number;
  name: string;
  order: number;
  supports_excel?: boolean;
  category?: number | null;
  category_name?: string | null;
}

export function sortTitlesByOrder<
  T extends { order: number; id: number; category?: number | null },
>(titles: T[]): T[] {
  return [...titles].sort(
    (a, b) =>
      (a.category ?? Number.MAX_SAFE_INTEGER) - (b.category ?? Number.MAX_SAFE_INTEGER) ||
      a.order - b.order ||
      a.id - b.id,
  );
}

export function sortTitleCategoriesByOrder<T extends { order: number; id: number }>(
  categories: T[],
): T[] {
  return [...categories].sort((a, b) => a.order - b.order || a.id - b.id);
}

export interface Attribute {
  id: number;
  title_id?: number;
  title?: number | null;
  label: string;
  type:
    | 'text'
    | 'textarea'
    | 'number'
    | 'date'
    | 'boolean'
    | 'select'
    | 'city'
    | 'district'
    | 'sub_district'
    | 'community'
    | 'image'
    | 'file'
    | EntityAttributeType;
  required: boolean;
  order: number;
  key?: string;
  group?: string;
  unit_ar?: string;
  help_ar?: string;
  readonly?: boolean;
  computed_from?: string | null;
  min_value?: number | string | null;
  max_value?: number | string | null;
  max_field?: string;
  warn_if_gt_field?: string;
  message_ar?: string;
  decimals?: number | null;
  options?: Option[];
}

/** GET /reports/form-schema/?title_id= */
export interface FormSchemaGroup {
  id: string;
  title_ar: string;
  order: number;
  collapsed_by_default?: boolean;
}

export interface FormSchemaField {
  id: number;
  key: string;
  label_ar: string;
  type: string;
  group: string;
  order: number;
  required: boolean;
  unit_ar?: string | null;
  readonly?: boolean;
  help_ar?: string | null;
  computed_from?: string | null;
  min?: number | null;
  max?: number | null;
  max_field?: string | null;
  warn_if_gt_field?: string | null;
  message_ar?: string | null;
  decimals?: number | null;
  options?: { id: number; label: string }[];
}

export interface FormSchemaPayload {
  section: {
    id: number;
    order: number;
    title_ar: string;
    subtitle_ar?: string | null;
    mode: string;
    groups: FormSchemaGroup[];
    preview_field_keys: string[];
  };
  fields: FormSchemaField[];
}

export interface EntityOption {
  id: number;
  label: string;
}

export interface Option {
  id: number;
  attribute_id: number;
  label: string;
  value: string;
}

export interface City {
  id: number;
  name: string;
}

export interface District {
  id: number;
  name: string;
  city: number;
}

export interface SubDistrictOption {
  id: number;
  name: string;
  district?: number;
}

export interface CommunityOption {
  id: number;
  name: string;
  subdistrict?: number;
}

export type AttributeType = Attribute['type'];

/** Payload for creating/updating an attribute. */
export interface AttributeInput {
  title: number;
  label: string;
  type: AttributeType;
  required: boolean;
  /** Arabic unit shown beside numeric inputs (e.g. م.و.س). */
  unit_ar?: string;
}

/** Permissions scope returned for non-admin users. */
export interface UserPermissions {
  sub_main_ids: number[];
  title_ids: number[];
}

export interface ReportAttributeValue {
  id: number;
  value: unknown;
}

export interface SubmitReportData {
  sub_main_id: number;
  attribute_values: ReportAttributeValue[];
}

export interface ReportSubmitResult {
  created?: number;
  [key: string]: unknown;
}

/** Report structure for a title (shape provided by the backend). */
export type FullStructureResponse = Record<string, unknown>;

@Injectable({ providedIn: 'root' })
export class BuilderService {
  private api = inject(ApiService);
  private uploadLimitsCache: { max_upload_bytes: number } | null = null;

  /** DRF returns a bare array when `pagination_class` is None on the viewset. */
  private unwrapAttributeList(data: Attribute[] | { results?: Attribute[] }): Attribute[] {
    if (Array.isArray(data)) return data;
    return data.results ?? [];
  }

  // Main Sections
  getMainSections(): Observable<{ results: MainSection[] }> {
    return this.api.get<{ results: MainSection[] }>('/main-sections/');
  }

  createMainSection(data: { name: string }): Observable<MainSection> {
    return this.api.post<MainSection>('/main-sections/', data);
  }

  updateMainSection(id: number, data: { name: string }): Observable<MainSection> {
    return this.api.patch<MainSection>(`/main-sections/${id}/`, data);
  }

  deleteMainSection(id: number): Observable<void> {
    return this.api.delete(`/main-sections/${id}/`);
  }

  // Sub Main Sections
  /**
   * List sub-sections. Pass a main-section id (legacy) or options.
   * ``leaves: true`` → only nodes without children (assignable / Info entry).
   */
  getSubMainSections(
    mainSectionIdOrOpts?: number | { mainSectionId?: number; leaves?: boolean },
  ): Observable<{ results: SubMainSection[] }> {
    const opts =
      typeof mainSectionIdOrOpts === 'number'
        ? { mainSectionId: mainSectionIdOrOpts }
        : (mainSectionIdOrOpts ?? {});
    const params: Record<string, string | number> = { page_size: 1000 };
    if (opts.mainSectionId) params['main_section'] = opts.mainSectionId;
    if (opts.leaves) params['leaves'] = 1;
    return this.api.get<{ results: SubMainSection[] }>('/sub-sections/', params);
  }

  createSubMainSection(data: {
    name: string;
    main_section_id: number;
    parent_id?: number | null;
  }): Observable<SubMainSection> {
    return this.api.post<SubMainSection>('/sub-sections/', {
      name: data.name,
      main_section: data.main_section_id,
      parent: data.parent_id ?? null,
    });
  }

  updateSubMainSection(
    id: number,
    data: { name: string; main_section_id?: number; parent_id?: number | null },
  ): Observable<SubMainSection> {
    const payload: { name: string; main_section?: number; parent?: number | null } = {
      name: data.name,
    };
    if (data.main_section_id) payload.main_section = data.main_section_id;
    if (data.parent_id !== undefined) payload.parent = data.parent_id;
    return this.api.patch<SubMainSection>(`/sub-sections/${id}/`, payload);
  }

  deleteSubMainSection(id: number): Observable<void> {
    return this.api.delete(`/sub-sections/${id}/`);
  }

  getSubSectionTree(mainSectionId: number): Observable<
    Array<{
      id: number;
      name: string;
      parent: number | null;
      is_leaf: boolean;
      children: unknown[];
    }>
  > {
    return this.api.get(`/sub-sections/tree/`, { main_section: mainSectionId });
  }

  getEntityOptions(
    entityType: string,
    params?: { q?: string; limit?: number },
  ): Observable<EntityOption[]> {
    return this.api.get<EntityOption[]>(`/entity-options/${entityType}/`, params);
  }

  // Title categories
  getTitleCategories(): Observable<{ results: TitleCategory[] }> {
    return this.api
      .get<{ results: TitleCategory[] }>('/title-categories/', { page_size: 1000 })
      .pipe(
        map((res) => ({
          results: sortTitleCategoriesByOrder(res.results || []),
        })),
      );
  }

  createTitleCategory(data: { name: string; order: number }): Observable<TitleCategory> {
    return this.api.post<TitleCategory>('/title-categories/', data);
  }

  updateTitleCategory(
    id: number,
    data: { name: string; order: number },
  ): Observable<TitleCategory> {
    return this.api.patch<TitleCategory>(`/title-categories/${id}/`, data);
  }

  deleteTitleCategory(id: number): Observable<void> {
    return this.api.delete(`/title-categories/${id}/`);
  }

  // Titles
  getTitles(params?: { category?: number }): Observable<{ results: Title[] }> {
    const query: Record<string, string | number> = { page_size: 1000 };
    if (params?.category != null) {
      query['category'] = params.category;
    }
    return this.api.get<{ results: Title[] }>('/titles/', query).pipe(
      map((res) => ({
        results: sortTitlesByOrder(res.results || []),
      })),
    );
  }

  getSubSectionAssignedUsers(subSectionId: number): Observable<
    Array<{
      id: number;
      full_name: string;
      username: string;
      email: string;
      is_active: boolean;
      parent_name?: string | null;
    }>
  > {
    return this.api.get(`/sub-sections/${subSectionId}/assigned-users/`);
  }

  getTitleAssignedUsers(titleId: number): Observable<
    Array<{
      id: number;
      full_name: string;
      username: string;
      email: string;
      is_active: boolean;
      parent_name?: string | null;
    }>
  > {
    return this.api.get(`/titles/${titleId}/assigned-users/`);
  }

  createTitle(data: { name: string; order: number; category?: number | null }): Observable<Title> {
    return this.api.post<Title>('/titles/', data);
  }

  updateTitle(
    id: number,
    data: { name: string; order: number; category?: number | null },
  ): Observable<Title> {
    return this.api.patch<Title>(`/titles/${id}/`, data);
  }

  deleteTitle(id: number): Observable<void> {
    return this.api.delete(`/titles/${id}/`);
  }

  // Attributes
  getAttributes(titleId: number): Observable<{ results: Attribute[] }> {
    return this.api
      .get<Attribute[] | { results: Attribute[] }>('/attributes/', { title: titleId })
      .pipe(map((raw) => ({ results: this.unwrapAttributeList(raw) })));
  }

  getFormSchema(titleId: number): Observable<FormSchemaPayload> {
    return this.api.get<FormSchemaPayload>('/reports/form-schema/', { title_id: titleId });
  }

  /** All attributes the API exposes to the current user (unpaginated). */
  getAllAttributes(): Observable<{ results: Attribute[] }> {
    return this.api
      .get<Attribute[] | { results: Attribute[] }>('/attributes/')
      .pipe(map((raw) => ({ results: this.unwrapAttributeList(raw) })));
  }

  createAttribute(data: AttributeInput): Observable<Attribute> {
    return this.api.post<Attribute>('/attributes/', data);
  }

  updateAttribute(id: number, data: AttributeInput): Observable<Attribute> {
    return this.api.patch<Attribute>(`/attributes/${id}/`, data);
  }

  deleteAttribute(id: number): Observable<void> {
    return this.api.delete(`/attributes/${id}/`);
  }

  // Options
  getOptions(attributeId: number): Observable<{ results: Option[] }> {
    return this.api.get<{ results: Option[] }>('/options/', { attribute: attributeId });
  }

  createOption(data: { attribute_id: number; label: string; value?: string }): Observable<Option> {
    return this.api.post<Option>('/options/', { attribute: data.attribute_id, label: data.label });
  }

  updateOption(id: number, data: { label: string; value: string }): Observable<Option> {
    return this.api.patch<Option>(`/options/${id}/`, data);
  }

  deleteOption(id: number): Observable<void> {
    return this.api.delete(`/options/${id}/`);
  }

  // Report
  getFullStructure(titleId: number): Observable<FullStructureResponse> {
    return this.api.get<FullStructureResponse>('/reports/full-structure/', {
      title_id: titleId,
    });
  }

  submitReport(titleId: number, data: SubmitReportData): Observable<ReportSubmitResult> {
    return this.api.post<ReportSubmitResult>('/reports/submit/', {
      title_id: titleId,
      ...data,
    });
  }

  submitFullReport(data: Record<string, unknown>): Observable<ReportSubmitResult> {
    return this.api.post<ReportSubmitResult>('/reports/submit-full/', data);
  }

  getUserPermissions(): Observable<UserPermissions> {
    return this.api.get<UserPermissions>('/auth/permissions/');
  }

  // Locations (unified hierarchy — city/district attrs map to governorate/district)
  getCities(): Observable<{ results: City[] }> {
    return this.api.get<LocationOption[]>('/locations/governorates/options/').pipe(
      map((items) => ({
        results: items.map((item) => ({ id: item.id, name: item.name })),
      })),
    );
  }

  getDistricts(governorateId?: number): Observable<{ results: District[] }> {
    const params = governorateId ? { governorate: governorateId } : {};
    return this.api.get<LocationOption[]>('/locations/districts/options/', params).pipe(
      map((items) => ({
        results: items.map((item) => ({
          id: item.id,
          name: item.name,
          city: item.governorate ?? governorateId ?? 0,
        })),
      })),
    );
  }

  getSubDistricts(districtId?: number): Observable<{ results: SubDistrictOption[] }> {
    const params = districtId ? { district: districtId } : {};
    return this.api.get<LocationOption[]>('/locations/subdistricts/options/', params).pipe(
      map((items) => ({
        results: items.map((item) => ({
          id: item.id,
          name: item.name,
          district: districtId,
        })),
      })),
    );
  }

  getCommunities(subdistrictId?: number): Observable<{ results: CommunityOption[] }> {
    const params = subdistrictId ? { subdistrict: subdistrictId } : {};
    return this.api.get<LocationOption[]>('/locations/communities/options/', params).pipe(
      map((items) => ({
        results: items.map((item) => ({
          id: item.id,
          name: item.name,
          subdistrict: subdistrictId,
        })),
      })),
    );
  }

  getUploadLimits(): Observable<{ max_upload_bytes: number }> {
    if (this.uploadLimitsCache) {
      return of(this.uploadLimitsCache);
    }
    return this.api.get<{ max_upload_bytes: number }>('/uploads/limits/').pipe(
      tap((res) => {
        this.uploadLimitsCache = res;
      }),
    );
  }

  uploadFormFile(file: File, kind: 'image' | 'file'): Observable<{ url: string }> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('kind', kind);
    return this.api.postFormData<{ url: string }>('/uploads/form-file/', fd);
  }
}
